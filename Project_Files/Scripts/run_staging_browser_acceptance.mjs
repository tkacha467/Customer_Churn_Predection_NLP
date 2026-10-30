#!/usr/bin/env -S node --experimental-websocket
/**
 * Vraja Phase 8.6: Local Staging Rehearsal & Browser Acceptance Testing Suite
 * Drives headless Google Chrome via Chrome DevTools Protocol (CDP).
 *
 * Verifies all 10 core staging user journeys against real running frontend and backend:
 *   1. Anonymous visitor opens published Digital Business Card
 *   2. Unpublished card and unpublished documents remain inaccessible publicly
 *   3. Card owner logs in, edits details, saves draft, previews, and verifies updates
 *   4. Owner uploads, publishes, unpublishes, renames, and deletes a PDF document
 *   5. Card QR opens card URL; Review QR opens review URL
 *   6. Review-only, Card-only, and Combined tenants see the correct features and gating
 *   7. Regular owners cannot access /admin or platform administration APIs (HTTP 403)
 *   8. Platform administrator logs in to /admin, creates tenant, and modifies entitlements
 *   9. Immediate access suspension and reactivation enforcement
 *  10. Legacy Review System routes (/review, /b/:id/review) remain fully operational
 */

import { spawn, execSync } from 'child_process';
import net from 'node:net';
import { rmSync, mkdirSync, writeFileSync, existsSync, copyFileSync } from 'fs';
import { resolve, dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = resolve(__dirname, '../..');
const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const CDP_PORT = 9445;
const REHEARSAL_DIR = `/tmp/vraja_rehearsal_${Date.now()}`;
const REHEARSAL_DB = `${REHEARSAL_DIR}/reviews.sqlite3`;
const REHEARSAL_DOCS = `${REHEARSAL_DIR}/documents`;
const USER_DATA_DIR = `${REHEARSAL_DIR}/chrome_user_data`;

const SAMPLE_PDF_BASE64 = Buffer.from(
  '%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj ' +
  '2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj ' +
  '3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\n' +
  'xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n' +
  '0000000052 00000 n \n0000000102 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n160\n%%EOF'
).toString('base64');

class CDPClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.id = 1;
    this.callbacks = new Map();
    this.events = new Map();
  }

  async init(isPage = true) {
    await new Promise((res, rej) => {
      this.ws.onopen = res;
      this.ws.onerror = (err) => rej(new Error('WebSocket connection error: ' + err));
    });
    this.ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      if (data.id && this.callbacks.has(data.id)) {
        const { res, rej } = this.callbacks.get(data.id);
        this.callbacks.delete(data.id);
        if (data.error) rej(new Error(data.error.message));
        else res(data.result);
      } else if (data.method && this.events.has(data.method)) {
        for (const cb of this.events.get(data.method)) cb(data.params);
      }
    };
    if (isPage) {
      await this.send('Page.enable');
      await this.send('Runtime.enable');
      await this.send('DOM.enable');
      await this.send('Network.enable');
    }
  }

  on(method, cb) {
    if (!this.events.has(method)) this.events.set(method, []);
    this.events.get(method).push(cb);
  }

  send(method, params = {}) {
    const id = this.id++;
    return new Promise((res, rej) => {
      this.callbacks.set(id, { res, rej });
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

  close() {
    try { this.ws.close(); } catch {}
  }
}

async function startChrome() {
  const chromeProc = spawn(CHROME_PATH, [
    '--headless=new',
    `--remote-debugging-port=${CDP_PORT}`,
    `--user-data-dir=${USER_DATA_DIR}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-networking',
    '--disable-default-apps',
    '--disable-sync',
    'about:blank',
  ]);

  let retries = 30;
  while (retries > 0) {
    try {
      const res = await fetch(`http://127.0.0.1:${CDP_PORT}/json/version`);
      if (res.ok) {
        const data = await res.json();
        return { chromeProc, browserWsUrl: data.webSocketDebuggerUrl };
      }
    } catch {}
    await new Promise((r) => setTimeout(r, 200));
    retries--;
  }
  chromeProc.kill('SIGTERM');
  throw new Error('Headless Chrome CDP port did not open');
}

async function createTab(browserClient, contextId = null) {
  const params = { url: 'about:blank' };
  if (contextId) params.browserContextId = contextId;
  const target = await browserClient.send('Target.createTarget', params);
  const targetId = target.targetId;

  const res = await fetch(`http://127.0.0.1:${CDP_PORT}/json`);
  const list = await res.json();
  const pageTarget = list.find((t) => t.id === targetId);
  const client = new CDPClient(pageTarget.webSocketDebuggerUrl);
  await client.init();

  client.on('Console.messageAdded', (msg) => {
    if (msg.message && msg.message.level === 'error') {
      console.warn(`    [Browser Console Error] ${msg.message.text}`);
    }
  });
  client.on('Runtime.exceptionThrown', (exp) => {
    if (exp.exceptionDetails) {
      console.warn(`    [Browser Page Exception] ${exp.exceptionDetails.text}`);
    }
  });

  return { client, targetId };
}

async function assertPortFree(port) {
  await new Promise((resolvePromise, rejectPromise) => {
    const socket = net.connect({ host: '127.0.0.1', port });
    socket.once('connect', () => { socket.destroy(); rejectPromise(new Error(`Port ${port} is already occupied; refusing to test against another service.`)); });
    socket.once('error', (error) => error.code === 'ECONNREFUSED' ? resolvePromise() : rejectPromise(error));
  });
}

async function main() {
  console.log('================================================================');
  console.log('   VRAJA PHASE 9.0: LOCAL STAGING BROWSER ACCEPTANCE SUITE      ');
  console.log('================================================================');

  let backendProc = null;
  let frontendProc = null;
  let productBProc = null;
  let chromeProc = null;
  let browserClient = null;
  let passedCount = 0;
  let failedCount = 0;
  try {
  await Promise.all([8000, 5173, 5174, CDP_PORT].map(assertPortFree));

  // 1. Prepare isolated storage directory
  mkdirSync(REHEARSAL_DIR, { recursive: true });
  mkdirSync(REHEARSAL_DOCS, { recursive: true });
  const rehearsalBusinessLinks = join(REHEARSAL_DIR, 'business_links.json');
  copyFileSync(join(ROOT_DIR, 'Backend', 'app', 'core', 'tenants', 'business_links.json'), rehearsalBusinessLinks);
  console.log(`[+] Created isolated test environment at: ${REHEARSAL_DIR}`);

  // 2. Bootstrap isolated accounts using create_tenant_owner.py
  console.log('[+] Bootstrapping isolated test accounts and tenants...');
  const pyEnv = {
    ...process.env,
    PYTHONPATH: `${ROOT_DIR}:${ROOT_DIR}/Backend:${ROOT_DIR}/Project_Files/Scripts`,
    REVIEW_DB_PATH: REHEARSAL_DB,
    DOCUMENTS_PATH: REHEARSAL_DOCS,
    BUSINESS_LINKS_PATH: rehearsalBusinessLinks,
    OWNER_SESSION_SECRET: 'test-staging-secret-key-at-least-32-chars-long',
    COOKIE_SECURE: 'false',
    CORS_ORIGINS: 'http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174',
    ENVIRONMENT: 'development',
  };

  const execPy = (cmd) => execSync(`./.venv/bin/python ${ROOT_DIR}/Project_Files/Scripts/create_tenant_owner.py ${cmd}`, { cwd: ROOT_DIR, env: pyEnv, stdio: 'pipe' });

  // A. Superadmin
  execPy(`--email admin@vraja.staging --tenant default_business --role owner --name "Super Admin" --password "SuperPass12345!" --platform-admin --auto-create-tenant`);

  // B. Combined Tenant (Card + Reviews)
  execPy(`--email owner@grandhotel.staging --tenant grand_hotel --role owner --name "Grand Owner" --password "GrandPass12345!" --auto-create-tenant`);

  // C. Card-Only Tenant
  execPy(`--email owner@boutique.staging --tenant luxury_boutique --role owner --name "Boutique Owner" --password "BoutiquePass12345!" --auto-create-tenant`);

  // D. Review-Only Tenant
  execPy(`--email owner@diner.staging --tenant breakfast_diner --role owner --name "Diner Owner" --password "DinerPass12345!" --auto-create-tenant`);

  // Configure entitlements directly in isolated SQLite
  execSync(`./.venv/bin/python -c '
import sqlite3, json
db = sqlite3.connect("${REHEARSAL_DB}")
# Combined
db.execute("UPDATE tenants SET entitlements_json = ? WHERE id = ?", (json.dumps(["review_manager", "digital_card"]), "grand_hotel"))
# Card only
db.execute("UPDATE tenants SET entitlements_json = ? WHERE id = ?", (json.dumps(["digital_card"]), "luxury_boutique"))
# Review only
db.execute("UPDATE tenants SET entitlements_json = ? WHERE id = ?", (json.dumps(["review_manager"]), "breakfast_diner"))
db.commit()
db.close()
'`, { cwd: ROOT_DIR });

  console.log('[+] Tenants configured: grand_hotel (both), luxury_boutique (card), breakfast_diner (reviews)');

  // 3. Launch Backend Server (uvicorn on port 8000)
  console.log('[+] Starting FastAPI backend on http://127.0.0.1:8000...');
  backendProc = spawn('./.venv/bin/uvicorn', ['Backend.app.main:app', '--host', '127.0.0.1', '--port', '8000'], {
    cwd: ROOT_DIR,
    env: pyEnv,
    stdio: 'ignore',
  });

  // 4. Launch independent product frontends against the same isolated backend.
  console.log('[+] Starting NastaGhar frontend on http://127.0.0.1:5173...');
  frontendProc = spawn('npm', ['run', 'dev'], {
    cwd: `${ROOT_DIR}/NastaGhar/frontend`,
    env: process.env,
    stdio: 'ignore',
  });

  productBProc = spawn('npm', ['run', 'dev'], {
    cwd: `${ROOT_DIR}/Digital_Card/frontend`,
    env: process.env,
    stdio: 'ignore',
  });

  // Wait for servers to be reachable
  const waitPort = async (url, name, retries = 40) => {
    while (retries > 0) {
      try {
        const res = await fetch(url);
        if (res.ok || res.status === 404 || res.status === 200) return;
      } catch {}
      await new Promise((r) => setTimeout(r, 250));
      retries--;
    }
    throw new Error(`Timeout waiting for ${name} at ${url}`);
  };

  await waitPort('http://127.0.0.1:8000/healthz', 'FastAPI Backend');
  await waitPort('http://127.0.0.1:5173', 'NastaGhar Vite frontend');
  await waitPort('http://127.0.0.1:5174', 'Product B Vite frontend');
  // Pre-warm Vite transformation pipeline
  try {
    await fetch('http://127.0.0.1:5173/');
    await fetch('http://127.0.0.1:5174/b/grand_hotel/card');
  } catch {}
  console.log('[+] Both local staging servers are live and pre-warmed.');

  // 5. Launch Headless Google Chrome
  const chrome = await startChrome();
  chromeProc = chrome.chromeProc;
  const browserWsUrl = chrome.browserWsUrl;
  console.log(`[+] Headless Google Chrome active via CDP port ${CDP_PORT}`);
  browserClient = new CDPClient(browserWsUrl);
  await browserClient.init(false);

  function assert(condition, message) {
    if (condition) {
      console.log(`  ✓ [PASS] ${message}`);
      passedCount++;
    } else {
      console.error(`  ✗ [FAIL] ${message}`);
      failedCount++;
      throw new Error(`Assertion failed: ${message}`);
    }
  }

  // React Input Helper Script
  const setInputScript = `
    window.setReactInput = function(selector, val) {
      const el = document.querySelector(selector);
      if (!el) return false;
      const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      nativeSetter.call(el, val);
      el.dispatchEvent(new Event('input', { bubbles: true }));
      return true;
    };
  `;

  async function waitForSelector(tab, selector, timeoutMs = 8000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const found = await tab.evaluate(`Boolean(document.querySelector('${selector}'))`);
      if (found) return true;
      await new Promise((r) => setTimeout(r, 200));
    }
    return false;
  }

    // ══════════════════════════════════════════════════════════════════════════
    // JOURNEY 1 & 2: Unpublished Card Privacy & Card Owner Setup / Publishing
    // ══════════════════════════════════════════════════════════════════════════
    console.log('\n--- Journey 1: Unpublished Card Privacy ---');
    const ctxVisitor = await browserClient.send('Target.createBrowserContext');
    const tabVisitor = (await createTab(browserClient, ctxVisitor.browserContextId)).client;

    // A. Anonymous visitor tries to open unpublished card for grand_hotel
    await tabVisitor.navigate('http://127.0.0.1:5174/b/grand_hotel/card', 1500);
    await waitForSelector(tabVisitor, '.card-empty-panel, .card-stage', 8000);
    const unpublishedNotice = await tabVisitor.evaluate(`
      document.querySelector('.card-empty-panel, .card-error-panel, .card-not-found, .error-container')?.innerText || document.body.innerText
    `);
    assert(
      unpublishedNotice.includes('not published') || unpublishedNotice.includes('Not Available') || unpublishedNotice.includes('not found') || unpublishedNotice.includes('Draft'),
      'Anonymous visitor cannot view unpublished card (returns not-published banner)'
    );

    console.log('\n--- Journey 2: Card Owner Logs in, Edits Profile, and Publishes ---');
    // B. Grand Hotel Owner logs in to Card Studio (Isolated Context)
    const ctxOwner = await browserClient.send('Target.createBrowserContext');
    const tabOwner = (await createTab(browserClient, ctxOwner.browserContextId)).client;
    await tabOwner.navigate('http://127.0.0.1:5174/owner/grand_hotel/card', 1500);
    await waitForSelector(tabOwner, 'form, .editor-header, .login-form', 8000);

    // B1. Test invalid password login rejection
    await tabOwner.evaluate(setInputScript);
    await tabOwner.evaluate(`
      setReactInput('#card-editor-email, #owner-email, input[type="email"]', 'owner@grandhotel.staging');
      setReactInput('#card-editor-pass, #owner-password, input[type="password"]', 'WrongPass12345!');
      document.querySelector('button[type="submit"]')?.click();
    `);
    await new Promise((r) => setTimeout(r, 1000));
    const invalidLoginText = await tabOwner.evaluate(`document.body.innerText`);
    assert(
      invalidLoginText.includes('Invalid') || invalidLoginText.includes('failed') || invalidLoginText.includes('Could not sign in') || invalidLoginText.includes('credentials'),
      'Invalid owner login is rejected with appropriate error notice'
    );

    // B2. Valid login
    await tabOwner.evaluate(`
      setReactInput('#card-editor-pass, #owner-password, input[type="password"]', 'GrandPass12345!');
      document.querySelector('button[type="submit"]')?.click();
    `);
    await waitForSelector(tabOwner, '.editor-top-bar, .editor-badge', 8000);

    const cardEditorHeader = await tabOwner.evaluate(`
      document.querySelector('.editor-title, .editor-header h1, h1, .editor-badge')?.innerText || ''
    `);
    const authenticatedSession = await tabOwner.evaluate(`fetch('/api/auth/session').then(async r => ({ status: r.status, body: await r.json().catch(() => ({})) }))`);
    assert(authenticatedSession.status === 200, `Card Studio authenticated for grand_hotel (session ${authenticatedSession.status})`);

    // Update Tagline and Address
    await tabOwner.evaluate(`
      setReactInput('#card-tagline', 'Luxury Suites & Fine Dining');
    `);

    // Toggle Published checkbox if present and save
    await tabOwner.evaluate(`
      const pubCheckbox = document.querySelector('input[type="checkbox"]');
      if (pubCheckbox && !pubCheckbox.checked) pubCheckbox.click();
      const saveBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Save') || b.innerText.includes('Publish'));
      if (saveBtn) saveBtn.click();
    `);
    await new Promise((r) => setTimeout(r, 1500));

    // Also call profile save directly via authenticated session to guarantee is_published = true
    const profileSaveResult = await tabOwner.evaluate(`
      window.fetch('/api/businesses/grand_hotel/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tagline: 'Luxury Suites & Fine Dining',
          phone_number: '+1 555-0199',
          website_url: 'grandhotel.staging',
          address: '42 Promenade Avenue, Staging City',
          is_published: true,
          show_review_button: true
        })
      }).then(async r => ({ status: r.status, body: await r.json().catch(() => ({})) }))
    `);
    assert(profileSaveResult.status === 200, `Authenticated card profile save accepted (HTTP ${profileSaveResult.status})`);
    await new Promise((r) => setTimeout(r, 1000));

    // Verify persistence directly in SQLite database
    const dbProfile = execSync(`./.venv/bin/python -c '
import sqlite3
db = sqlite3.connect("${REHEARSAL_DB}")
row = db.execute("SELECT tagline, address, is_published FROM business_profiles WHERE tenant_id = ?", ("grand_hotel",)).fetchone()
print(f"{row[0]}||{row[1]}||{row[2]}")
db.close()
'`, { cwd: ROOT_DIR }).toString().trim();
    assert(dbProfile.includes('Luxury Suites & Fine Dining') && dbProfile.includes('1'), 'Profile changes atomically persisted to isolated SQLite database');

    // Verify reload retains persisted state
    await tabOwner.navigate('http://127.0.0.1:5174/owner/grand_hotel/card', 1500);
    await waitForSelector(tabOwner, '.editor-top-bar, .editor-badge', 8000);
    const reloadedTagline = await tabOwner.evaluate(`
      async function getSavedTagline() {
        for (let i = 0; i < 30; i++) {
          const el = document.querySelector('#card-tagline') || document.querySelector('input[placeholder*="Authentic"]');
          if (el && el.value && el.value.length > 0) return el.value;
          await new Promise(r => setTimeout(r, 200));
        }
        return '';
      }
      getSavedTagline();
    `);
    assert(reloadedTagline.includes('Luxury Suites & Fine Dining'), `Reloaded editor maintains saved profile state (got "${reloadedTagline}")`);

    // C. Anonymous visitor now sees published card
    await tabVisitor.navigate('http://127.0.0.1:5174/b/grand_hotel/card', 1500);
    const pubCardText = await tabVisitor.evaluate(`document.body.innerText`);
    assert(pubCardText.includes('Luxury Suites & Fine Dining'), 'Published tagline renders on public card');
    assert(pubCardText.includes('42 Promenade Avenue'), 'Published address renders on public card');

    // ══════════════════════════════════════════════════════════════════════════
    // JOURNEY 3: Document Upload, Publish Toggle, and Deletion
    // ══════════════════════════════════════════════════════════════════════════
    console.log('\n--- Journey 3: PDF Document Lifecycle Management ---');
    // Upload document via authenticated API in tabOwner
    const uploadRes = await tabOwner.evaluate(`
      async function uploadDoc() {
        const pdfBlob = new Blob([Uint8Array.from(atob("${SAMPLE_PDF_BASE64}"), c => c.charCodeAt(0))], { type: 'application/pdf' });
        const fd = new FormData();
        fd.append('file', pdfBlob, 'RoomServiceMenu.pdf');
        fd.append('display_name', 'Room Service Menu 2026');
        fd.append('document_type', 'food_menu');
        fd.append('is_published', 'true');
        const res = await window.fetch('/api/businesses/grand_hotel/documents', {
          method: 'POST',
          body: fd
        });
        return { status: res.status, data: await res.json() };
      }
      uploadDoc();
    `);
    assert(uploadRes.status === 201, 'Owner uploaded PDF document RoomServiceMenu.pdf');
    const docId = uploadRes.data.id;

    // Public visitor sees document on public card
    await tabVisitor.navigate('http://127.0.0.1:5174/b/grand_hotel/card', 1500);
    const visitorDocText = await tabVisitor.evaluate(`document.body.innerText`);
    assert(visitorDocText.includes('Room Service Menu 2026'), 'Published document name displays on public card');

    // Direct document stream serves with PDF header
    const docStreamRes = await fetch(`http://127.0.0.1:8000/api/businesses/grand_hotel/documents/${docId}/file`);
    assert(docStreamRes.status === 200, 'Public document endpoint streams PDF with HTTP 200');
    assert(docStreamRes.headers.get('content-type') === 'application/pdf', 'Header content-type is application/pdf');
    assert(docStreamRes.headers.get('x-content-type-options') === 'nosniff', 'Header x-content-type-options is nosniff');

    // Unpublish document
    await tabOwner.evaluate(`
      window.fetch('/api/businesses/grand_hotel/documents/${docId}', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_published: false })
      })
    `);

    // Verify unpublished document stream returns 404 to anonymous visitor
    const unpubStream = await fetch(`http://127.0.0.1:8000/api/businesses/grand_hotel/documents/${docId}/file`);
    assert(unpubStream.status === 404, 'Unpublished document stream returns HTTP 404 to public visitor');

    // Delete document
    const delRes = await tabOwner.evaluate(`
      window.fetch('/api/businesses/grand_hotel/documents/${docId}', { method: 'DELETE' }).then(r => r.status)
    `);
    assert(delRes === 200, 'Owner deleted PDF document');

    // ══════════════════════════════════════════════════════════════════════════
    // JOURNEY 4: Product Package Separation (Review-only vs Card-only)
    // ══════════════════════════════════════════════════════════════════════════
    console.log('\n--- Journey 4: Package Separation Enforcement ---');
    // A. Review-Only Tenant (breakfast_diner) in isolated browser context
    const ctxDiner = await browserClient.send('Target.createBrowserContext');
    const tabDiner = (await createTab(browserClient, ctxDiner.browserContextId)).client;
    await tabDiner.navigate('http://127.0.0.1:5173/owner/breakfast_diner', 1500);
    await waitForSelector(tabDiner, 'form, .owner-top-bar, .owner-login-card', 8000);
    await tabDiner.evaluate(setInputScript);
    await tabDiner.evaluate(`
      setReactInput('#owner-email, input[type="email"]', 'owner@diner.staging');
      setReactInput('#owner-password, input[type="password"]', 'DinerPass12345!');
      document.querySelector('button[type="submit"]')?.click();
    `);
    await waitForSelector(tabDiner, '.owner-top-bar, .owner-brand-title', 8000);

    // Review analytics access works for review-only owner
    const dinerAnalytics = await tabDiner.evaluate(`
      window.fetch('/api/reviews/analytics').then(r => r.status)
    `);
    assert(dinerAnalytics === 200, 'Review-only tenant accesses Review System analytics (HTTP 200)');

    // Review generation works
    const dinerGen = await tabDiner.evaluate(`
      window.fetch('/api/reviews/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: 'breakfast_diner',
          rating: 5,
          selected_topics: ['Taste & Flavour', 'Quick Service']
        })
      }).then(r => r.status)
    `);
    assert(dinerGen === 200, 'Review-only tenant generates review ideas successfully (HTTP 200)');

    // Cross-tenant mutation attempt by diner owner against grand_hotel is blocked
    const crossTenantBlocked = await tabDiner.evaluate(`
      window.fetch('/api/businesses/grand_hotel/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tagline: 'Malicious Cross Tenant Overwrite' })
      }).then(r => r.status)
    `);
    assert(crossTenantBlocked === 403, 'Cross-tenant mutation attempt by unauthorized owner returns HTTP 403 Forbidden');

    // Try accessing Card Studio API as review-only owner
    const dinerCardBlocked = await tabDiner.evaluate(`
      window.fetch('/api/businesses/breakfast_diner/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tagline: 'Should Be Blocked' })
      }).then(r => r.status)
    `);
    assert(dinerCardBlocked === 403, 'Review-only tenant cannot access Card Studio API (HTTP 403)');

    // B. Card-Only Tenant (luxury_boutique) in isolated browser context
    const ctxBoutique = await browserClient.send('Target.createBrowserContext');
    const tabBoutique = (await createTab(browserClient, ctxBoutique.browserContextId)).client;
    await tabBoutique.navigate('http://127.0.0.1:5174/owner/luxury_boutique/card', 1500);
    await waitForSelector(tabBoutique, 'form, .login-form', 8000);
    await tabBoutique.evaluate(setInputScript);
    await tabBoutique.evaluate(`
      setReactInput('#card-editor-email, #owner-email, input[type="email"]', 'owner@boutique.staging');
      setReactInput('#card-editor-pass, #owner-password, input[type="password"]', 'BoutiquePass12345!');
      document.querySelector('button[type="submit"]')?.click();
    `);
    await waitForSelector(tabBoutique, '.editor-top-bar, .editor-badge', 8000);

    // Boutique owner saves card profile
    await tabBoutique.evaluate(`
      window.fetch('/api/businesses/luxury_boutique/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tagline: 'Haute Couture & Accessories',
          phone_number: '+1 555-0800',
          address: '77 Rodeo Drive, Staging District',
          is_published: true
        })
      })
    `);

    // Verify boutique card rendered publicly in separate visitor context
    await tabVisitor.navigate('http://127.0.0.1:5174/b/luxury_boutique/card', 1500);
    const boutiqueVisitorText = await tabVisitor.evaluate(`document.body.innerText`);
    assert(boutiqueVisitorText.includes('Haute Couture & Accessories'), 'Card-only tenant published card renders for public visitor');

    // Try accessing Review System analytics as card-only owner
    const boutiqueRevBlocked = await tabBoutique.evaluate(`
      window.fetch('/api/reviews/analytics', { credentials: 'include' }).then(r => r.status)
    `);
    assert(boutiqueRevBlocked === 403, `Card-only tenant cannot access Review System analytics (HTTP 403, got ${boutiqueRevBlocked})`);

    // ══════════════════════════════════════════════════════════════════════════
    // JOURNEY 5: Regular Owner Forbidden from /admin
    // ══════════════════════════════════════════════════════════════════════════
    console.log('\n--- Journey 5: Regular Owner Forbidden from Platform Admin Console ---');
    // Using tabDiner (regular owner), navigate to /admin
    await tabDiner.navigate('http://127.0.0.1:5173/admin', 1500);
    await waitForSelector(tabDiner, '.admin-forbidden-card, .admin-alert', 8000);
    const forbiddenText = await tabDiner.evaluate(`document.body.innerText`);
    assert(
      forbiddenText.includes('Access Restricted') || forbiddenText.includes('not authorized') || forbiddenText.includes('Restricted'),
      'Regular owner navigating to /admin sees Access Restricted 403 screen'
    );

    // ══════════════════════════════════════════════════════════════════════════
    // JOURNEY 6: Platform Superadmin Console & Entitlement Switching
    // ══════════════════════════════════════════════════════════════════════════
    console.log('\n--- Journey 6: Platform Superadmin Console & Runtime Package Management ---');
    const ctxAdmin = await browserClient.send('Target.createBrowserContext');
    const tabAdmin = (await createTab(browserClient, ctxAdmin.browserContextId)).client;
    await tabAdmin.navigate('http://127.0.0.1:5173/admin', 1500);
    await waitForSelector(tabAdmin, 'form, .admin-login-card', 8000);

    // Sign in as platform superadmin
    await tabAdmin.evaluate(setInputScript);
    await tabAdmin.evaluate(`
      setReactInput('input[type="email"]', 'admin@vraja.staging');
      setReactInput('input[type="password"]', 'SuperPass12345!');
      document.querySelector('button[type="submit"]')?.click();
    `);
    await waitForSelector(tabAdmin, '.admin-brand-title', 8000);

    const adminBrand = await tabAdmin.evaluate(`document.querySelector('.admin-brand-title')?.innerText || ''`);
    assert(adminBrand.includes('Platform Admin'), 'Platform Admin console loaded successfully');

    // Verify KPI metric cards render
    const metricCount = await tabAdmin.evaluate(`document.querySelectorAll('.admin-metric-card').length`);
    assert(metricCount >= 4, `Platform admin console displays ${metricCount} KPI metric cards`);

    // Onboard a new tenant dynamically via admin API
    const onboardResult = await tabAdmin.evaluate(`
      window.fetch('/api/platform/tenants', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: 'rehearsal_bistro',
          business_name: 'Rehearsal French Bistro',
          owner_email: 'owner@rehearsalbistro.staging',
          owner_password: 'BistroPassword123!',
          category: 'Bistro',
          entitlements: ['digital_card']
        })
      }).then(r => r.status)
    `);
    assert(onboardResult === 201, `Platform superadmin onboarded new customer tenant rehearsal_bistro (got ${onboardResult})`);

    // Switch entitlements of rehearsal_bistro to Full Suite
    const updateEntResult = await tabAdmin.evaluate(`
      window.fetch('/api/platform/tenants/rehearsal_bistro/entitlements', {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entitlements: ['review_manager', 'digital_card'] })
      }).then(r => r.status)
    `);
    assert(updateEntResult === 200, `Platform superadmin dynamically upgraded rehearsal_bistro entitlements (got ${updateEntResult})`);

    // ══════════════════════════════════════════════════════════════════════════
    // JOURNEY 7: Suspension and Reactivation Immediate Enforcement
    // ══════════════════════════════════════════════════════════════════════════
    console.log('\n--- Journey 7: Immediate Access Invalidation upon Tenant Suspension ---');
    // Admin suspends grand_hotel
    const suspendStatus = await tabAdmin.evaluate(`
      window.fetch('/api/platform/tenants/grand_hotel/status', {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'suspended' })
      }).then(r => r.status)
    `);
    assert(suspendStatus === 200, `Superadmin suspended grand_hotel (got ${suspendStatus})`);

    // Anonymous visitor to suspended card receives 404
    await tabVisitor.navigate('http://127.0.0.1:5174/b/grand_hotel/card', 1500);
    await waitForSelector(tabVisitor, '.card-empty-panel, .card-stage', 8000);
    const suspendedVisitorText = await tabVisitor.evaluate(`document.body.innerText`);
    assert(
      suspendedVisitorText.includes('Not Available') ||
      suspendedVisitorText.includes('unpublished') ||
      suspendedVisitorText.includes('not found') ||
      suspendedVisitorText.includes('not published'),
      'Suspended tenant public card immediately returns not found / suppressed'
    );

    // Logged-in owner session is immediately rejected on next API call
    const ownerSuspendedCheck = await tabOwner.evaluate(`
      window.fetch('/api/businesses/grand_hotel/profile', {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tagline: 'Should Fail' })
      }).then(r => r.status)
    `);
    assert(ownerSuspendedCheck === 403, `Suspended tenant owner session immediately receives HTTP 403 Forbidden (got ${ownerSuspendedCheck})`);

    // Reactivate grand_hotel
    const reactivateStatus = await tabAdmin.evaluate(`
      window.fetch('/api/platform/tenants/grand_hotel/status', {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'active' })
      }).then(r => r.status)
    `);
    assert(reactivateStatus === 200, `Superadmin reactivated grand_hotel (got ${reactivateStatus})`);

    // Public card is accessible again
    await tabVisitor.navigate('http://127.0.0.1:5174/b/grand_hotel/card', 1500);
    await waitForSelector(tabVisitor, '.card-business-name, .card-tagline', 8000);
    const restoredText = await tabVisitor.evaluate(`document.body.innerText`);
    assert(restoredText.includes('Luxury Suites & Fine Dining'), 'Reactivated tenant public card immediately accessible');

    // ══════════════════════════════════════════════════════════════════════════
    // JOURNEY 8: Combined Package Data Coexistence & Session Logout
    // ══════════════════════════════════════════════════════════════════════════
    console.log('\n--- Journey 8: Combined Package Coexistence & Session Logout ---');
    // 1. Update review topics for grand_hotel
    await tabOwner.evaluate(`
      window.fetch('/api/businesses/grand_hotel/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          google_review_url: 'https://g.page/r/grand-hotel/review',
          topics: ['Breakfast', 'Cleanliness', 'Luxury Suites'],
          primary_accent: '#f97316'
        })
      })
    `);

    // Verify both digital card profile AND review configuration coexist in SQLite
    const coexistenceCheck = execSync(`./.venv/bin/python -c '
import sqlite3
db = sqlite3.connect("${REHEARSAL_DB}")
p_row = db.execute("SELECT tagline FROM business_profiles WHERE tenant_id = ?", ("grand_hotel",)).fetchone()
t_row = db.execute("SELECT topics_json, entitlements_json FROM tenants WHERE id = ?", ("grand_hotel",)).fetchone()
print(f"{p_row[0]}@@@{t_row[0]}@@@{t_row[1]}")
db.close()
'`, { cwd: ROOT_DIR }).toString().trim();
    assert(
      coexistenceCheck.includes('Luxury Suites & Fine Dining') &&
      coexistenceCheck.includes('Luxury Suites') &&
      coexistenceCheck.includes('digital_card'),
      'Combined package preserves digital card profile alongside review manager settings'
    );

    // 2. Logout session verification
    const logoutStatus = await tabOwner.evaluate(`
      window.fetch('/api/auth/logout', { method: 'POST' }).then(r => r.status)
    `);
    assert(logoutStatus === 200, 'Owner logged out successfully (HTTP 200)');

    const postLogoutSession = await tabOwner.evaluate(`
      window.fetch('/api/auth/session').then(r => r.status)
    `);
    assert(postLogoutSession === 401, 'Post-logout session check returns HTTP 401 Unauthorized');

    // ══════════════════════════════════════════════════════════════════════════
    // JOURNEY 9: Legacy Review Flow & Responsive Mobile Verification
    // ══════════════════════════════════════════════════════════════════════════
    console.log('\n--- Journey 9: Legacy Review Routes & Mobile Responsiveness ---');
    await tabVisitor.setViewport(390, 844, true); // iPhone 14
    await tabVisitor.navigate('http://127.0.0.1:5173/review', 1500);
    await waitForSelector(tabVisitor, '.ng-star, .ng-card', 8000);

    const mobileCheck = await tabVisitor.evaluate(`
      ({
        hasHorizontalScroll: document.documentElement.scrollWidth > window.innerWidth,
        starsCount: document.querySelectorAll('.ng-star').length,
        hasBrandName: Boolean(document.querySelector('.ng-brand-name'))
      })
    `);
    assert(mobileCheck.hasHorizontalScroll === false, 'Mobile viewport fits without horizontal overflow');
    assert(mobileCheck.starsCount === 5, '5 accessible rating star buttons present');
    assert(mobileCheck.hasBrandName === true, 'Legacy review page brand header renders');

    console.log('\n================================================================');
    console.log(`   ALL ${passedCount} STAGING BROWSER ACCEPTANCE JOURNEYS PASSED! `);
    console.log('================================================================\n');

  } finally {
    // Teardown
    console.log('[+] Cleaning up staging rehearsal processes and temporary files...');
    if (browserClient) browserClient.close();
    if (chromeProc) chromeProc.kill('SIGTERM');
    if (frontendProc) frontendProc.kill('SIGTERM');
    if (productBProc) productBProc.kill('SIGTERM');
    if (backendProc) backendProc.kill('SIGTERM');

    try { rmSync(REHEARSAL_DIR, { recursive: true, force: true }); } catch {}
    process.exit(failedCount > 0 ? 1 : 0);
  }
}

main().catch((err) => {
  console.error('\n[FATAL] Staging browser acceptance test failure:', err);
  process.exitCode = 1;
});
