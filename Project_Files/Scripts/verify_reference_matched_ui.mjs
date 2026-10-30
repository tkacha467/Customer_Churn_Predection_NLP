#!/usr/bin/env -S node --experimental-websocket
/**
 * Vraja AI Digital Card — Reference-Matched UI E2E Verification & Screenshot Capture
 * Spins up an isolated backend & frontend stack, logs in as tenant owner,
 * configures all new reference-matched fields, uploads assets, publishes,
 * and captures high-resolution evidence screenshots at mobile and desktop viewports.
 */

import { spawn, execSync } from 'child_process';
import net from 'node:net';
import { rmSync, mkdirSync, writeFileSync, existsSync } from 'fs';
import { resolve, dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = resolve(__dirname, '../..');
const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const BACKEND_PORT = 8012;
const FRONTEND_PORT = 5176;
const CDP_PORT = 9448;
const AUDIT_DIR = `/tmp/vraja_vcard_audit_${Date.now()}`;
const AUDIT_DB = `${AUDIT_DIR}/reviews.sqlite3`;
const AUDIT_DOCS = `${AUDIT_DIR}/documents`;
const USER_DATA_DIR = `${AUDIT_DIR}/chrome_user_data`;
const ARTIFACT_DIR = '/Users/tushi/.gemini/antigravity/brain/67134c41-8090-4984-94c4-a6b843aef526';

const SAMPLE_PNG_BASE64 = 
  'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAABHNCSVQICAgIfAhkiAAAAAlwSFlz' +
  'AAAOxAAADsQBlSsOGwAAAE5JREFUeJztwTEBAAAAwqD1T20LL6AAAAAAAAAAAAAA' +
  'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAODHAFeIAAE6lYj6AAAA' +
  'AElFTkSuQmCC';

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

async function main() {
  console.log('================================================================');
  console.log('   VRAJA AI DIGITAL CARD — REFERENCE-MATCHED UI AUDIT          ');
  console.log('================================================================\n');

  mkdirSync(AUDIT_DIR, { recursive: true });
  mkdirSync(AUDIT_DOCS, { recursive: true });
  mkdirSync(USER_DATA_DIR, { recursive: true });

  // 1. Initialize isolated database and seed tenant
  console.log('[*] Setting up isolated SQLite test database...');
  const pythonBin = existsSync(join(ROOT_DIR, '.venv/bin/python3'))
    ? join(ROOT_DIR, '.venv/bin/python3')
    : 'python3';

  execSync(
    `REVIEW_DB_PATH="${AUDIT_DB}" "${pythonBin}" -c "
import time
from Backend.app.core.database.storage import ReviewStore
from Backend.app.core.auth.auth import hash_password

store = ReviewStore(database_path='${AUDIT_DB}')
store.upsert_tenant({
    'id': 'grand_hotel',
    'business_name': 'Grand Hotel & Suites',
    'category': 'Hospitality & Luxury Suites',
    'description': 'Premier heritage dining and suites in Rajkot.',
    'status': 'active',
    'review_url': 'https://search.google.com/local/writereview?placeid=ChIJGrandHotelRajkot',
    'primary_accent': '#0f281e',
    'entitlements': ['digital_card', 'review_manager']
})

user = store.create_user(
    email='owner@grandhotel.test',
    password_hash=hash_password('GrandOwnerSecure2026!'),
    display_name='Hotel Managing Director',
    is_active=1
)
store.add_membership(user['id'], 'grand_hotel', role='owner')
print('[+] Seeded tenant grand_hotel and owner credentials.')
"`,
    { stdio: 'inherit' }
  );

  // 2. Start Backend on isolated port
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
  console.log(`[+] Backend ready on http://127.0.0.1:${BACKEND_PORT}`);

  // 3. Start Frontend on isolated port
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
  console.log(`[+] Frontend ready on http://127.0.0.1:${FRONTEND_PORT}`);

  // 4. Launch Headless Chrome
  console.log(`[*] Launching headless Google Chrome on CDP port ${CDP_PORT}...`);
  const chromeProc = spawn(
    CHROME_PATH,
    [
      `--remote-debugging-port=${CDP_PORT}`,
      `--user-data-dir=${USER_DATA_DIR}`,
      '--headless=new',
      '--disable-gpu',
      '--no-first-run',
      '--no-default-browser-check',
      'about:blank',
    ],
    { stdio: ['ignore', 'pipe', 'pipe'] }
  );

  await waitForTcp(CDP_PORT);
  console.log(`[+] Headless Chrome CDP ready on port ${CDP_PORT}`);

  const verRes = await fetch(`http://127.0.0.1:${CDP_PORT}/json/version`);
  const verData = await verRes.json();
  const browserClient = new CDPClient(verData.webSocketDebuggerUrl);
  await browserClient.init(false);

  const { targetId } = await browserClient.send('Target.createTarget', { url: 'about:blank' });
  const targets = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json`)).json();
  const pageTarget = targets.find((t) => t.id === targetId);

  const client = new CDPClient(pageTarget.webSocketDebuggerUrl);
  await client.init(true);
  console.log('[+] CDP session initialized.');

  try {
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
            email: 'owner@grandhotel.test',
            password: 'GrandOwnerSecure2026!',
            tenant_id: 'grand_hotel',
          }),
        });
        return { status: res.status, body: await res.json().catch(() => ({})) };
      })()
    `);
    console.log('[+] Authenticated session response:', loginRes.status, JSON.stringify(loginRes.body));

    // Reload editor page to pick up authenticated session cookie
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/owner/grand_hotel/card`, 1500);
    await waitForSelector(client, '.editor-nav-tabs', 6000);
    console.log('[+] Owner authenticated successfully.');

    // ─────────────────────────────────────────────────────────────────
    // STEP 2: TAB 1 - BRAND PRESENTATION (NEW FIELDS & IMAGE UPLOAD)
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 2: Tab 1 - Brand Presentation Configuration ---');
    await client.evaluate(`
      window.setReactInput = (selector, value) => {
        const el = document.querySelector(selector);
        if (!el) return;
        const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
        if (setter) setter.call(el, value);
        else el.value = value;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      };
      setReactInput('#card-display-name', 'Pramukh Heritage Restaurant');
      setReactInput('#card-category', 'GUJARATI & RAJASTHANI RESTAURANT');
      setReactInput('#card-tagline', 'Authentic Homestyle Kathiyawadi & Royal Thali');
      setReactInput('#card-welcome', 'Thanks for visiting Pramukh Heritage Restaurant! Connect with us, share your experience, and stay updated.');
    `);

    // Direct Image Upload via Backend for Logo in browser session
    const logoJson = await client.evaluate(`
      (async () => {
        const samplePng = '${SAMPLE_PNG_BASE64}';
        const bin = atob(samplePng);
        const bytes = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
        const fd = new FormData();
        fd.append('file', new Blob([bytes], { type: 'image/png' }), 'restaurant_logo.png');
        fd.append('image_type', 'logo');
        const res = await fetch('/api/businesses/grand_hotel/images', {
          method: 'POST',
          body: fd,
        });
        const body = await res.json().catch(() => ({}));
        return { status: res.status, body };
      })()
    `);
    console.log(`[+] Uploaded tenant logo image response:`, JSON.stringify(logoJson));

    // Update input in UI
    await client.evaluate(`
      setReactInput('#card-logo', '${logoJson?.body?.image_url || ''}');
    `);
    await new Promise((r) => setTimeout(r, 600));
    await client.captureScreenshot('editor_tab1_brand.png');

    // ─────────────────────────────────────────────────────────────────
    // STEP 3: TAB 2 - CONTACT & LOCATION (EMAIL, HOURS, ADDRESS, PHONE)
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 3: Tab 2 - Contact & Location Configuration ---');
    await client.evaluate(`document.querySelectorAll('.editor-tab-btn')[1]?.click();`);
    await waitForSelector(client, '#card-phone', 3000);

    await client.evaluate(`
      setReactInput('#card-phone', '+91 98250 12345');
      setReactInput('#card-email', 'namaste@pramukhheritage.in');
      setReactInput('#card-website', 'https://pramukhheritage.in');
      setReactInput('#card-hours', 'Mon - Sun: 10:00 AM - 10:00 PM');
      setReactInput('#card-address', 'Pramukh Heritage Complex, Palace Road, Near Royal Square, Rajkot, Gujarat 360001, India');
      setReactInput('#card-map', 'https://maps.google.com/?q=22.3039,70.8022');
    `);
    await new Promise((r) => setTimeout(r, 600));
    await client.captureScreenshot('editor_tab2_contact.png');

    // ─────────────────────────────────────────────────────────────────
    // STEP 4: TAB 3 - SOCIAL MEDIA & DIRECT CHAT (WHATSAPP GROUP, SOCIALS)
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 4: Tab 3 - Social Media & Online Links ---');
    await client.evaluate(`document.querySelectorAll('.editor-tab-btn')[2]?.click();`);
    await waitForSelector(client, '#card-wa', 3000);

    await client.evaluate(`
      setReactInput('#card-wa', '+919825012345');
      setReactInput('#card-wa-group', 'https://chat.whatsapp.com/PramukhFoodLovers');
      setReactInput('#card-insta', 'https://instagram.com/pramukh_restaurant');
      setReactInput('#card-fb', 'https://facebook.com/pramukhrestaurant');
      setReactInput('#card-yt', 'https://youtube.com/@pramukhrestaurant');
    `);
    await new Promise((r) => setTimeout(r, 600));
    await client.captureScreenshot('editor_tab3_social.png');

    // ─────────────────────────────────────────────────────────────────
    // STEP 5: SAVE PROFILE CHANGES
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 5: Save Profile Changes via UI Button ---');
    await client.evaluate(`document.querySelector('.editor-btn.save')?.click();`);
    await new Promise((r) => setTimeout(r, 1200));

    // ─────────────────────────────────────────────────────────────────
    // STEP 6: TAB 4 - PDF MENU UPLOAD
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 6: Tab 4 - Upload Authentic Menu PDF ---');
    await client.evaluate(`document.querySelectorAll('.editor-tab-btn')[3]?.click();`);
    await waitForSelector(client, '.doc-upload-box', 3000);

    const docJson = await client.evaluate(`
      (async () => {
        const samplePdf = '${SAMPLE_PDF_BASE64}';
        const bin = atob(samplePdf);
        const bytes = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
        const fd = new FormData();
        fd.append('file', new Blob([bytes], { type: 'application/pdf' }), 'Pramukh_Kathiyawadi_Menu.pdf');
        fd.append('document_type', 'food_menu');
        fd.append('display_name', 'Kathiyawadi Thali & Farsan Menu');
        fd.append('is_published', 'true');
        const res = await fetch('/api/businesses/grand_hotel/documents', {
          method: 'POST',
          body: fd,
        });
        return await res.json();
      })()
    `);
    console.log(`[+] Uploaded tenant document: ${docJson?.display_name}`);

    await client.evaluate(`document.querySelectorAll('.editor-tab-btn')[3]?.click();`);
    await new Promise((r) => setTimeout(r, 1000));
    await client.captureScreenshot('editor_tab4_documents.png');

    // ─────────────────────────────────────────────────────────────────
    // STEP 7: TAB 5 - QR COLOR CUSTOMIZATION & PUBLICATION
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 7: Tab 5 - QR Customization & Publish Live ---');
    await client.evaluate(`document.querySelectorAll('.editor-tab-btn')[4]?.click();`);
    await waitForSelector(client, '.master-publish-btn', 3000);

    // Click Forest Green Swatch
    await client.evaluate(`
      const swatch = document.querySelectorAll('.qr-swatch-btn')[0];
      if (swatch) swatch.click();
    `);
    await new Promise((r) => setTimeout(r, 400));

    // Click "Publish Live to Web"
    const pubStatus = await client.evaluate(`
      (() => {
        const pubBtn = document.querySelector('.master-publish-btn');
        const text = pubBtn ? pubBtn.textContent : 'none';
        if (pubBtn && text.includes('Publish')) {
          pubBtn.click();
        }
        return text;
      })()
    `);
    console.log('[+] pubBtn status before click:', pubStatus);
    await new Promise((r) => setTimeout(r, 2000));
    await client.captureScreenshot('editor_tab5_publish.png');

    const checkCard = await client.evaluate(`
      (async () => {
        const res = await fetch('/api/businesses/grand_hotel/card');
        return { status: res.status, body: await res.json().catch(() => ({})) };
      })()
    `);
    console.log('[DEBUG] GET /api/businesses/grand_hotel/card in browser:', JSON.stringify(checkCard));

    // ─────────────────────────────────────────────────────────────────
    // STEP 8: RENDER REFERENCE-MATCHED PUBLIC CARD (DESKTOP)
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 8: Render Reference-Matched Public Card (Desktop) ---');
    await client.setViewport(1280, 850);
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/b/grand_hotel/card`, 1500);
    const bodyHtml = await client.evaluate(`document.body.innerHTML`);
    console.log('[DEBUG] Page body at /b/grand_hotel/card:', bodyHtml.slice(0, 500));
    await waitForSelector(client, '.vcard-business-name', 8000);
    await client.captureScreenshot('public_card_desktop.png');

    // ─────────────────────────────────────────────────────────────────
    // STEP 9: RENDER REFERENCE-MATCHED PUBLIC CARD (MOBILE VIEWPORT)
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 9: Render Reference-Matched Public Card (Mobile Viewport: 390x844) ---');
    await client.setViewport(390, 844, true); // iPhone 14 viewport
    await client.navigate(`http://127.0.0.1:${FRONTEND_PORT}/b/grand_hotel/card`, 1500);
    await waitForSelector(client, '.vcard-business-name', 8000);
    await client.captureScreenshot('public_card_mobile.png');

    // ─────────────────────────────────────────────────────────────────
    // STEP 10: VERIFY DOM STRUCTURE & ACTION DESTINATIONS
    // ─────────────────────────────────────────────────────────────────
    console.log('\n--- Step 10: Inspect Live Rendered Action Hierarchy ---');
    const auditResult = await client.evaluate(`
      (() => {
        const actionLabels = Array.from(document.querySelectorAll('.vcard-tile-label')).map(el => el.textContent.trim());
        const dockLabels = Array.from(document.querySelectorAll('.vcard-dock-label')).map(el => el.textContent.trim());
        return {
          businessName: document.querySelector('.vcard-business-name')?.textContent || null,
          categoryTag: document.querySelector('.vcard-category-tag')?.textContent || null,
          addressText: document.querySelector('.vcard-address-text')?.textContent || null,
          welcomeMessage: document.querySelector('.vcard-welcome-message')?.textContent || null,
          hoursPill: document.querySelector('.vcard-hours-text')?.textContent || null,
          actionGridItems: actionLabels,
          dockActionItems: dockLabels,
          hasCallHref: Boolean(document.querySelector('a[href="tel:+91 98250 12345"]')),
          hasEmailHref: Boolean(document.querySelector('a[href="mailto:namaste@pramukhheritage.in"]')),
          hasWebsiteHref: Boolean(document.querySelector('a[href="https://pramukhheritage.in"]')),
          hasWaGroupHref: Boolean(document.querySelector('a[href="https://chat.whatsapp.com/PramukhFoodLovers"]')),
          hasMapHref: Boolean(document.querySelector('a[href="https://maps.google.com/?q=22.3039,70.8022"]')),
          hasMenuButton: actionLabels.includes('MENU'),
          hasSaveContactButton: actionLabels.includes('Save Contact'),
          poweredByBranding: document.querySelector('.vcard-dock-footer')?.textContent || null,
        };
      })()
    `);

    console.log('\n[+] Reference-Matched Live UI Inspection Result:');
    console.log(JSON.stringify(auditResult, null, 2));

    // Verify assertions
    if (auditResult.businessName !== 'Pramukh Heritage Restaurant') {
      throw new Error(`Expected businessName to be 'Pramukh Heritage Restaurant', got: ${auditResult.businessName}`);
    }
    if (!auditResult.hasSaveContactButton) throw new Error('Save Contact button missing');
    if (!auditResult.hasMenuButton) throw new Error('MENU action button missing');
    if (!auditResult.hasEmailHref) throw new Error('Email dock item missing');
    if (!auditResult.hasCallHref) throw new Error('Call dock item missing');

    console.log('\n================================================================');
    console.log('   ALL CHECKS PASSED & SCREENSHOTS SUCCESSFULLY EMBEDDED!       ');
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
  console.error('[FATAL] Verification error:', err);
  process.exit(1);
});
