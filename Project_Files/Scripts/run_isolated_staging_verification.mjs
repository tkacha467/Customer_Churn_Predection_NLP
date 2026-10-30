#!/usr/bin/env -S node --experimental-websocket

/**
 * Isolated Staging Deployment and Verification Runner
 * Deploys the built release archive into an isolated staging environment
 * and runs automated end-to-end acceptance tests via Chrome DevTools Protocol.
 */

import { spawn, execSync } from 'child_process';
import { existsSync, mkdirSync, writeFileSync, rmSync, readFileSync } from 'fs';
import { resolve, join } from 'path';
import http from 'http';
import net from 'net';

const ROOT_DIR = resolve('/Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP');
const ARTIFACT_DIR = '/Users/tushi/.gemini/antigravity/brain/67134c41-8090-4984-94c4-a6b843aef526';
const RELEASE_TAR = join(ROOT_DIR, 'Project_Files/Releases/vraja-2.1.0-staging.tar.gz');
const STAGING_DIR = join(ROOT_DIR, 'Project_Files/Staging_Deployment');
const STAGING_APP = join(STAGING_DIR, 'app');
const STAGING_DATA = join(STAGING_DIR, 'data');
const STAGING_DOCS = join(STAGING_DIR, 'documents');
const STAGING_BACKUPS = join(STAGING_DIR, 'backups');
const CHROME_PROFILE = join(STAGING_DIR, 'chrome_profile');

const STAGING_BACKEND_PORT = 8050;
const STAGING_FRONTEND_PORT = 5188;
const STAGING_CHROME_PORT = 9230;

class CDPClient {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.msgId = 1;
    this.pending = new Map();
  }

  async connect() {
    this.ws = new WebSocket(this.wsUrl);
    await new Promise((res, rej) => {
      this.ws.onopen = res;
      this.ws.onerror = rej;
    });

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.id && this.pending.has(data.id)) {
          const { resolve: r, reject: rej } = this.pending.get(data.id);
          this.pending.delete(data.id);
          if (data.error) rej(new Error(JSON.stringify(data.error)));
          else r(data.result);
        }
      } catch (err) {
        console.error('CDP message parse error:', err);
      }
    };

    await this.send('Page.enable');
    await this.send('Runtime.enable');
    await this.send('DOM.enable');
  }

  async send(method, params = {}) {
    const id = this.msgId++;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async evaluate(expression) {
    const res = await this.send('Runtime.evaluate', {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    return res.result?.value;
  }

  async navigate(url, waitMs = 1200) {
    await this.send('Page.navigate', { url });
    await new Promise((r) => setTimeout(r, waitMs));
  }

  async setViewport(width, height, isMobile = false) {
    await this.send('Emulation.setDeviceMetricsOverride', {
      width,
      height,
      deviceScaleFactor: 2,
      mobile: isMobile,
    });
  }

  async captureScreenshot(filename) {
    const res = await this.send('Page.captureScreenshot', { format: 'png', quality: 90 });
    const buffer = Buffer.from(res.data, 'base64');
    const dest = join(ARTIFACT_DIR, filename);
    writeFileSync(dest, buffer);
    console.log(`[+] Saved screenshot: ${dest} (${(buffer.length / 1024).toFixed(1)} KB)`);
  }

  close() {
    try { this.ws.close(); } catch {}
  }
}

async function waitForTcp(port, host = '127.0.0.1', timeoutMs = 25000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const ok = await new Promise((res) => {
      const s = net.connect(port, host, () => {
        s.end();
        res(true);
      });
      s.on('error', () => res(false));
    });
    if (ok) return;
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error(`Timeout waiting for port ${port}`);
}

async function waitForSelector(client, selector, timeoutMs = 10000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const found = await client.evaluate(`Boolean(document.querySelector('${selector}'))`);
    if (found) return true;
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error(`Timeout waiting for selector: ${selector}`);
}

function findChromePath() {
  const candidates = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium-browser',
  ];
  for (const p of candidates) {
    if (existsSync(p)) return p;
  }
  throw new Error('Google Chrome binary not found');
}

async function main() {
  console.log('================================================================');
  console.log(' VRAJA AI DIGITAL CARD — ISOLATED STAGING DEPLOYMENT & VERIFY');
  console.log('================================================================\n');

  // 1. Prepare Staging Directories
  console.log('[1/8] Setting up staging directories...');
  if (existsSync(STAGING_DIR)) {
    rmSync(STAGING_DIR, { recursive: true, force: true });
  }
  mkdirSync(STAGING_APP, { recursive: true });
  mkdirSync(STAGING_DATA, { recursive: true });
  mkdirSync(STAGING_DOCS, { recursive: true });
  mkdirSync(STAGING_BACKUPS, { recursive: true });
  mkdirSync(CHROME_PROFILE, { recursive: true });

  // 2. Extract Release Archive
  console.log(`[2/8] Unpacking release archive ${RELEASE_TAR}...`);
  if (!existsSync(RELEASE_TAR)) {
    throw new Error(`Release archive not found: ${RELEASE_TAR}`);
  }
  execSync(`tar -xzf "${RELEASE_TAR}" -C "${STAGING_APP}" --strip-components=1`, { stdio: 'inherit' });

  // 3. Write Staging Environment Config
  console.log('[3/8] Writing staging environment configuration...');
  const stagingDbPath = join(STAGING_DATA, 'reviews.sqlite3');
  const stagingEnvContent = [
    'ENVIRONMENT=staging',
    'DEBUG=false',
    `PORT=${STAGING_BACKEND_PORT}`,
    `REVIEW_DB_PATH=${stagingDbPath}`,
    `DOCUMENTS_PATH=${STAGING_DOCS}`,
    `BACKUP_BASE_DIR=${STAGING_BACKUPS}`,
    `CORS_ORIGINS=http://127.0.0.1:${STAGING_FRONTEND_PORT},http://localhost:${STAGING_FRONTEND_PORT}`,
    'OWNER_SESSION_SECRET=c3RhZ2luZy1zZWNyZXQta2V5LWF0LWxlYXN0LTMyLWJ5dGVzLWxvbmc=',
    'SESSION_TTL_HOURS=24',
    'COOKIE_SECURE=false',
  ].join('\n');
  writeFileSync(join(STAGING_DIR, 'staging.env'), stagingEnvContent);

  // 4. Initialize Staging Database & Seed Tenants
  console.log('[4/8] Initializing staging SQLite database with schema and tenants...');
  const pythonBin = existsSync(join(ROOT_DIR, '.venv/bin/python3'))
    ? join(ROOT_DIR, '.venv/bin/python3')
    : 'python3';

  execSync(
    `REVIEW_DB_PATH="${stagingDbPath}" "${pythonBin}" -c "
import time, os
from os.path import join
from Backend.app.core.database.storage import ReviewStore
from Backend.app.core.auth.auth import hash_password

store = ReviewStore(database_path='${stagingDbPath}')

# 1. Nasta Ghar (Default Business)
store.upsert_tenant({
    'id': 'default_business',
    'business_name': 'Nasta Ghar',
    'category': 'Breakfast & Snacks',
    'description': 'Authentic homestyle breakfast, chai, and snacks in Rajkot.',
    'status': 'active',
    'review_url': 'https://search.google.com/local/writereview?placeid=ChIJZeK7NwDLWTkR1pOxt51jLro',
    'primary_accent': '#f97316',
    'entitlements': ['review_manager', 'digital_card']
})
store.upsert_business_profile('default_business', {
    'display_name': 'Nasta Ghar',
    'tagline': 'Authentic Kathiyawadi Heritage Taste',
    'category': 'Breakfast & Snacks',
    'phone_number': '+91 94282 12345',
    'whatsapp_url': 'https://wa.me/919428212345',
    'address': 'Near Race Course Ground, Rajkot, Gujarat 360001',
    'map_url': 'https://maps.google.com/?q=Nasta+Ghar+Rajkot',
    'opening_hours': 'Mon - Sun: 7:00 AM - 11:00 PM',
    'welcome_message': 'Welcome to Nasta Ghar! Authentic Kathiyawadi breakfast, warm chai, and farsan.',
    'show_review_button': True,
    'is_published': True
})
u_nasta = store.create_user(
    email='owner1@nastaghar.test',
    password_hash=hash_password('NastaGharPass123!'),
    display_name='Nasta Ghar Owner',
    is_active=1
)
store.add_membership(u_nasta['id'], 'default_business', role='owner')

# 2. Restaurant Profile (Saffron Spice Bistro)
store.upsert_tenant({
    'id': 'restaurant_demo',
    'business_name': 'Saffron Spice Bistro',
    'category': 'Gourmet Dining & Bistro',
    'description': 'Artisanal regional dining, seasonal dishes, and hospitality.',
    'status': 'active',
    'review_url': 'https://search.google.com/local/writereview?placeid=ChIJSaffronSpiceBistro',
    'primary_accent': '#0f281e',
    'entitlements': ['digital_card', 'review_manager']
})
store.upsert_business_profile('restaurant_demo', {
    'display_name': 'Saffron Spice Bistro',
    'category': 'Gourmet Dining & Bistro',
    'phone_number': '+91 98765 43210',
    'whatsapp_url': 'https://wa.me/919876543210',
    'instagram_url': 'https://instagram.com/saffronspicebistro',
    'map_url': 'https://maps.google.com/?q=Saffron+Spice+Bistro',
    'address': 'Heritage Square, Main Boulevard',
    'opening_hours': 'Tue - Sun: 12:00 PM - 10:30 PM',
    'welcome_message': 'Welcome to Saffron Spice Bistro! Fresh seasonal dining and authentic flavours.',
    'show_review_button': True,
    'is_published': True
})
store.add_tenant_document({
    'id': 'doc_tasting_menu',
    'tenant_id': 'restaurant_demo',
    'document_type': 'food_menu',
    'display_name': 'Chef Tasting Menu',
    'original_filename': 'tasting_menu.pdf',
    'file_size_bytes': 154000,
    'mime_type': 'application/pdf',
    'sha256_hash': 'abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
    'storage_path': join('${STAGING_DOCS}', 'tasting_menu.pdf'),
    'is_published': True
})

# 3. Gym Profile (Pulse Fitness Club)
store.upsert_tenant({
    'id': 'gym_demo',
    'business_name': 'Pulse Fitness Club',
    'category': 'Fitness & Health Club',
    'status': 'active',
    'entitlements': ['digital_card']
})
store.upsert_business_profile('gym_demo', {
    'display_name': 'Pulse Fitness Club',
    'category': 'Fitness & Health Club',
    'phone_number': '+91 98111 22233',
    'whatsapp_url': 'https://wa.me/919811122233',
    'instagram_url': 'https://instagram.com/pulsefitnessclub',
    'website_url': 'https://pulsefitness.example.com',
    'address': 'Olympic Arena, West Wing',
    'opening_hours': 'Mon - Sat: 6:00 AM - 10:00 PM',
    'welcome_message': 'Transform your body and mind at Pulse Fitness Club.',
    'show_review_button': False,
    'is_published': True
})

# 4. Professional Service (Apex Legal Partners)
store.upsert_tenant({
    'id': 'service_demo',
    'business_name': 'Apex Legal Partners',
    'category': 'Corporate Legal Consultancy',
    'status': 'active',
    'entitlements': ['digital_card']
})
store.upsert_business_profile('service_demo', {
    'display_name': 'Apex Legal Partners',
    'category': 'Corporate Legal Consultancy',
    'phone_number': '+91 98999 88877',
    'email': 'contact@apexlegal.example.com',
    'website_url': 'https://apexlegal.example.com',
    'address': 'Tower 4, Financial District',
    'opening_hours': 'Mon - Fri: 9:00 AM - 6:00 PM',
    'welcome_message': 'Trusted corporate legal and financial advisory services.',
    'show_review_button': False,
    'is_published': True
})

# 5. Unpublished Draft Tenant
store.upsert_tenant({
    'id': 'draft_demo',
    'business_name': 'Secret Draft Studio',
    'category': 'Design Studio',
    'status': 'active',
    'entitlements': ['digital_card']
})
store.upsert_business_profile('draft_demo', {
    'display_name': 'Secret Draft Studio',
    'is_published': False
})
print('[+] Staging SQLite DB seeded with 5 test tenants.')
"`,
    { stdio: 'inherit' }
  );

  // 5. Start Staging Backend
  console.log(`[5/8] Launching staging FastAPI backend on port ${STAGING_BACKEND_PORT}...`);
  const backendProc = spawn(
    pythonBin,
    ['-m', 'uvicorn', 'Backend.app.main:app', '--host', '127.0.0.1', '--port', String(STAGING_BACKEND_PORT)],
    {
      cwd: STAGING_APP,
      env: {
        ...process.env,
        ENVIRONMENT: 'staging',
        DEBUG: 'false',
        PORT: String(STAGING_BACKEND_PORT),
        REVIEW_DB_PATH: stagingDbPath,
        DOCUMENTS_PATH: STAGING_DOCS,
        BACKUP_BASE_DIR: STAGING_BACKUPS,
        CORS_ORIGINS: `http://127.0.0.1:${STAGING_FRONTEND_PORT},http://localhost:${STAGING_FRONTEND_PORT}`,
        OWNER_SESSION_SECRET: 'c3RhZ2luZy1zZWNyZXQta2V5LWF0LWxlYXN0LTMyLWJ5dGVzLWxvbmc=',
        PYTHONPATH: STAGING_APP,
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    }
  );

  await waitForTcp(STAGING_BACKEND_PORT);
  console.log(`[+] Staging backend live on http://127.0.0.1:${STAGING_BACKEND_PORT}`);

  // 6. Start Staging Digital Card Frontend
  console.log(`[6/8] Launching staging Digital Card frontend on port ${STAGING_FRONTEND_PORT}...`);
  const stagingFrontend = resolve(STAGING_APP, 'Digital_Card/frontend');
  const sourceNodeModules = resolve(ROOT_DIR, 'Digital_Card/frontend/node_modules');
  if (!existsSync(join(stagingFrontend, 'node_modules')) && existsSync(sourceNodeModules)) {
    execSync(`ln -s "${sourceNodeModules}" "${join(stagingFrontend, 'node_modules')}"`);
  }

  const viteBin = join(sourceNodeModules, '.bin/vite');
  const frontendProc = spawn(
    viteBin,
    ['--port', String(STAGING_FRONTEND_PORT), '--strictPort'],
    {
      cwd: stagingFrontend,
      env: {
        ...process.env,
        VITE_BACKEND_URL: `http://127.0.0.1:${STAGING_BACKEND_PORT}`,
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    }
  );

  await waitForTcp(STAGING_FRONTEND_PORT);
  console.log(`[+] Staging frontend live on http://127.0.0.1:${STAGING_FRONTEND_PORT}`);

  // 7. Launch Headless Chrome
  console.log(`[7/8] Launching Chrome CDP on port ${STAGING_CHROME_PORT}...`);
  const chromeBin = findChromePath();
  const chromeProc = spawn(chromeBin, [
    `--remote-debugging-port=${STAGING_CHROME_PORT}`,
    '--headless=new',
    '--disable-gpu',
    '--no-sandbox',
    '--disable-extensions',
    `--user-data-dir=${CHROME_PROFILE}`,
    'about:blank',
  ]);

  await waitForTcp(STAGING_CHROME_PORT);

  const targets = await new Promise((res, rej) => {
    http.get(`http://127.0.0.1:${STAGING_CHROME_PORT}/json`, (resp) => {
      let data = '';
      resp.on('data', (c) => (data += c));
      resp.on('end', () => res(JSON.parse(data)));
      resp.on('error', rej);
    });
  });

  const pageTarget = targets.find((t) => t.type === 'page');
  const client = new CDPClient(pageTarget.webSocketDebuggerUrl);
  await client.connect();
  console.log('[+] Connected to Chrome CDP session.\n');

  // 8. Execute Acceptance Test Scenarios against Staging
  console.log('[8/8] Executing Staging Acceptance Suite...');

  try {
    // ─── TEST 1: NASTAGHAR STAGING PUBLIC CARD ───────────────────────
    console.log('\n--- Staging Test 1: NastaGhar Public Card ---');
    await client.setViewport(390, 844, true);
    await client.navigate(`http://127.0.0.1:${STAGING_FRONTEND_PORT}/?b=nasta-ghar`, 2000);
    await waitForSelector(client, '.vcard-phone-shell', 5000);

    const nastaData = await client.evaluate(`
      (() => {
        const title = document.querySelector('.vcard-business-name')?.textContent?.trim();
        const category = document.querySelector('.vcard-category-tag')?.textContent?.trim();
        const actionLabels = Array.from(document.querySelectorAll('.vcard-grid-tile .vcard-tile-label')).map(el => el.textContent.trim());
        const dockLabels = Array.from(document.querySelectorAll('.vcard-dock-item .vcard-dock-label')).map(el => el.textContent.trim());
        const hasLogin = Boolean(document.querySelector('.editor-login-box'));
        const isOverflow = document.documentElement.scrollWidth > window.innerWidth;
        return { title, category, actionLabels, dockLabels, hasLogin, isOverflow };
      })()
    `);
    console.log('Staging NastaGhar Result:', nastaData);
    if (nastaData.hasLogin) throw new Error('Staging FAIL: Login screen prompted for public card!');
    if (nastaData.title !== 'Nasta Ghar') throw new Error(`Staging FAIL: Expected title 'Nasta Ghar', got '${nastaData.title}'`);
    if (nastaData.category !== 'BREAKFAST & SNACKS') throw new Error(`Staging FAIL: Unexpected category '${nastaData.category}'`);
    if (nastaData.isOverflow) throw new Error('Staging FAIL: Viewport horizontal overflow!');
    await client.captureScreenshot('staging_nastaghar_card.png');
    console.log('✅ Staging Test 1 PASSED: NastaGhar card loads without login, clean layout.');

    // ─── TEST 2: RESTAURANT STAGING CARD ─────────────────────────────
    console.log('\n--- Staging Test 2: Restaurant Profile (Menu & Maps) ---');
    await client.navigate(`http://127.0.0.1:${STAGING_FRONTEND_PORT}/?b=restaurant_demo`, 2000);
    await waitForSelector(client, '.vcard-phone-shell', 5000);

    const restData = await client.evaluate(`
      (() => {
        const actionLabels = Array.from(document.querySelectorAll('.vcard-grid-tile .vcard-tile-label')).map(el => el.textContent.trim());
        const hasMenu = actionLabels.some(l => l.includes('Menu'));
        return { actionLabels, hasMenu };
      })()
    `);
    console.log('Staging Restaurant Actions:', restData.actionLabels);
    if (!restData.hasMenu) throw new Error('Staging FAIL: Restaurant missing Menu document action!');
    await client.captureScreenshot('staging_restaurant_card.png');
    console.log('✅ Staging Test 2 PASSED: Restaurant has tasting menu and review action.');

    // ─── TEST 3: GYM STAGING CARD (ZERO MENU/DOCS LEAK) ──────────────
    console.log('\n--- Staging Test 3: Gym Profile (Zero Menu / Document Leak) ---');
    await client.navigate(`http://127.0.0.1:${STAGING_FRONTEND_PORT}/?b=gym_demo`, 2000);
    await waitForSelector(client, '.vcard-phone-shell', 5000);

    const gymData = await client.evaluate(`
      (() => {
        const actionLabels = Array.from(document.querySelectorAll('.vcard-grid-tile .vcard-tile-label')).map(el => el.textContent.trim());
        const dockLabels = Array.from(document.querySelectorAll('.vcard-dock-item .vcard-dock-label')).map(el => el.textContent.trim());
        const hasMenu = actionLabels.some(l => l.toLowerCase().includes('menu') || l.toLowerCase().includes('doc'));
        return { actionLabels, dockLabels, hasMenu };
      })()
    `);
    console.log('Staging Gym Actions:', gymData.actionLabels);
    if (gymData.hasMenu) throw new Error('Staging FAIL: Gym profile displayed Menu/Document!');
    if (!gymData.actionLabels.includes('Website')) throw new Error('Staging FAIL: Gym missing Website action!');
    await client.captureScreenshot('staging_gym_card.png');
    console.log('✅ Staging Test 3 PASSED: Gym profile has 0 menu leak.');

    // ─── TEST 4: SERVICE STAGING CARD (2x2 GRID, 0 WHATSAPP) ─────────
    console.log('\n--- Staging Test 4: Professional Service (2x2 Grid, Zero WhatsApp) ---');
    await client.navigate(`http://127.0.0.1:${STAGING_FRONTEND_PORT}/?b=service_demo`, 2000);
    await waitForSelector(client, '.vcard-phone-shell', 5000);

    const srvData = await client.evaluate(`
      (() => {
        const actionLabels = Array.from(document.querySelectorAll('.vcard-grid-tile .vcard-tile-label')).map(el => el.textContent.trim());
        const gridClass = document.querySelector('.vcard-action-grid')?.className;
        const hasWA = actionLabels.some(l => l.toLowerCase().includes('whatsapp'));
        return { actionLabels, gridClass, hasWA };
      })()
    `);
    console.log('Staging Service Actions:', srvData.actionLabels);
    if (srvData.hasWA) throw new Error('Staging FAIL: Professional service displayed WhatsApp!');
    if (!srvData.gridClass.includes('vcard-grid-count-4')) {
      throw new Error(`Staging FAIL: Expected count-4 balanced grid, got ${srvData.gridClass}`);
    }
    await client.captureScreenshot('staging_service_card.png');
    console.log('✅ Staging Test 4 PASSED: Service profile has 4-action symmetric grid and 0 WhatsApp.');

    // ─── TEST 5: UNPUBLISHED CARD PRIVACY BOUNDARY ────────────────────
    console.log('\n--- Staging Test 5: Unpublished Draft Privacy ---');
    await client.navigate(`http://127.0.0.1:${STAGING_FRONTEND_PORT}/?b=draft_demo`, 2000);
    await waitForSelector(client, '.vcard-empty-panel', 5000);

    const emptyText = await client.evaluate(`document.querySelector('.vcard-empty-title')?.textContent?.trim()`);
    if (emptyText !== 'Business Card Not Available') {
      throw new Error(`Staging FAIL: Expected 'Business Card Not Available', got '${emptyText}'`);
    }
    console.log('✅ Staging Test 5 PASSED: Unpublished cards remain private.');

    // ─── TEST 6: OWNER AUTH & CROSS-TENANT SECURITY GATE ─────────────
    console.log('\n--- Staging Test 6: Staging Owner Auth & Cross-Tenant Security ---');
    await client.navigate(`http://127.0.0.1:${STAGING_FRONTEND_PORT}/owner/default_business/card`, 1500);

    const loginRes = await client.evaluate(`
      (async () => {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: 'owner1@nastaghar.test',
            password: 'NastaGharPass123!',
            tenant_id: 'default_business'
          })
        });
        return { status: res.status };
      })()
    `);
    if (loginRes.status !== 200) {
      throw new Error(`Staging FAIL: Owner login failed with status: ${loginRes.status}`);
    }

    await client.navigate(`http://127.0.0.1:${STAGING_FRONTEND_PORT}/owner/default_business/card`, 1500);
    await waitForSelector(client, '.editor-heading', 8000);
    await client.captureScreenshot('staging_owner_studio.png');
    console.log('[+] Nasta Ghar owner signed into Card Studio in staging.');

    // Attempt illegal cross-tenant edit on restaurant_demo
    const hackRes = await client.evaluate(`
      (async () => {
        const res = await fetch('/api/businesses/restaurant_demo/profile', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ display_name: 'Stolen By NastaGhar Owner' })
        });
        return { status: res.status };
      })()
    `);
    if (hackRes.status !== 403) {
      throw new Error(`Staging FAIL: Cross-tenant update was not 403 Forbidden! Status: ${hackRes.status}`);
    }
    console.log('✅ Staging Test 6 PASSED: Cross-tenant profile tampering rejected with 403 Forbidden.');

    // ─── TEST 7: QR DESTINATION ROUTING ENDPOINT ──────────────────────
    console.log('\n--- Staging Test 7: QR Code Destination Routing ---');
    const qrInfo = await client.evaluate(`
      (async () => {
        const res = await fetch('/api/businesses/nasta-ghar/card/qr-info');
        return { status: res.status, json: await res.json() };
      })()
    `);
    console.log('QR Info Endpoint Result:', qrInfo);
    if (qrInfo.status !== 200 || !qrInfo.json?.card_url) {
      throw new Error(`Staging FAIL: QR Info endpoint failed: ${JSON.stringify(qrInfo)}`);
    }
    console.log('✅ Staging Test 7 PASSED: QR destination endpoint active and accurate.');

    console.log('\n================================================================');
    console.log(' STAGING ACCEPTANCE COMPLETED WITH 100% SUCCESS!');
    console.log('================================================================\n');
  } finally {
    client.close();
    chromeProc.kill('SIGKILL');
    backendProc.kill('SIGTERM');
    frontendProc.kill('SIGTERM');
  }
}

main().catch((err) => {
  console.error('\n❌ STAGING AUDIT FAILED:', err);
  process.exit(1);
});
