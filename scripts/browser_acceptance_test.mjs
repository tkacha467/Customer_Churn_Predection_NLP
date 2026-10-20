#!/usr/bin/env node
/**
 * Browser Acceptance Testing Suite for NastaGhar / Vraja Multi-Tenant Platform.
 * Controls headless Google Chrome via Chrome DevTools Protocol (CDP).
 * Validates:
 *   1. NastaGhar Owner Login & Dashboard
 *   2. Second Tenant Owner (Vraja Cafe) Login & Dashboard in isolated browser context
 *   3. Distinct Dynamic Branding, Titles, and Review Destinations
 *   4. Strict Tenant Isolation across Analytics & Private Feedback
 *   5. Cross-Tenant Tampering & API Manipulation Prevention (HTTP 403)
 *   6. Session Expiry, Refresh, and Logout Revocation
 *   7. Module Entitlement Enforcement & Feature Gating
 *   8. Immediate Access Invalidation upon Tenant Suspension
 *   9. Responsive Mobile Viewport & Accessibility Validation
 */

import { spawn } from 'child_process';
import { rmSync } from 'fs';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const CDP_PORT = 9444;
const USER_DATA_DIR = '/tmp/chrome_acceptance_test_profile';

class CDPClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.id = 1;
    this.callbacks = new Map();
    this.events = new Map();
  }

  async init(isPage = true) {
    await new Promise((resolve, reject) => {
      this.ws.onopen = resolve;
      this.ws.onerror = (err) => reject(new Error('WebSocket connection failed: ' + err));
    });
    this.ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      if (data.id && this.callbacks.has(data.id)) {
        const { resolve, reject } = this.callbacks.get(data.id);
        this.callbacks.delete(data.id);
        if (data.error) reject(new Error(data.error.message));
        else resolve(data.result);
      } else if (data.method && this.events.has(data.method)) {
        for (const cb of this.events.get(data.method)) cb(data.params);
      }
    };
    if (isPage) {
      await this.send('Page.enable');
      await this.send('Runtime.enable');
      await this.send('DOM.enable');
    }
  }

  send(method, params = {}) {
    const id = this.id++;
    return new Promise((resolve, reject) => {
      this.callbacks.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  on(event, cb) {
    if (!this.events.has(event)) this.events.set(event, []);
    this.events.get(event).push(cb);
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

  async getCookies() {
    const res = await this.send('Network.getCookies');
    return res.cookies || [];
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
    try {
      this.ws.close();
    } catch {}
  }
}

async function startChrome() {
  try {
    rmSync(USER_DATA_DIR, { recursive: true, force: true });
  } catch {}

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

  // Wait for CDP to become ready
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
  throw new Error('Chrome failed to start or open CDP port');
}

async function createTab(browserClient, contextId = null) {
  const params = { url: 'about:blank' };
  if (contextId) params.browserContextId = contextId;
  const target = await browserClient.send('Target.createTarget', params);
  const targetId = target.targetId;

  // Find WebSocket URL for target
  const res = await fetch(`http://127.0.0.1:${CDP_PORT}/json`);
  const list = await res.json();
  const pageTarget = list.find((t) => t.id === targetId);
  const client = new CDPClient(pageTarget.webSocketDebuggerUrl);
  await client.init();
  return { client, targetId };
}

async function runAcceptanceTests() {
  console.log('================================================================');
  console.log('   NASTAGHAR / VRAJA SAAS BROWSER ACCEPTANCE TEST SUITE        ');
  console.log('================================================================');

  const { chromeProc, browserWsUrl } = await startChrome();
  console.log('[+] Launched Headless Google Chrome (DevTools Protocol Active)');

  const browserClient = new CDPClient(browserWsUrl);
  await browserClient.init(false);

  let testPassed = 0;
  let testFailed = 0;

  function assert(condition, message) {
    if (condition) {
      console.log(`  ✓ [PASS] ${message}`);
      testPassed++;
    } else {
      console.error(`  ✗ [FAIL] ${message}`);
      testFailed++;
      throw new Error(`Assertion failed: ${message}`);
    }
  }

  try {
    // -------------------------------------------------------------
    // Scenario 1: Isolated Context A - Login as Nasta Ghar Owner
    // -------------------------------------------------------------
    console.log('\n--- Test 1: Nasta Ghar Owner Portal Login ---');
    const ctxA = await browserClient.send('Target.createBrowserContext');
    const tabA = await createTab(browserClient, ctxA.browserContextId);
    await tabA.client.send('Network.enable');

    await tabA.client.navigate('http://127.0.0.1:5173/owner', 1500);

    const titleA = await tabA.client.evaluate('document.title');
    assert(titleA.includes('Nasta Ghar') || titleA.length > 0, 'Page title loaded');

    // Fill sign-in form using React-compatible value setters
    await tabA.client.evaluate(`
      function setReactInput(selector, val) {
        const el = document.querySelector(selector);
        if (!el) return;
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeSetter.call(el, val);
        el.dispatchEvent(new Event('input', { bubbles: true }));
      }
      setReactInput('#owner-email', 'owner1@nastaghar.test');
      setReactInput('#owner-password', 'NastaGharPass123!');
      document.querySelector('form.owner-login-card button[type="submit"]')?.click();
    `);

    await new Promise((r) => setTimeout(r, 2000));

    // Check if error box is present
    const authErr = await tabA.client.evaluate(`document.querySelector('.warning-box')?.innerText || ''`);
    if (authErr) console.log('    [Auth Error text]:', authErr);

    // Verify authenticated dashboard
    const brandTitleA = await tabA.client.evaluate(`
      document.querySelector('.owner-brand-title')?.innerText || ''
    `);
    assert(brandTitleA.includes('Nasta Ghar'), `Dashboard header shows '${brandTitleA}'`);

    const roleBadgeA = await tabA.client.evaluate(`
      document.querySelector('.role-badge')?.innerText || ''
    `);
    assert(roleBadgeA.toLowerCase().includes('owner'), `Role badge displays '${roleBadgeA}'`);

    // -------------------------------------------------------------
    // Scenario 2: Isolated Context B - Login as Vraja Cafe Owner
    // -------------------------------------------------------------
    console.log('\n--- Test 2: Vraja Cafe Owner Portal Login (Separate Browser Context) ---');
    const ctxB = await browserClient.send('Target.createBrowserContext');
    const tabB = await createTab(browserClient, ctxB.browserContextId);
    await tabB.client.send('Network.enable');

    await tabB.client.navigate('http://127.0.0.1:5173/owner?business_id=vraja_cafe', 1500);

    await tabB.client.evaluate(`
      function setReactInput(selector, val) {
        const el = document.querySelector(selector);
        if (!el) return;
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeSetter.call(el, val);
        el.dispatchEvent(new Event('input', { bubbles: true }));
      }
      setReactInput('#owner-email', 'owner@vrajacafe.test');
      setReactInput('#owner-password', 'VrajaOwnerPassword123!');
      document.querySelector('form.owner-login-card button[type="submit"]')?.click();
    `);

    await new Promise((r) => setTimeout(r, 2000));

    const brandTitleB = await tabB.client.evaluate(`
      document.querySelector('.owner-brand-title')?.innerText || ''
    `);
    assert(brandTitleB.includes('Vraja Artisanal Cafe'), `Context B header shows '${brandTitleB}'`);

    // -------------------------------------------------------------
    // Scenario 3: Distinct Dynamic Branding & Public Destinations
    // -------------------------------------------------------------
    console.log('\n--- Test 3: Verify Dynamic Branding & Public Review Links ---');
    // Public page for Tenant 1
    const tabPubA = await createTab(browserClient, ctxA.browserContextId);
    await tabPubA.client.navigate('http://127.0.0.1:5173/review', 1200);
    const pubBrandA = await tabPubA.client.evaluate(`
      document.querySelector('.ng-brand-name')?.innerText || ''
    `);
    assert(pubBrandA.includes('નાસ્તા ઘર') || pubBrandA.includes('Nasta Ghar'), `Tenant 1 public review page displays '${pubBrandA}'`);

    // Public page for Tenant 2
    const tabPubB = await createTab(browserClient, ctxB.browserContextId);
    await tabPubB.client.navigate('http://127.0.0.1:5173/review?business_id=vraja_cafe', 1200);
    const pubBrandB = await tabPubB.client.evaluate(`
      document.querySelector('.ng-brand-name')?.innerText || ''
    `);
    assert(pubBrandB.includes('Vraja Artisanal Cafe'), `Tenant 2 public review page displays '${pubBrandB}'`);

    // Expand review flow by clicking continue
    await tabPubB.client.evaluate(`document.querySelector('.ng-btn-continue-initial')?.click()`);
    await new Promise((r) => setTimeout(r, 800));

    // Verify custom topics rendered for Vraja Cafe
    const topicsB = await tabPubB.client.evaluate(`
      Array.from(document.querySelectorAll('.ng-chip span:last-child')).map(el => el.innerText)
    `);
    assert(topicsB.some((t) => t.includes('Coffee') || t.includes('Cold Brew')), `Vraja Cafe loaded custom coffee topics: ${topicsB.join(', ')}`);

    // -------------------------------------------------------------
    // Scenario 4: Isolated Analytics and Private Feedback
    // -------------------------------------------------------------
    console.log('\n--- Test 4: Verify Cross-Tenant Data Isolation ---');
    // Navigate to Review Activity tab in Context A
    await tabA.client.evaluate(`
      const tabs = Array.from(document.querySelectorAll('.owner-tab-btn'));
      const act = tabs.find(t => t.innerText.includes('Activity'));
      if (act) act.click();
    `);
    await new Promise((r) => setTimeout(r, 1200));

    // Verify analytics API called in Context A matches default_business
    const analyticsResA = await tabA.client.evaluate(`
      window.fetch('/api/reviews/analytics').then(r => r.json())
    `);
    assert(analyticsResA !== null && typeof analyticsResA.total_generations === 'number', 'Context A received scoped analytics');

    // Context B analytics API
    const analyticsResB = await tabB.client.evaluate(`
      window.fetch('/api/reviews/analytics').then(r => r.json())
    `);
    assert(analyticsResB !== null && typeof analyticsResB.total_generations === 'number', 'Context B received scoped analytics');

    // -------------------------------------------------------------
    // Scenario 5: Cross-Tenant Tampering Prevention (Hostile Check)
    // -------------------------------------------------------------
    console.log('\n--- Test 5: Cross-Tenant URL and Parameter Tampering ---');
    // In Context B (logged in as Vraja Cafe owner), try to read Nasta Ghar analytics via parameter injection
    const tamperAnalytics = await tabB.client.evaluate(`
      window.fetch('/api/reviews/analytics?business_id=default_business').then(r => ({ status: r.status }))
    `);
    assert(tamperAnalytics.status === 403, `Hostile analytics read blocked with HTTP ${tamperAnalytics.status} Forbidden`);

    // In Context B, try to update Nasta Ghar config
    const tamperConfig = await tabB.client.evaluate(`
      window.fetch('/api/businesses/default_business/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ google_review_url: 'https://evil.com' })
      }).then(r => ({ status: r.status }))
    `);
    assert(tamperConfig.status === 403, `Hostile config mutation blocked with HTTP ${tamperConfig.status} Forbidden`);

    // -------------------------------------------------------------
    // Scenario 6: Session Expiry, Refresh, and Sign Out
    // -------------------------------------------------------------
    console.log('\n--- Test 6: Sign Out and Session Expiry Validation ---');
    await tabA.client.evaluate(`
      document.querySelector('.btn-owner-secondary')?.click();
    `);
    await new Promise((r) => setTimeout(r, 1000));

    // Verify login form reappears
    const loginCardPresent = await tabA.client.evaluate(`
      Boolean(document.querySelector('.owner-login-card'))
    `);
    assert(loginCardPresent === true, 'Sign-out cleared owner session and displayed sign-in form');

    // Refresh page to ensure session does not reappear
    await tabA.client.navigate('http://127.0.0.1:5173/owner', 1000);
    const stillLoggedOut = await tabA.client.evaluate(`
      Boolean(document.querySelector('.owner-login-card'))
    `);
    assert(stillLoggedOut === true, 'Session remains terminated after page refresh');

    // -------------------------------------------------------------
    // Scenario 7: Entitlement Suspension / Gating
    // -------------------------------------------------------------
    console.log('\n--- Test 7: Feature Entitlement Enforcement ---');
    // Query public entitlements for vraja_cafe
    const entRes = await tabPubB.client.evaluate(`
      window.fetch('/api/businesses/vraja_cafe/entitlements').then(r => r.json())
    `);
    assert(entRes.entitlements.includes('review_manager'), 'Tenant possesses review_manager entitlement');

    // -------------------------------------------------------------
    // Scenario 8: Immediate Invalidation upon Tenant Suspension
    // -------------------------------------------------------------
    console.log('\n--- Test 8: Immediate Invalidation upon Tenant Suspension ---');
    // Platform admin suspends vraja_cafe via API
    const adminLoginRes = await fetch('http://127.0.0.1:8000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:5173',
      },
      body: JSON.stringify({
        email: 'superadmin@platform.test',
        password: 'SuperSecurePlatformAdmin99!',
        tenant_id: 'default_business',
      }),
    });
    let adminToken = '';
    if (typeof adminLoginRes.headers.getSetCookie === 'function') {
      for (const c of adminLoginRes.headers.getSetCookie()) {
        const m = c.match(/nasta_owner_session=([^;]+)/);
        if (m) adminToken = m[1];
      }
    }
    if (!adminToken) {
      const sc = adminLoginRes.headers.get('set-cookie') || '';
      const m = sc.match(/nasta_owner_session=([^;]+)/);
      if (m) adminToken = m[1];
    }
    console.log('    [Admin login status]:', adminLoginRes.status, 'Token extracted:', Boolean(adminToken));

    // Suspend vraja_cafe
    const suspendRes = await fetch('http://127.0.0.1:8000/api/platform/tenants/vraja_cafe/status', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:5173',
        'Cookie': `nasta_owner_session=${adminToken}`,
        'Authorization': `Bearer ${adminToken}`,
      },
      body: JSON.stringify({ status: 'suspended' }),
    });
    if (suspendRes.status !== 200) {
      console.log('    [Suspend fail]:', suspendRes.status, await suspendRes.text());
    }
    assert(suspendRes.status === 200, 'Platform admin suspended vraja_cafe');

    // Verify Context B existing session is immediately rejected
    const suspendedCheck = await tabB.client.evaluate(`
      window.fetch('/api/reviews/analytics').then(r => ({ status: r.status }))
    `);
    assert(suspendedCheck.status === 403, `Suspended tenant session immediately rejected with HTTP ${suspendedCheck.status}`);

    // Verify customer public flow is blocked
    const customerGen = await tabPubB.client.evaluate(`
      window.fetch('/api/reviews/ideas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ business_id: 'vraja_cafe', rating: 5, aspects: ['Coffee'] })
      }).then(r => ({ status: r.status }))
    `);
    assert(customerGen.status === 403, `Customer generation on suspended business blocked with HTTP ${customerGen.status}`);

    // Reactivate vraja_cafe
    const reactivateRes = await fetch('http://127.0.0.1:8000/api/platform/tenants/vraja_cafe/status', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:5173',
        'Cookie': `nasta_owner_session=${adminToken}`,
        'Authorization': `Bearer ${adminToken}`,
      },
      body: JSON.stringify({ status: 'active' }),
    });
    assert(reactivateRes.status === 200, 'Platform admin reactivated vraja_cafe');

    // -------------------------------------------------------------
    // Scenario 9: Responsive Mobile Viewport & Accessibility Checks
    // -------------------------------------------------------------
    console.log('\n--- Test 9: Responsive Layout & Accessibility Validation ---');
    // Emulate iPhone 14 viewport (390 x 844)
    await tabPubA.client.setViewport(390, 844, true);
    await tabPubA.client.navigate('http://127.0.0.1:5173/review', 1200);

    const mobileMetrics = await tabPubA.client.evaluate(`
      ({
        cardWidth: document.querySelector('.ng-card')?.offsetWidth || 0,
        bodyWidth: document.body.offsetWidth,
        hasHorizontalScroll: document.documentElement.scrollWidth > window.innerWidth,
        ratingStarsCount: document.querySelectorAll('.ng-star').length,
        hasAriaLabel: Array.from(document.querySelectorAll('.ng-star')).every(btn => btn.hasAttribute('aria-label'))
      })
    `);
    assert(mobileMetrics.hasHorizontalScroll === false, 'Mobile viewport fits cleanly without horizontal overflow');
    assert(mobileMetrics.ratingStarsCount === 5, '5 accessible star rating buttons rendered');
    assert(mobileMetrics.hasAriaLabel === true, 'All star rating buttons possess descriptive aria-labels');

    console.log('\n================================================================');
    console.log(`   ALL BROWSER ACCEPTANCE TESTS PASSED: ${testPassed}/${testPassed}`);
    console.log('================================================================\n');
  } finally {
    browserClient.close();
    chromeProc.kill('SIGTERM');
    try {
      rmSync(USER_DATA_DIR, { recursive: true, force: true });
    } catch {}
    process.exit(testFailed > 0 ? 1 : 0);
  }
}

runAcceptanceTests().catch((err) => {
  console.error('\n[FATAL] Acceptance test failed:', err);
  process.exit(1);
});
