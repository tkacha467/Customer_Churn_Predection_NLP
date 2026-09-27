// content_app.js — Runs on the Nasta Ghar web app
console.log('[Nasta Ghar Extension] Attached to review assistant.');

window.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'NASTA_GHAR_REVIEW_SELECTED') {
    const payload = event.data.payload;
    if (payload && payload.reviewText) {
      chrome.storage.local.set({ pendingReview: payload }, () => {
        console.log('[Nasta Ghar Extension] Review saved for auto-pasting:', payload);
      });
    }
  }
});
