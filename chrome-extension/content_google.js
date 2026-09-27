// content_google.js — Runs on Google Maps & Google Search review dialogs
console.log('[Nasta Ghar Extension] Attached to Google Reviews page.');

let hasAutoPasted = false;

function findReviewTextarea() {
  // Strategy 1: Look for textarea with placeholder or aria-label matching experience / review
  const allTextareas = Array.from(document.querySelectorAll('textarea'));
  for (const ta of allTextareas) {
    const ph = (ta.getAttribute('placeholder') || '').toLowerCase();
    const aria = (ta.getAttribute('aria-label') || '').toLowerCase();
    if (
      ph.includes('experience') ||
      ph.includes('details') ||
      ph.includes('review') ||
      aria.includes('experience') ||
      aria.includes('review')
    ) {
      return ta;
    }
  }

  // Strategy 2: Largest visible textarea in the dialog
  if (allTextareas.length > 0) {
    return allTextareas[0];
  }

  // Strategy 3: Contenteditable div
  const editables = document.querySelectorAll('div[contenteditable="true"]');
  if (editables.length > 0) {
    return editables[0];
  }

  return null;
}

function findStarButtons() {
  // Star rating radio buttons in Google Review dialog
  const radios = Array.from(
    document.querySelectorAll(
      'div[role="radio"], button[aria-label*="star" i], div[data-rating]'
    )
  );

  // Return top 5 stars
  if (radios.length >= 5) {
    return radios.slice(0, 5);
  }
  return [];
}

function executeAutoPaste() {
  if (hasAutoPasted) return;

  chrome.storage.local.get(['pendingReview'], (result) => {
    const item = result.pendingReview;
    if (!item || !item.reviewText) return;

    // Check if review was sent within the last 10 minutes
    if (Date.now() - (item.timestamp || 0) > 10 * 60 * 1000) return;

    const textarea = findReviewTextarea();
    if (!textarea) return;

    // Avoid double pasting
    if (textarea.value === item.reviewText || textarea.innerText === item.reviewText) {
      hasAutoPasted = true;
      return;
    }

    // 1. Focus the field
    textarea.focus();

    // 2. Set review text
    if (textarea.tagName === 'TEXTAREA') {
      textarea.value = item.reviewText;
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
      textarea.dispatchEvent(new Event('change', { bubbles: true }));
    } else {
      textarea.innerText = item.reviewText;
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // 3. Auto-select star rating if specified
    if (item.rating && Number(item.rating) >= 1 && Number(item.rating) <= 5) {
      const stars = findStarButtons();
      const targetStar = stars[Number(item.rating) - 1];
      if (targetStar) {
        try {
          targetStar.click();
        } catch (e) {
          console.warn('Could not auto-click star:', e);
        }
      }
    }

    hasAutoPasted = true;
    console.log('[Nasta Ghar Extension] Successfully auto-pasted review into Google Review box!');

    // Show a floating confirmation banner on the Google page
    const toast = document.createElement('div');
    toast.textContent = '✨ Nasta Ghar review auto-pasted! Click "Post" to publish.';
    toast.style.cssText =
      'position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#15803d;color:#fff;padding:12px 24px;border-radius:999px;font-family:sans-serif;font-weight:600;font-size:14px;box-shadow:0 10px 30px rgba(0,0,0,0.5);z-index:999999;transition:opacity 0.5s ease;';
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 500);
    }, 4000);

    // Clean up stored pending review
    setTimeout(() => {
      chrome.storage.local.remove(['pendingReview']);
    }, 15000);
  });
}

// Observe DOM changes (dialog opens dynamically)
const observer = new MutationObserver(() => {
  executeAutoPaste();
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
});

// Also poll for 15 seconds
const pollInterval = setInterval(() => {
  executeAutoPaste();
}, 400);

setTimeout(() => {
  clearInterval(pollInterval);
}, 15000);
