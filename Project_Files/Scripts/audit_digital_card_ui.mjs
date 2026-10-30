#!/usr/bin/env -S node --experimental-websocket
/**
 * Digital Card — Live UI Audit & Evidence Capture
 * Drives headless Chrome via CDP to audit every UI control, field, tab, and public rendering.
 */

import { spawn, execSync } from 'child_process';
import net from 'node:net';
import { rmSync, mkdirSync, writeFileSync, existsSync } from 'fs';
import { resolve, dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = resolve(__dirname, '../..');
const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const BACKEND_PORT = 8010;
const FRONTEND_PORT = 5175;
const CDP_PORT = 9447;
const AUDIT_DIR = `/tmp/vraja_ui_audit_${Date.now()}`;
const AUDIT_DB = `${AUDIT_DIR}/reviews.sqlite3`;
const AUDIT_DOCS = `${AUDIT_DIR}/documents`;
const USER_DATA_DIR = `${AUDIT_DIR}/chrome_user_data`;
const ARTIFACT_DIR = '/Users/tushi/.gemini/antigravity/brain/67134c41-8090-4984-94c4-a6b843aef526';

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

  async captureScreenshot(filename) {
    const res = await this.send('Page.captureScreenshot', { format: 'png', quality: 90 });
    const buffer = Buffer.from(res.data, 'base64');
    const dest = join(ARTIFACT_DIR, filename);
    writeFileSync(dest, buffer);
    console.log(`[+] Captured screenshot saved to: ${dest}`);
    return dest;
  }

  close() {
    try { this.ws.close(); } catch {}
  }
}

async function startChrome() {
  mkdirSync(USER_DATA_DIR, { recursive: true });
  const chromeProc = spawn(CHROME_PATH, [
    '--headless=new',
    `--remote-debugging-port=${CDP_PORT}`,
    `--user-data-dir=${USER_DATA_DIR}`,
    '--no-first-run',
    '--no-default-browser-check',
    'about:blank',
  ], { stdio: 'ignore' });

  for (let i = 0; i < 30; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${CDP_PORT}/json/version`);
      if (res.ok) {
        const info = await res.json();
        return { chromeProc, browserWsUrl: info.webSocketDebuggerUrl };
      }
    } catch {}
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error('Chrome remote debugging did not respond.');
}

async function createTab(browserClient) {
  const target = await browserClient.send('Target.createTarget', { url: 'about:blank' });
  const targetId = target.targetId;

  const res = await fetch(`http://127.0.0.1:${CDP_PORT}/json`);
  const list = await res.json();
  const pageTarget = list.find((t) => t.id === targetId);
  const client = new CDPClient(pageTarget.webSocketDebuggerUrl);
  await client.init(true);
  return client;
}

async function waitForSelector(tab, selector, timeoutMs = 8000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const found = await tab.evaluate(`Boolean(document.querySelector('${selector}'))`);
    if (found) return true;
    await new Promise((r) => setTimeout(r, 200));
  }
  return false;
}

const SET_INPUT_SCRIPT = `
  window.setReactInput = function(selector, val) {
    const el = document.querySelector(selector);
    if (!el) return false;
    const proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
    const nativeSetter = Object.getOwnPropertyDescriptor(proto, 'value').set;
    nativeSetter.call(el, val);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  };
`;

async function main() {
  console.log('================================================================');
  console.log('   DIGITAL CARD: LIVE UI AUDIT & EVIDENCE CAPTURE               ');
  console.log('================================================================');

  let backendProc = null;
  let frontendProc = null;
  let chromeProc = null;
  let browserClient = null;
  let client = null;

  try {
    mkdirSync(AUDIT_DIR, { recursive: true });
    mkdirSync(AUDIT_DOCS, { recursive: true });

    // 1. Seed isolated tenant
    const pyEnv = {
      ...process.env,
      REVIEW_DB_PATH: AUDIT_DB,
      DOCUMENTS_PATH: AUDIT_DOCS,
      OWNER_SESSION_SECRET: 'audit-session-secret-key-entropy-32-chars!!',
      CORS_ORIGINS: 'http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5175,http://127.0.0.1:5175',
      ENVIRONMENT: 'development',
      BUSINESS_LINKS_PATH: `${ROOT_DIR}/Backend/app/core/tenants/business_links.json`,
    };

    const execPy = (cmd) => execSync(`./.venv/bin/python ${ROOT_DIR}/Project_Files/Scripts/create_tenant_owner.py ${cmd}`, { cwd: ROOT_DIR, env: pyEnv, stdio: 'pipe' });

    console.log('[+] Creating test owner and tenants in isolated test DB...');
    execPy(`--email owner@grandhotel.staging --tenant grand_hotel --role owner --name "Grand Owner" --password "GrandPass12345!" --auto-create-tenant`);
    execPy(`--email owner@boutique.staging --tenant luxury_boutique --role owner --name "Boutique Owner" --password "BoutiquePass12345!" --auto-create-tenant`);

    // Enable digital_card entitlement
    execSync(`./.venv/bin/python -c '
import sqlite3, json
db = sqlite3.connect("${AUDIT_DB}")
db.execute("UPDATE tenants SET entitlements_json = ? WHERE id = ?", (json.dumps(["review_manager", "digital_card"]), "grand_hotel"))
db.execute("UPDATE tenants SET entitlements_json = ? WHERE id = ?", (json.dumps(["digital_card"]), "luxury_boutique"))
db.commit()
db.close()
'`, { cwd: ROOT_DIR });

    // 2. Start Backend & Digital Card Frontend
    console.log(`[+] Starting FastAPI backend on http://127.0.0.1:${BACKEND_PORT}...`);
    backendProc = spawn('./.venv/bin/uvicorn', ['Backend.app.main:app', '--host', '127.0.0.1', '--port', String(BACKEND_PORT)], {
      cwd: ROOT_DIR,
      env: pyEnv,
      stdio: 'ignore',
    });

    console.log(`[+] Starting Digital Card frontend on http://127.0.0.1:${FRONTEND_PORT}...`);
    frontendProc = spawn('npm', ['run', 'dev', '--', '--port', String(FRONTEND_PORT)], {
      cwd: `${ROOT_DIR}/Digital_Card/frontend`,
      env: {
        ...process.env,
        VITE_BACKEND_URL: `http://127.0.0.1:${BACKEND_PORT}`,
      },
      stdio: 'ignore',
    });

    // Wait for ports
    const waitPort = async (url, retries = 40) => {
      while (retries > 0) {
        try {
          const res = await fetch(url);
          if (res.ok || res.status === 404 || res.status === 200) return;
        } catch {}
        await new Promise((r) => setTimeout(r, 250));
        retries--;
      }
      throw new Error(`Timeout waiting for ${url}`);
    };

    await Promise.all([
      waitPort(`http://127.0.0.1:${BACKEND_PORT}/healthz`),
      waitPort(`http://127.0.0.1:${FRONTEND_PORT}`),
    ]);
    console.log('[+] Both Backend and Digital Card Frontend are online!');

    // 3. Connect Chrome CDP
    const chrome = await startChrome();
    chromeProc = chrome.chromeProc;
    browserClient = new CDPClient(chrome.browserWsUrl);
    await browserClient.init(false);

    client = await createTab(browserClient);

    // Set standard desktop viewport
    await client.setViewport(1280, 900);

    // ─────────────────────────────────────────────────────────────────
    // STEP 1: LOGIN TO CARD EDITOR
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 1: Editor Authentication ---');
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/owner/grand_hotel/card`, 1500);

    // Capture login screen screenshot
    await client.captureScreenshot('editor_login_screen.png');

    // Authenticate session via /api/auth/login directly in browser session
    const loginRes = await client.evaluate(`
      (async () => {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: 'owner@grandhotel.staging',
            password: 'GrandPass12345!',
            tenant_id: 'grand_hotel',
          }),
        });
        return { status: res.status, body: await res.json().catch(() => ({})) };
      })()
    `);
    console.log('[+] Authenticated session response:', loginRes.status, JSON.stringify(loginRes.body));

    // Reload editor page to pick up authenticated session cookie
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/owner/grand_hotel/card`, 1500);

    const authLoaded = await waitForSelector(client, '.editor-top-bar', 8000);
    console.log('[+] Card Editor authenticated and loaded:', authLoaded);
    if (!authLoaded) {
      const pageText = await client.evaluate('document.body.innerText');
      console.warn('[!] Page text after reload:\n', pageText);
    }

    // Inject helper into editor page
    await client.evaluate(SET_INPUT_SCRIPT);

    // ─────────────────────────────────────────────────────────────────
    // STEP 2: TAB 1 - BRAND PRESENTATION
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 2: Tab 1 - Brand Presentation ---');
    await client.evaluate(`
      setReactInput('#card-tagline', 'Luxury Heritage Suites & Rooftop Dining');
      setReactInput('#card-logo', 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=200&h=200&fit=crop');
      setReactInput('#card-cover', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1200&h=400&fit=crop');
    `);
    await new Promise((r) => setTimeout(r, 400));
    await client.captureScreenshot('editor_tab1_brand.png');

    // ─────────────────────────────────────────────────────────────────
    // STEP 3: TAB 2 - CONTACT & MAPS
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 3: Tab 2 - Contact & Location ---');
    await client.evaluate(`document.querySelectorAll('.editor-tab-btn')[1]?.click();`);
    await waitForSelector(client, '#card-phone', 3000);

    await client.evaluate(`
      setReactInput('#card-phone', '+91 98250 12345');
      setReactInput('#card-website', 'https://grandhotel.staging');
      setReactInput('#card-address', 'Palace Road, Near Heritage Square, Rajkot, Gujarat 360001');
      setReactInput('#card-map', 'https://maps.google.com/?q=22.3039,70.8022');
    `);
    await new Promise((r) => setTimeout(r, 400));
    await client.captureScreenshot('editor_tab2_contact.png');

    // ─────────────────────────────────────────────────────────────────
    // STEP 4: TAB 3 - SOCIAL & CUSTOM LINKS
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 4: Tab 3 - Social & Online Links ---');
    await client.evaluate(`document.querySelectorAll('.editor-tab-btn')[2]?.click();`);
    await waitForSelector(client, '#card-wa', 3000);

    await client.evaluate(`
      setReactInput('#card-wa', '+919825012345');
      setReactInput('#card-insta', 'https://instagram.com/grandhotelrajkot');
      setReactInput('#card-fb', 'https://facebook.com/grandhotelrajkot');
      setReactInput('#card-yt', 'https://youtube.com/@grandhotelrajkot');
      
      setReactInput('.add-link-title', 'Order Room Service (Swiggy)');
      setReactInput('.add-link-url', 'https://swiggy.com/restaurants/grand-hotel');
      document.querySelector('.add-link-btn')?.click();
    `);
    await new Promise((r) => setTimeout(r, 600));
    await client.captureScreenshot('editor_tab3_social.png');

    // ─────────────────────────────────────────────────────────────────
    // STEP 5: SAVE PROFILE
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 5: Save Profile via UI Button ---');
    await client.evaluate(`document.querySelector('.editor-btn.save')?.click();`);
    await new Promise((r) => setTimeout(r, 1200));

    // ─────────────────────────────────────────────────────────────────
    // STEP 6: TAB 4 - PDF MENUS & DOCUMENTS
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 6: Tab 4 - PDF Menus & Documents ---');
    await client.evaluate(`document.querySelectorAll('.editor-tab-btn')[3]?.click();`);
    await waitForSelector(client, '.doc-upload-box', 3000);

    // Upload PDF via authenticated backend endpoint to populate real storage
    const cookies = await client.evaluate(`document.cookie`);
    await fetch(`http://127.0.0.1:${BACKEND_PORT}/api/businesses/grand_hotel/documents`, {
      method: 'POST',
      headers: {
        'Cookie': cookies,
      },
      body: (() => {
        const fd = new FormData();
        const blob = new Blob([Buffer.from(SAMPLE_PDF_BASE64, 'base64')], { type: 'application/pdf' });
        fd.append('file', blob, 'RooftopDinnerMenu.pdf');
        fd.append('document_type', 'food_menu');
        fd.append('display_name', 'Grand Rooftop Dinner Menu (Winter)');
        fd.append('is_published', 'true');
        return fd;
      })(),
    });

    // Refresh document tab view by re-clicking tab
    await client.evaluate(`document.querySelectorAll('.editor-tab-btn')[3]?.click();`);
    await new Promise((r) => setTimeout(r, 1000));
    await client.captureScreenshot('editor_tab4_documents.png');

    // ─────────────────────────────────────────────────────────────────
    // STEP 7: TAB 5 - QR & PUBLICATION
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 7: Tab 5 - QR & Publishing ---');
    await client.evaluate(`document.querySelectorAll('.editor-tab-btn')[4]?.click();`);
    await waitForSelector(client, '.master-publish-btn', 3000);

    // Click "Publish Live to Web"
    await client.evaluate(`
      const pubBtn = document.querySelector('.master-publish-btn');
      if (pubBtn && pubBtn.textContent.includes('Publish')) {
        pubBtn.click();
      }
    `);
    await new Promise((r) => setTimeout(r, 1500));
    await client.captureScreenshot('editor_tab5_publish.png');

    // ─────────────────────────────────────────────────────────────────
    // STEP 8: RENDER LIVE PUBLIC DIGITAL CARD (DESKTOP)
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 8: Render Live Public Digital Card (Desktop) ---');
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/b/grand_hotel/card`, 1500);
    await client.captureScreenshot('public_card_desktop.png');

    // ─────────────────────────────────────────────────────────────────
    // STEP 9: RENDER LIVE PUBLIC DIGITAL CARD (MOBILE)
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 9: Render Live Public Digital Card (Mobile Viewport) ---');
    await client.setViewport(390, 844, true); // iPhone 14 viewport
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/b/grand_hotel/card`, 1500);
    await client.captureScreenshot('public_card_mobile.png');

    // Verify rendered public DOM elements
    const cardAudit = await client.evaluate(`
      (() => {
        return {
          businessName: document.querySelector('.card-business-name')?.textContent || null,
          tagline: document.querySelector('.card-tagline')?.textContent || null,
          hasCallBtn: Boolean(document.querySelector('a[href^="tel:"]')),
          hasWhatsAppBtn: Boolean(document.querySelector('.quick-action-circle.whatsapp')),
          hasDirectionsBtn: Boolean(document.querySelector('.quick-action-circle.maps')),
          hasWebsiteBtn: Boolean(document.querySelector('.quick-action-circle.web')),
          addressText: document.querySelector('.detail-value')?.textContent || null,
          docsCount: document.querySelectorAll('.card-doc-tile').length,
          docName: document.querySelector('.doc-title-text')?.textContent || null,
          hasInstagram: Boolean(document.querySelector('.card-social-btn.instagram')),
          hasFacebook: Boolean(document.querySelector('.card-social-btn.facebook')),
          hasYouTube: Boolean(document.querySelector('.card-social-btn.youtube')),
          customLinksCount: document.querySelectorAll('.card-custom-link-btn').length,
          hasReviewBtn: Boolean(document.querySelector('.card-google-review-btn')),
          hasShareBtn: Boolean(document.querySelector('.card-secondary-share-btn')),
        };
      })()
    `);

    console.log('\n[+] Public Card Render Audit Result:');
    console.log(JSON.stringify(cardAudit, null, 2));

    console.log('\n================================================================');
    console.log('   ALL SCREENSHOTS CAPTURED & AUDIT DATA COLLECTED!             ');
    console.log('================================================================\n');

  } finally {
    if (client) client.close();
    if (browserClient) browserClient.close();
    if (chromeProc) chromeProc.kill('SIGTERM');
    if (frontendProc) frontendProc.kill('SIGTERM');
    if (backendProc) backendProc.kill('SIGTERM');
    try { rmSync(AUDIT_DIR, { recursive: true, force: true }); } catch {}
  }
}

main().catch((err) => {
  console.error('[FATAL] Audit script error:', err);
  process.exit(1);
});
