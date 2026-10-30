#!/usr/bin/env -S node --experimental-websocket

/**
 * End-to-End Acceptance Test for VRAJA AI Digital Card
 * Dynamic Optional Actions, Multi-Tenant Data Isolation, and Security Boundaries
 */

import { spawn, execSync } from 'child_process';
import { existsSync, mkdirSync, writeFileSync, rmSync } from 'fs';
import { resolve, join } from 'path';
import http from 'http';
import net from 'net';
import os from 'os';

const ROOT_DIR = resolve('/Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP');
const ARTIFACT_DIR = '/Users/tushi/.gemini/antigravity/brain/67134c41-8090-4984-94c4-a6b843aef526';
const BACKEND_PORT = 8196;
const FRONTEND_PORT = 5186;
const CHROME_PORT = 9226;

const AUDIT_DIR = join(os.tmpdir(), `vraja_acceptance_${Date.now()}`);
const AUDIT_DB = join(AUDIT_DIR, 'test_review.sqlite3');
const AUDIT_DOCS = join(AUDIT_DIR, 'documents');
const USER_DATA_DIR = join(AUDIT_DIR, 'chrome_profile');

const SAMPLE_PDF_BASE64 =
  'JVBERi0xLjQKJeLjz9MKMSAwIG9iajw8L1R5cGUvQ2F0YWxvZy9QYWdlcyAyIDAgUj4+ZW5kb2Jq' +
  'CjIgMCBvYmo8PC9UeXBlL1BhZ2VzL0tpZHNbMyAwIFJdL0NvdW50IDE+PmVuZG9iagozIDAgb2Jq' +
  'PDwvVHlwZS9QYWdlL1BhcmVudCAyIDAgUi9NZWRpYUJveFswIDAgMzAwIDMwMF0vQ29udGVudHMg' +
  'NCAwIFI+PmVuZG9iago0IDAgb2JqPDwvTGVuZ3RoIDQ0Pj5zdHJlYW0KQVQgL0YxIDEyIFRmIDUw' +
  'IDIwMCBUZCAoU2FmZnJvbiBCaXN0cm8gTWVudSkgVGoKRVQgZW5kc3RyZWFtCmVuZG9iagp4cmVm' +
  'CjAgNQowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMDkgMDAwMDAgbiAKMDAwMDAwMDA1NiAw' +
  'MDAwMCBuIAowMDAwMDAwMTExIDAwMDAwIG4gCjAwMDAwMDAyMDQgMDAwMDAgbiAKdHJhaWxlcjw8' +
  'L1NpemUgNT4+CnN0YXJ0eHJlZgoyOTgKJSVFT0Y=';

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
  console.log(' VRAJA AI DIGITAL CARD — DYNAMIC UI & DATA ISOLATION AUDIT');
  console.log('================================================================\n');

  mkdirSync(AUDIT_DIR, { recursive: true });
  mkdirSync(AUDIT_DOCS, { recursive: true });
  mkdirSync(USER_DATA_DIR, { recursive: true });

  const pythonBin = existsSync(join(ROOT_DIR, '.venv/bin/python3'))
    ? join(ROOT_DIR, '.venv/bin/python3')
    : 'python3';

  // 1. Initialize isolated database and seed the 3 tenant profiles + draft tenant
  console.log('[*] Seeding 3 visibly different tenant profiles into isolated SQLite DB...');
  execSync(
    `REVIEW_DB_PATH="${AUDIT_DB}" "${pythonBin}" -c "
import time, json, os
from os.path import join
from Backend.app.core.database.storage import ReviewStore
from Backend.app.core.auth.auth import hash_password

store = ReviewStore(database_path='${AUDIT_DB}')

# 1. Restaurant Profile
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
u_rest = store.create_user(
    email='owner@saffronspice.test',
    password_hash=hash_password('SaffronOwner2026!'),
    display_name='Saffron Managing Chef',
    is_active=1
)
store.add_membership(u_rest['id'], 'restaurant_demo', role='owner')

# Add Menu Document for Restaurant
store.add_tenant_document({
    'id': 'doc_rest_menu_1',
    'tenant_id': 'restaurant_demo',
    'document_type': 'food_menu',
    'display_name': 'Tasting Menu',
    'original_filename': 'saffron_tasting_menu.pdf',
    'file_size_bytes': 145020,
    'mime_type': 'application/pdf',
    'sha256_hash': 'abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
    'storage_path': join('${AUDIT_DOCS}', 'saffron_tasting_menu.pdf'),
    'is_published': True
})

# 2. Gym Profile
store.upsert_tenant({
    'id': 'gym_demo',
    'business_name': 'Pulse Fitness Club',
    'category': 'Fitness & Health Club',
    'description': 'Elite strength conditioning and personal training.',
    'status': 'active',
    'primary_accent': '#1e3a8a',
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
    'welcome_message': 'Transform your body and mind at Pulse Fitness Club. Modern equipment and personal training.',
    'show_review_button': False,
    'is_published': True
})
u_gym = store.create_user(
    email='owner@pulsefitness.test',
    password_hash=hash_password('PulseOwner2026!'),
    display_name='Pulse Head Trainer',
    is_active=1
)
store.add_membership(u_gym['id'], 'gym_demo', role='owner')

# 3. Professional Service Profile
store.upsert_tenant({
    'id': 'service_demo',
    'business_name': 'Apex Legal Partners',
    'category': 'Corporate Legal Consultancy',
    'description': 'Corporate mergers, IP protection, and contract dispute advisory.',
    'status': 'active',
    'primary_accent': '#0f172a',
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
    'welcome_message': 'Trusted corporate legal and financial advisory services for growing enterprises.',
    'show_review_button': False,
    'is_published': True
})
u_srv = store.create_user(
    email='owner@apexlegal.test',
    password_hash=hash_password('ApexOwner2026!'),
    display_name='Apex Senior Partner',
    is_active=1
)
store.add_membership(u_srv['id'], 'service_demo', role='owner')

# 4. Unpublished Draft Tenant
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
print('[+] Successfully seeded all 4 tenants.')
"`,
    { stdio: 'inherit' }
  );

  // 2. Start Backend
  console.log(`[*] Starting isolated FastAPI backend on port ${BACKEND_PORT}...`);
  const backendProc = spawn(
    pythonBin,
    ['-m', 'uvicorn', 'Backend.app.main:app', '--host', '127.0.0.1', '--port', String(BACKEND_PORT)],
    {
      cwd: ROOT_DIR,
      env: {
        ...process.env,
        REVIEW_DB_PATH: AUDIT_DB,
        DOCUMENTS_PATH: AUDIT_DOCS,
        PORT: String(BACKEND_PORT),
        ENVIRONMENT: 'test',
        PYTHONPATH: ROOT_DIR,
        CORS_ORIGINS: `http://127.0.0.1:${FRONTEND_PORT},http://localhost:${FRONTEND_PORT}`,
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    }
  );

  await waitForTcp(BACKEND_PORT);
  console.log(`[+] Backend online on http://127.0.0.1:${BACKEND_PORT}`);

  // 3. Start Frontend
  console.log(`[*] Starting Digital Card Vite frontend on port ${FRONTEND_PORT}...`);
  const frontendProc = spawn(
    'npx',
    ['vite', '--port', String(FRONTEND_PORT), '--strictPort'],
    {
      cwd: resolve(ROOT_DIR, 'Digital_Card/frontend'),
      env: {
        ...process.env,
        VITE_BACKEND_URL: `http://127.0.0.1:${BACKEND_PORT}`,
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    }
  );

  await waitForTcp(FRONTEND_PORT);
  console.log(`[+] Frontend online on http://127.0.0.1:${FRONTEND_PORT}`);

  // 4. Start Chrome in Headless CDP mode
  const chromeBin = findChromePath();
  console.log(`[*] Launching Headless Chrome (${chromeBin}) on port ${CHROME_PORT}...`);
  const chromeProc = spawn(chromeBin, [
    `--remote-debugging-port=${CHROME_PORT}`,
    '--headless=new',
    '--disable-gpu',
    '--no-sandbox',
    '--disable-extensions',
    `--user-data-dir=${USER_DATA_DIR}`,
    'about:blank',
  ]);

  await waitForTcp(CHROME_PORT);

  // Query CDP Target
  const targets = await new Promise((res, rej) => {
    http.get(`http://127.0.0.1:${CHROME_PORT}/json`, (resp) => {
      let data = '';
      resp.on('data', (c) => (data += c));
      resp.on('end', () => res(JSON.parse(data)));
      resp.on('error', rej);
    });
  });

  const pageTarget = targets.find((t) => t.type === 'page');
  const client = new CDPClient(pageTarget.webSocketDebuggerUrl);
  await client.connect();
  console.log('[+] Connected to Chrome DevTools Protocol session.');

  try {
    // ─────────────────────────────────────────────────────────────────
    // VERIFICATION 1: RESTAURANT PROFILE (Saffron Spice Bistro)
    // ─────────────────────────────────────────────────────────────────
    console.log('\n================================================================');
    console.log(' TEST CASE 1: RESTAURANT PROFILE (Saffron Spice Bistro)');
    console.log('================================================================');
    await client.setViewport(390, 844, true); // iPhone 14
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/?b=restaurant_demo`, 2000);
    await waitForSelector(client, '.vcard-phone-shell', 5000);

    const restData = await client.evaluate(`
      (() => {
        const title = document.querySelector('.vcard-business-name')?.textContent?.trim();
        const category = document.querySelector('.vcard-category-tag')?.textContent?.trim();
        const hours = document.querySelector('.vcard-hours-text')?.textContent?.trim();
        const actionLabels = Array.from(document.querySelectorAll('.vcard-grid-tile .vcard-tile-label')).map(el => el.textContent.trim());
        const dockLabels = Array.from(document.querySelectorAll('.vcard-dock-item .vcard-dock-label')).map(el => el.textContent.trim());
        const hasLogin = Boolean(document.querySelector('.editor-login-box') || document.querySelector('input[type="password"]'));
        const menuLink = document.querySelector('.vcard-grid-tile[aria-label*="Menu"]')?.textContent?.trim();
        return { title, category, hours, actionLabels, dockLabels, hasLogin, menuLink };
      })()
    `);

    console.log('Rendered Restaurant Profile:', JSON.stringify(restData, null, 2));

    if (restData.hasLogin) throw new Error('FAIL: Public visitor was shown a login screen!');
    if (restData.title !== 'Saffron Spice Bistro') throw new Error(`FAIL: Expected title 'Saffron Spice Bistro', got '${restData.title}'`);
    if (restData.category !== 'GOURMET DINING & BISTRO') throw new Error(`FAIL: Unexpected category '${restData.category}'`);
    if (!restData.actionLabels.includes('Save Contact')) throw new Error('FAIL: Missing Save Contact action');
    if (!restData.actionLabels.includes('Call')) throw new Error('FAIL: Missing Call action');
    if (!restData.actionLabels.includes('WhatsApp')) throw new Error('FAIL: Missing WhatsApp action');
    if (!restData.actionLabels.includes('Instagram')) throw new Error('FAIL: Missing Instagram action');
    if (!restData.actionLabels.includes('Review Us')) throw new Error('FAIL: Missing Review Us action');
    if (!restData.actionLabels.some(l => l.includes('Menu') || l.includes('Tasting Menu'))) throw new Error('FAIL: Missing Menu PDF action');
    if (!restData.actionLabels.includes('Google Maps')) throw new Error('FAIL: Missing Google Maps action');

    // Confirm absent actions are strictly not rendered
    if (restData.actionLabels.includes('Email')) throw new Error('FAIL: Email action rendered when not configured!');
    if (restData.actionLabels.includes('Website')) throw new Error('FAIL: Website action rendered when not configured!');
    if (restData.actionLabels.includes('Facebook')) throw new Error('FAIL: Facebook action rendered when not configured!');

    // Dock verification
    if (restData.dockLabels.length !== 2 || !restData.dockLabels.includes('Call') || !restData.dockLabels.includes('WhatsApp')) {
      throw new Error(`FAIL: Restaurant dock must contain ONLY Call and WhatsApp, got: ${restData.dockLabels}`);
    }

    await client.captureScreenshot('restaurant_public_card.png');
    console.log('✅ TEST CASE 1 PASSED: Restaurant displays all and only configured actions.');

    // ─────────────────────────────────────────────────────────────────
    // VERIFICATION 2: GYM PROFILE (Pulse Fitness Club)
    // ─────────────────────────────────────────────────────────────────
    console.log('\n================================================================');
    console.log(' TEST CASE 2: GYM PROFILE (Pulse Fitness Club)');
    console.log('================================================================');
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/?b=gym_demo`, 2000);
    await waitForSelector(client, '.vcard-phone-shell', 5000);

    const gymData = await client.evaluate(`
      (() => {
        const title = document.querySelector('.vcard-business-name')?.textContent?.trim();
        const category = document.querySelector('.vcard-category-tag')?.textContent?.trim();
        const actionLabels = Array.from(document.querySelectorAll('.vcard-grid-tile .vcard-tile-label')).map(el => el.textContent.trim());
        const dockLabels = Array.from(document.querySelectorAll('.vcard-dock-item .vcard-dock-label')).map(el => el.textContent.trim());
        const hasLogin = Boolean(document.querySelector('.editor-login-box'));
        const hasMenu = Boolean(document.querySelector('.vcard-grid-tile[aria-label*="menu" i]') || document.querySelector('.vcard-grid-tile[aria-label*="document" i]'));
        return { title, category, actionLabels, dockLabels, hasLogin, hasMenu };
      })()
    `);

    console.log('Rendered Gym Profile:', JSON.stringify(gymData, null, 2));

    if (gymData.hasLogin) throw new Error('FAIL: Public visitor was shown a login screen!');
    if (gymData.title !== 'Pulse Fitness Club') throw new Error(`FAIL: Expected 'Pulse Fitness Club', got '${gymData.title}'`);
    if (gymData.category !== 'FITNESS & HEALTH CLUB') throw new Error(`FAIL: Unexpected category '${gymData.category}'`);

    // Expected actions
    if (!gymData.actionLabels.includes('Save Contact')) throw new Error('FAIL: Missing Save Contact action');
    if (!gymData.actionLabels.includes('Call')) throw new Error('FAIL: Missing Call action');
    if (!gymData.actionLabels.includes('WhatsApp')) throw new Error('FAIL: Missing WhatsApp action');
    if (!gymData.actionLabels.includes('Instagram')) throw new Error('FAIL: Missing Instagram action');
    if (!gymData.actionLabels.includes('Website')) throw new Error('FAIL: Missing Website action');

    // Strict absence checks (CRITICAL REQUIREMENT: Gym must NEVER display restaurant menu!)
    if (gymData.hasMenu) throw new Error('CRITICAL FAIL: Gym profile displayed a Menu or Document action!');
    if (gymData.actionLabels.includes('Review Us')) throw new Error('FAIL: Gym displayed Review Us when not configured/entitled!');
    if (gymData.actionLabels.includes('Email')) throw new Error('FAIL: Email rendered when unconfigured!');
    if (gymData.actionLabels.includes('Google Maps')) throw new Error('FAIL: Google Maps rendered when unconfigured!');

    // Dock verification: Call, WhatsApp, Website (Count = 3, no Email)
    if (gymData.dockLabels.length !== 3 || !gymData.dockLabels.includes('Call') || !gymData.dockLabels.includes('WhatsApp') || !gymData.dockLabels.includes('Website')) {
      throw new Error(`FAIL: Gym dock must contain Call, WhatsApp, and Website only, got: ${gymData.dockLabels}`);
    }
    if (gymData.dockLabels.includes('Email')) throw new Error('FAIL: Gym dock contained Email when unconfigured!');

    await client.captureScreenshot('gym_public_card.png');
    console.log('✅ TEST CASE 2 PASSED: Gym displays only configured actions with zero menu/review leak.');

    // ─────────────────────────────────────────────────────────────────
    // VERIFICATION 3: PROFESSIONAL SERVICE (Apex Legal Partners)
    // ─────────────────────────────────────────────────────────────────
    console.log('\n================================================================');
    console.log(' TEST CASE 3: PROFESSIONAL SERVICE PROFILE (Apex Legal Partners)');
    console.log('================================================================');
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/?b=service_demo`, 2000);
    await waitForSelector(client, '.vcard-phone-shell', 5000);

    const srvData = await client.evaluate(`
      (() => {
        const title = document.querySelector('.vcard-business-name')?.textContent?.trim();
        const category = document.querySelector('.vcard-category-tag')?.textContent?.trim();
        const actionLabels = Array.from(document.querySelectorAll('.vcard-grid-tile .vcard-tile-label')).map(el => el.textContent.trim());
        const dockLabels = Array.from(document.querySelectorAll('.vcard-dock-item .vcard-dock-label')).map(el => el.textContent.trim());
        const gridClass = document.querySelector('.vcard-action-grid')?.className;
        const gridCount = document.querySelector('.vcard-action-grid')?.getAttribute('data-count');
        return { title, category, actionLabels, dockLabels, gridClass, gridCount };
      })()
    `);

    console.log('Rendered Professional Service Profile:', JSON.stringify(srvData, null, 2));

    if (srvData.title !== 'Apex Legal Partners') throw new Error(`FAIL: Expected 'Apex Legal Partners', got '${srvData.title}'`);
    if (srvData.category !== 'CORPORATE LEGAL CONSULTANCY') throw new Error(`FAIL: Unexpected category '${srvData.category}'`);

    // Expected actions: Save Contact, Call, Email, Website
    if (!srvData.actionLabels.includes('Save Contact')) throw new Error('FAIL: Missing Save Contact action');
    if (!srvData.actionLabels.includes('Call')) throw new Error('FAIL: Missing Call action');
    if (!srvData.actionLabels.includes('Email')) throw new Error('FAIL: Missing Email action');
    if (!srvData.actionLabels.includes('Website')) throw new Error('FAIL: Missing Website action');

    // Strict absence checks: NO Instagram, NO WhatsApp, NO Menu/Docs, NO Review Us, NO Maps!
    if (srvData.actionLabels.includes('WhatsApp') || srvData.actionLabels.includes('WhatsApp Group')) {
      throw new Error('FAIL: Professional service displayed WhatsApp when unconfigured!');
    }
    if (srvData.actionLabels.includes('Instagram')) throw new Error('FAIL: Service displayed Instagram when unconfigured!');
    if (srvData.actionLabels.includes('Review Us')) throw new Error('FAIL: Service displayed Review Us when unconfigured!');
    if (srvData.actionLabels.some(l => l.toLowerCase().includes('menu') || l.toLowerCase().includes('doc'))) {
      throw new Error('FAIL: Service displayed Menu/Docs when unconfigured!');
    }

    // Dock verification: Call, Email, Website (Count = 3, NO WhatsApp)
    if (srvData.dockLabels.length !== 3 || !srvData.dockLabels.includes('Call') || !srvData.dockLabels.includes('Email') || !srvData.dockLabels.includes('Website')) {
      throw new Error(`FAIL: Professional service dock must contain Call, Email, and Website only, got: ${srvData.dockLabels}`);
    }
    if (srvData.dockLabels.includes('WhatsApp')) throw new Error('FAIL: Service dock contained WhatsApp when unconfigured!');

    // Grid layout symmetry check
    if (!srvData.gridClass.includes('vcard-grid-count-4') || srvData.gridCount !== '4') {
      throw new Error(`FAIL: Expected symmetric grid count 4 layout, got class: ${srvData.gridClass}`);
    }

    await client.captureScreenshot('professional_service_public_card.png');
    console.log('✅ TEST CASE 3 PASSED: Professional service has 4-action symmetric grid and no WhatsApp/Menu leak.');

    // ─────────────────────────────────────────────────────────────────
    // VERIFICATION 4: UNPUBLISHED DRAFT PRIVACY
    // ─────────────────────────────────────────────────────────────────
    console.log('\n================================================================');
    console.log(' TEST CASE 4: UNPUBLISHED DRAFT PRIVACY BOUNDARY');
    console.log('================================================================');
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/?b=draft_demo`, 2000);
    await waitForSelector(client, '.vcard-empty-panel', 5000);

    const draftText = await client.evaluate(`document.querySelector('.vcard-empty-title')?.textContent?.trim()`);
    if (draftText !== 'Business Card Not Available') {
      throw new Error(`FAIL: Expected 'Business Card Not Available', got '${draftText}'`);
    }

    await client.captureScreenshot('unpublished_private_card.png');
    console.log('✅ TEST CASE 4 PASSED: Unpublished card is strictly inaccessible to public visitors.');

    // ─────────────────────────────────────────────────────────────────
    // VERIFICATION 5: MULTI-TENANT AUTHORIZATION & EDIT ISOLATION
    // ─────────────────────────────────────────────────────────────────
    console.log('\n================================================================');
    console.log(' TEST CASE 5: MULTI-TENANT AUTHORIZATION & EDIT ISOLATION');
    console.log('================================================================');
    // Open editor login for gym_demo
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/owner/gym_demo/card`, 1500);

    // Sign in as Pulse Fitness owner via browser session login
    const loginRes = await client.evaluate(`
      (async () => {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: 'owner@pulsefitness.test',
            password: 'PulseOwner2026!',
            tenant_id: 'gym_demo'
          })
        });
        return { status: res.status, body: await res.json().catch(() => ({})) };
      })()
    `);
    console.log(`[+] Pulse Fitness owner login status: ${loginRes.status}`);
    if (loginRes.status !== 200) {
      throw new Error(`FAIL: Owner login failed with status: ${loginRes.status}`);
    }

    // Reload editor page to verify authenticated view
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/owner/gym_demo/card`, 1500);
    await waitForSelector(client, '.editor-heading', 8000);
    console.log('[+] Pulse Fitness owner successfully signed in to Card Studio.');

    // Attempt illegal cross-tenant mutation: Pulse owner tries to modify Restaurant profile
    const attackResult = await client.evaluate(`
      (async () => {
        const res = await fetch('/api/businesses/restaurant_demo/profile', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ display_name: 'Hacked Restaurant By Gym Owner' })
        });
        return { status: res.status };
      })()
    `);

    console.log(`Cross-tenant edit HTTP status: ${attackResult.status}`);
    if (attackResult.status !== 403) {
      throw new Error(`SECURITY VULNERABILITY: Cross-tenant edit was not rejected with 403 Forbidden! Status: ${attackResult.status}`);
    }
    console.log('✅ TEST CASE 5.1 PASSED: Gym owner cannot edit Restaurant profile (HTTP 403 Forbidden).');

    // Legitimately update Gym's own tagline
    const updateResult = await client.evaluate(`
      (async () => {
        const res = await fetch('/api/businesses/gym_demo/profile', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tagline: 'State-of-the-Art Training Facility' })
        });
        return { status: res.status, json: await res.json() };
      })()
    `);
    if (updateResult.status !== 200) {
      throw new Error(`FAIL: Legitimate owner edit failed with status: ${updateResult.status}`);
    }
    console.log('✅ TEST CASE 5.2 PASSED: Gym owner successfully updated gym profile.');

    // Verify Restaurant profile was NOT modified in the database
    const verifyRestUnchanged = await client.evaluate(`
      (async () => {
        const res = await fetch('/api/businesses/restaurant_demo/card');
        const json = await res.json();
        return json.business_name;
      })()
    `);
    if (verifyRestUnchanged !== 'Saffron Spice Bistro') {
      throw new Error(`FAIL: Restaurant name was altered! Current: '${verifyRestUnchanged}'`);
    }
    console.log('✅ TEST CASE 5.3 PASSED: Restaurant profile is 100% isolated and unchanged.');

    console.log('\n================================================================');
    console.log(' ALL ACCEPTANCE TESTS PASSED WITH 100% EVIDENCE!');
    console.log('================================================================');
  } finally {
    client.close();
    chromeProc.kill('SIGKILL');
    backendProc.kill('SIGTERM');
    frontendProc.kill('SIGTERM');
    try { rmSync(AUDIT_DIR, { recursive: true, force: true }); } catch {}
  }
}

main().catch((err) => {
  console.error('\n❌ AUDIT FAILED:', err);
  process.exit(1);
});
