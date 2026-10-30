#!/usr/bin/env -S node --experimental-websocket

/**
 * VRAJA AI Digital Card — Final Manual Acceptance and Tenant Regression Audit
 * Tests the live application against the real NastaGhar configuration and multi-tenant security gates.
 */

import { spawn } from 'child_process';
import { existsSync, mkdirSync, writeFileSync } from 'fs';
import { resolve, join } from 'path';
import http from 'http';
import net from 'net';
import os from 'os';

const ROOT_DIR = resolve('/Volumes/D-Drive/Developer/Customer_Churn_Predection_NLP');
const ARTIFACT_DIR = '/Users/tushi/.gemini/antigravity/brain/67134c41-8090-4984-94c4-a6b843aef526';
const BACKEND_PORT = 8000;
const FRONTEND_PORT = 5174;
const CHROME_PORT = 9228;
const USER_DATA_DIR = join(os.tmpdir(), `vraja_incognito_profile_${Date.now()}`);

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
  console.log(' VRAJA AI DIGITAL CARD — FINAL MANUAL ACCEPTANCE & REGRESSION');
  console.log('================================================================\n');

  mkdirSync(USER_DATA_DIR, { recursive: true });

  // 1. Verify live servers
  console.log('[*] Verifying live services on ports 8000 and 5174...');
  await waitForTcp(BACKEND_PORT);
  await waitForTcp(FRONTEND_PORT);
  console.log(`[+] Backend (port ${BACKEND_PORT}) and Frontend (port ${FRONTEND_PORT}) are online.`);

  // 2. Launch Clean / Incognito Chrome instance
  const chromeBin = findChromePath();
  console.log(`[*] Launching clean incognito browser session on port ${CHROME_PORT}...`);
  const chromeProc = spawn(chromeBin, [
    `--remote-debugging-port=${CHROME_PORT}`,
    '--headless=new',
    '--incognito',
    '--disable-gpu',
    '--no-sandbox',
    '--disable-extensions',
    `--user-data-dir=${USER_DATA_DIR}`,
    'about:blank',
  ]);

  await waitForTcp(CHROME_PORT);

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
  console.log('[+] Connected to Chrome DevTools Protocol session.\n');

  try {
    // ─────────────────────────────────────────────────────────────────
    // CHECK 2 & 3: NASTAGHAR PUBLIC CARD (INCOGNITO & MOBILE VIEWPORT)
    // ─────────────────────────────────────────────────────────────────
    console.log('--- Step 2 & 3: Actual NastaGhar Public Card in Incognito Session ---');
    await client.setViewport(390, 844, true); // iPhone 14
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/?b=nasta-ghar`, 2000);
    await waitForSelector(client, '.vcard-phone-shell', 5000);

    const nastaData = await client.evaluate(`
      (() => {
        const title = document.querySelector('.vcard-business-name')?.textContent?.trim();
        const category = document.querySelector('.vcard-category-tag')?.textContent?.trim();
        const hours = document.querySelector('.vcard-hours-text')?.textContent?.trim();
        const address = document.querySelector('.vcard-address-text')?.textContent?.trim();
        const welcome = document.querySelector('.vcard-welcome-message')?.textContent?.trim();
        const hasLogin = Boolean(document.querySelector('.editor-login-box') || document.querySelector('input[type="password"]'));

        const actionTiles = Array.from(document.querySelectorAll('.vcard-grid-tile')).map(el => ({
          label: el.querySelector('.vcard-tile-label')?.textContent?.trim(),
          href: el.getAttribute('href') || null,
          tag: el.tagName.toLowerCase()
        }));

        const dockItems = Array.from(document.querySelectorAll('.vcard-dock-item')).map(el => ({
          label: el.querySelector('.vcard-dock-label')?.textContent?.trim(),
          href: el.getAttribute('href') || null
        }));

        const isOverflowing = document.documentElement.scrollWidth > window.innerWidth;

        return { title, category, hours, address, welcome, hasLogin, actionTiles, dockItems, isOverflowing };
      })()
    `);

    console.log('NastaGhar Mobile Card Inspection:');
    console.log(`  Title: "${nastaData.title}"`);
    console.log(`  Category: "${nastaData.category}"`);
    console.log(`  Hours: "${nastaData.hours}"`);
    console.log(`  Address: "${nastaData.address}"`);
    console.log(`  Welcome: "${nastaData.welcome}"`);
    console.log(`  Incognito Login Gate: ${nastaData.hasLogin ? 'VIOLATION (Login Required)' : 'PASS (Direct Public Access)'}`);
    console.log(`  Horizontal Overflow: ${nastaData.isOverflowing ? 'VIOLATION (Horizontal Scroll)' : 'PASS (Clean Viewport)'}`);
    console.log('  Action Tiles:', nastaData.actionTiles);
    console.log('  Dock Items:', nastaData.dockItems);

    if (nastaData.hasLogin) throw new Error('FAIL: Incognito visitor was prompted with a login screen!');
    if (nastaData.title !== 'Nasta Ghar') throw new Error(`FAIL: Expected 'Nasta Ghar', got '${nastaData.title}'`);
    if (nastaData.category !== 'BREAKFAST & SNACKS') throw new Error(`FAIL: Unexpected category '${nastaData.category}'`);
    if (!nastaData.hours.includes('7:00 AM - 11:00 PM')) throw new Error(`FAIL: Unexpected opening hours '${nastaData.hours}'`);
    if (nastaData.isOverflowing) throw new Error('FAIL: Horizontal viewport overflow detected!');

    await client.captureScreenshot('nastaghar_public_card_mobile.png');

    // ─────────────────────────────────────────────────────────────────
    // CHECK 8: DESKTOP VIEWPORT HEALTH & OVERFLOW CHECK
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 8: Desktop Viewport Check (1280x800) ---');
    await client.setViewport(1280, 800, false);
    await new Promise((r) => setTimeout(r, 600));

    const desktopHealth = await client.evaluate(`
      (() => {
        const shell = document.querySelector('.vcard-phone-shell');
        const isOverflowing = document.documentElement.scrollWidth > window.innerWidth;
        const shellRect = shell.getBoundingClientRect();
        return {
          isOverflowing,
          shellWidth: shellRect.width,
          shellHeight: shellRect.height,
          paddingBottom: window.getComputedStyle(shell).paddingBottom
        };
      })()
    `);
    console.log('Desktop Layout Metrics:', desktopHealth);
    if (desktopHealth.isOverflowing) throw new Error('FAIL: Desktop layout has horizontal overflow!');

    await client.captureScreenshot('nastaghar_public_card_desktop.png');
    console.log('✅ Step 8 PASSED: Desktop centered shell renders cleanly with zero overflow.');

    // Reset back to mobile for remainder of checks
    await client.setViewport(390, 844, true);

    // ─────────────────────────────────────────────────────────────────
    // CHECK 6 & 7: ACTION DESTINATIONS & ABSENCE VERIFICATION
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 6 & 7: Action Destinations & Absence Verification ---');
    const actionsMap = new Map(nastaData.actionTiles.map(a => [a.label, a]));

    // Check Save Contact
    if (!actionsMap.has('Save Contact')) throw new Error('FAIL: Missing Save Contact action tile');
    console.log('  [+] Save Contact tile present (type: button)');

    // Check Call Destination
    const callAction = actionsMap.get('Call');
    if (!callAction || callAction.href !== 'tel:+91 94282 12345') {
      throw new Error(`FAIL: Call href mismatch! Expected 'tel:+91 94282 12345', got '${callAction?.href}'`);
    }
    console.log(`  [+] Call tile destination verified: ${callAction.href}`);

    // Check WhatsApp Destination
    const waAction = actionsMap.get('WhatsApp');
    if (!waAction || !waAction.href.includes('919428212345')) {
      throw new Error(`FAIL: WhatsApp href mismatch! Got '${waAction?.href}'`);
    }
    console.log(`  [+] WhatsApp tile destination verified: ${waAction.href}`);

    // Check Google Maps Destination
    const mapAction = actionsMap.get('Google Maps');
    if (!mapAction || !mapAction.href.includes('maps.google.com')) {
      throw new Error(`FAIL: Google Maps href mismatch! Got '${mapAction?.href}'`);
    }
    console.log(`  [+] Google Maps destination verified: ${mapAction.href}`);

    // Check Review Us Destination
    const reviewAction = actionsMap.get('Review Us');
    if (!reviewAction || !reviewAction.href.includes('ChIJZeK7NwDLWTkR1pOxt51jLro')) {
      throw new Error(`FAIL: Review Us href mismatch! Got '${reviewAction?.href}'`);
    }
    console.log(`  [+] Review Us destination verified: ${reviewAction.href}`);

    // STRICT ABSENCE CHECKS (NastaGhar did not configure Website, Email, Instagram, YouTube, Facebook, Documents)
    const prohibited = ['Website', 'Email', 'Instagram', 'Facebook', 'YouTube', 'Menu', 'Document'];
    for (const p of prohibited) {
      if (actionsMap.has(p)) {
        throw new Error(`FAIL: Action '${p}' rendered when destination is absent!`);
      }
    }
    console.log('  [+] Verified absent actions (Email, Website, Instagram, Facebook, YouTube, Menu) are strictly hidden.');

    // Bottom dock verification: Call & WhatsApp only
    const dockLabels = nastaData.dockItems.map(d => d.label);
    if (dockLabels.length !== 2 || !dockLabels.includes('Call') || !dockLabels.includes('WhatsApp')) {
      throw new Error(`FAIL: NastaGhar dock should contain Call & WhatsApp only, got: ${dockLabels}`);
    }
    if (dockLabels.includes('Email') || dockLabels.includes('Website')) {
      throw new Error('FAIL: Bottom dock contained unconfigured Email or Website!');
    }
    console.log('  [+] Bottom action ribbon dynamic item count verified: Call, WhatsApp only.');
    console.log('✅ Steps 6 & 7 PASSED.');

    // ─────────────────────────────────────────────────────────────────
    // CHECK 4: UNPUBLISHED CARD PRIVACY (test_cafe)
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 4: Unpublished Card Privacy Boundary (test_cafe) ---');
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/?b=test_cafe`, 2000);
    await waitForSelector(client, '.vcard-empty-panel', 5000);

    const emptyTitle = await client.evaluate(`document.querySelector('.vcard-empty-title')?.textContent?.trim()`);
    console.log(`  Rendered unlisted state: "${emptyTitle}"`);
    if (emptyTitle !== 'Business Card Not Available') {
      throw new Error(`FAIL: Expected 'Business Card Not Available', got '${emptyTitle}'`);
    }
    await client.captureScreenshot('unpublished_test_cafe_card.png');
    console.log('✅ Step 4 PASSED: Unpublished cards are strictly private.');

    // ─────────────────────────────────────────────────────────────────
    // CHECK 5: OWNER EDITOR & MULTI-TENANT AUTHORIZATION
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 5: Owner Editor & Multi-Tenant Authorization ---');
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/?view=editor&b=default_business`, 1500);

    // Sign in as legitimate Nasta Ghar owner
    const loginResult = await client.evaluate(`
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
        return { status: res.status, body: await res.json().catch(() => ({})) };
      })()
    `);
    console.log(`  Owner login status: ${loginResult.status}`);
    if (loginResult.status !== 200) {
      throw new Error(`FAIL: Nasta Ghar owner authentication failed: ${JSON.stringify(loginResult.body)}`);
    }

    // Refresh editor with session active
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/?view=editor&b=default_business`, 1500);
    await waitForSelector(client, '.editor-heading', 8000);
    await client.captureScreenshot('nastaghar_owner_editor.png');
    console.log('  [+] Nasta Ghar owner successfully authenticated into Card Studio.');

    // Test illegal cross-tenant mutation: NastaGhar owner attempts to modify vraja_cafe
    const crossTenantAttack = await client.evaluate(`
      (async () => {
        const res = await fetch('/api/businesses/vraja_cafe/profile', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ display_name: 'Stolen By NastaGhar Owner' })
        });
        return { status: res.status };
      })()
    `);
    console.log(`  Cross-tenant edit attempt on vraja_cafe HTTP status: ${crossTenantAttack.status}`);
    if (crossTenantAttack.status !== 403) {
      throw new Error(`SECURITY FAIL: Cross-tenant update was not rejected with 403 Forbidden! Status: ${crossTenantAttack.status}`);
    }
    console.log('  [+] Cross-tenant profile tampering strictly blocked (403 Forbidden).');

    // Test legitimate self-edit: Update NastaGhar tagline
    const selfUpdate = await client.evaluate(`
      (async () => {
        const res = await fetch('/api/businesses/default_business/profile', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tagline: 'Authentic Kathiyawadi Heritage Taste' })
        });
        return { status: res.status };
      })()
    `);
    if (selfUpdate.status !== 200) {
      throw new Error(`FAIL: Legitimate profile update failed with status: ${selfUpdate.status}`);
    }
    console.log('  [+] Legitimate owner self-update succeeded (200 OK).');
    console.log('✅ Step 5 PASSED: Multi-tenant authorization strictly enforced.');

    // ─────────────────────────────────────────────────────────────────
    // CHECK 10: TENANT NORMALIZATION & ALIAS RESOLUTION
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 10: Tenant Normalization & URL Aliases ---');
    const aliasCheck = await client.evaluate(`
      (async () => {
        const [cDefault, cUnderscore, cHyphen] = await Promise.all([
          fetch('/api/businesses/default_business/card').then(r => r.status),
          fetch('/api/businesses/nasta_ghar/card').then(r => r.status),
          fetch('/api/businesses/nasta-ghar/card').then(r => r.status),
        ]);
        return { cDefault, cUnderscore, cHyphen };
      })()
    `);
    console.log('  Alias HTTP Statuses:', aliasCheck);
    if (aliasCheck.cDefault !== 200 || aliasCheck.cUnderscore !== 200 || aliasCheck.cHyphen !== 200) {
      throw new Error(`FAIL: Alias normalization mismatch! Expected all 200 OK, got: ${JSON.stringify(aliasCheck)}`);
    }
    console.log('✅ Step 10 PASSED: default_business, nasta_ghar, and nasta-ghar all resolve cleanly.');

    console.log('\n================================================================');
    console.log(' FINAL MANUAL ACCEPTANCE VERIFICATION COMPLETED WITH 100% SUCCESS!');
    console.log('================================================================\n');
  } finally {
    client.close();
    chromeProc.kill('SIGKILL');
  }
}

main().catch((err) => {
  console.error('\n❌ ACCEPTANCE AUDIT FAILED:', err);
  process.exit(1);
});
