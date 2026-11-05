import { useState, useEffect, useRef } from 'react';
import RestaurantWorld from './RestaurantWorld';
import { apiFetch } from '../lib/api';

// ─── NASTA GHAR BRAND CONSTANTS ──────────────────────────────────────────────
const BRAND = {
  name: 'Nasta Ghar',
  googleMapUrl:
    'https://search.google.com/local/writereview?placeid=ChIJZeK7NwDLWTkR1pOxt51jLro',
};

const DEFAULT_TOPICS = [
  { label: 'Breakfast', icon: '🍳' },
  { label: 'Chai & Tea', icon: '☕' },
  { label: 'Snacks', icon: '🥪' },
  { label: 'Taste & Flavour', icon: '😋' },
  { label: 'Friendly Staff', icon: '😊' },
  { label: 'Cleanliness', icon: '✨' },
  { label: 'Value for Money', icon: '💰' },
  { label: 'Quick Service', icon: '⚡' },
];

export const detectBrowserLanguage = () => {
  try {
    const browserLangs = Array.isArray(navigator?.languages) && navigator.languages.length > 0
      ? navigator.languages
      : [navigator?.language || ''];
    for (const lang of browserLangs) {
      if (!lang) continue;
      const l = String(lang).toLowerCase().trim();
      if (l.startsWith('gu')) return 'gujarati';
      if (l.startsWith('hi')) return 'hindi';
      if (l.startsWith('en')) return 'english';
    }
  } catch {
    // Restricted environment fallback
  }
  return 'english';
};

const getLanguageLabel = (l) => {
  if (l === 'hindi') return 'Hindi';
  if (l === 'gujarati') return 'Gujarati';
  return 'English';
};

// ─── COMPREHENSIVE UI LOCALIZATION DICTIONARY ─────────────────────────────────
export const UI_STRINGS = {
  english: {
    howWasVisit: 'How was your visit?',
    tapStar: 'Tap a star to rate your experience',
    continueBtn: 'Continue →',
    ratings: {
      5: { text: 'Loved it!', emoji: '🤩' },
      4: { text: 'Really good', emoji: '😊' },
      3: { text: 'It was okay', emoji: '🙂' },
      2: { text: 'Disappointed', emoji: '😕' },
      1: { text: 'Not good', emoji: '😞' },
    },
    whatStoodOut: 'What stood out?',
    pickMatched: 'Pick anything that matched your visit',
    nothingSpecific: 'Nothing specific',
    personalNote: 'Personal note',
    optional: 'optional',
    notePlaceholder: 'e.g. The poha was absolutely perfect! 😋',
    reviewIdeas: 'Review ideas',
    tapFavourite: 'Tap your favourite to copy & open Google Review',
    refiningIdeas: 'Refining ideas...',
    useThisReview: 'Use this review →',
    writeOwn: '✍️ Write my own review',
    writeTitle: 'Write your review',
    chars: 'chars',
    writeSub: "Edit anything before posting — it's your words!",
    makeNatural: '✨ Make it more natural',
    refiningNatural: '✨ Refining...',
    backToIdeas: '← Back to review ideas',
    googleNotice: "Your words, your review. Paste the copy into Google and post it yourself.",
    copyAndOpenGoogle: 'Copy & open Google Review',
    privatePromptGood: 'Want to tell us privately? ',
    privatePromptBad: 'Want to tell the team what could have been better? ',
    sendPrivateNote: 'Send private note',
    directNoteTo: 'Direct note to',
    sharePrivately: "Share anything you'd like our team to know privately.",
    feedbackPlaceholder: 'Share your thoughts, suggestions, or anything else...',
    contactPlaceholder: 'Your name or contact (optional)',
    sendToTeam: 'Send to Team',
    sending: 'Sending...',
    cancel: 'Cancel',
    close: 'Close',
    thankYou: 'Thank you!',
    feedbackSentMsg: 'Your message has been sent directly to the team.',
    errorRefresh: 'Could not refresh live suggestions. You can retry or write your own review.',
    retry: '🔄 Retry',
    retrying: 'Retrying...',
    cookieMsg: 'Your review is copied when you choose it. Paste it into Google and submit it yourself.',
    gotIt: 'Got it ✓',
  },
  hindi: {
    howWasVisit: 'Aapka anubhav kaisa raha?',
    tapStar: 'Apne anubhav ke anusaar star chunein',
    continueBtn: 'Aage badhein →',
    ratings: {
      5: { text: 'Bahut pasand aaya!', emoji: '🤩' },
      4: { text: 'Kaafi accha laga', emoji: '😊' },
      3: { text: 'Thik-thak raha', emoji: '🙂' },
      2: { text: 'Khaas nahi tha', emoji: '😕' },
      1: { text: 'Accha nahi laga', emoji: '😞' },
    },
    whatStoodOut: 'Kya sabse accha laga?',
    pickMatched: 'Jo aapki visit me accha raha use chunein',
    nothingSpecific: 'Kuch khaas nahi',
    personalNote: 'Personal note',
    optional: 'optional',
    notePlaceholder: 'Jaise ki poha bahut tasty tha! 😋',
    reviewIdeas: 'Review suggestions',
    tapFavourite: 'Pasandida review chunein aur Google Review kholein',
    refiningIdeas: 'Ideas taiyar ho rahe hain...',
    useThisReview: 'Yeh review use karein →',
    writeOwn: '✍️ Apna khud ka review likhein',
    writeTitle: 'Apna review likhein',
    chars: 'chars',
    writeSub: 'Post karne se pehle kuch bhi badal sakte hain!',
    makeNatural: '✨ Aur natural banayein',
    refiningNatural: '✨ Refining...',
    backToIdeas: '← Wapas suggestions par jayein',
    googleNotice: 'Aapka review, aapke shabd. Google par paste karke post karein.',
    copyAndOpenGoogle: 'Copy karke Google Review kholein',
    privatePromptGood: 'Kya hume privately kuch batana chahte hain? ',
    privatePromptBad: 'Kya team ko batana chahte hain kya behtar ho sakta tha? ',
    sendPrivateNote: 'Private note bhejein',
    directNoteTo: 'Direct note to',
    sharePrivately: 'Aap humari team se privately kuch bhi share kar sakte hain.',
    feedbackPlaceholder: 'Apne vichar, sujhav ya shikayat yahan likhein...',
    contactPlaceholder: 'Aapka naam ya contact (optional)',
    sendToTeam: 'Team ko bhejein',
    sending: 'Bheja ja raha hai...',
    cancel: 'Cancel',
    close: 'Band karein',
    thankYou: 'Dhanyawad!',
    feedbackSentMsg: 'Aapka message sidhe team ko pahunch gaya hai.',
    errorRefresh: 'Live suggestions load nahi ho sake. Dobara koshish karein ya apna review likhein.',
    retry: '🔄 Dobara koshish karein',
    retrying: 'Koshish jaari hai...',
    cookieMsg: 'Review select karne par clipboard par copy ho jayega. Google par paste karke submit karein.',
    gotIt: 'Samajh gaya ✓',
  },
  gujarati: {
    howWasVisit: 'Tamaro anubhav kevo rahyo?',
    tapStar: 'Tamara anubhav mujab star pasand karo',
    continueBtn: 'Aagal vadho →',
    ratings: {
      5: { text: 'Khub j saras!', emoji: '🤩' },
      4: { text: 'Gamyu', emoji: '😊' },
      3: { text: 'Thik hatu', emoji: '🙂' },
      2: { text: 'Khas na hatu', emoji: '😕' },
      1: { text: 'Saras na hatu', emoji: '😞' },
    },
    whatStoodOut: 'Shu sabthi vadhu gamyu?',
    pickMatched: 'Tamara anubhav mujab pasand karo',
    nothingSpecific: 'Khas kai nahi',
    personalNote: 'Personal note',
    optional: 'optional',
    notePlaceholder: 'Jem ke poha khub tasty hata! 😋',
    reviewIdeas: 'Review suggestions',
    tapFavourite: 'Tamaro pasandida review tap karo ane Google Review kholo',
    refiningIdeas: 'Ideas taiyar thai rahya chhe...',
    useThisReview: 'Aa review vapro →',
    writeOwn: '✍️ Tamaro potano review lakho',
    writeTitle: 'Tamaro review lakho',
    chars: 'chars',
    writeSub: 'Post karta pahela tame kai pan badli shako chho!',
    makeNatural: '✨ Vadhu natural banavo',
    refiningNatural: '✨ Refining...',
    backToIdeas: '← Pacha suggestions par jao',
    googleNotice: 'Tamaro review, tamara shabdo. Google par paste kari post karo.',
    copyAndOpenGoogle: 'Copy kari Google Review kholo',
    privatePromptGood: 'Shu amne privately kai janavva mango chho? ',
    privatePromptBad: 'Shu team ne janavva mango chho ke shu sudhari shakay? ',
    sendPrivateNote: 'Private note moklo',
    directNoteTo: 'Direct note to',
    sharePrivately: 'Tame amari team sathe privately kai pan share kari shako chho.',
    feedbackPlaceholder: 'Tamara vichar ke suchan ahiya lakho...',
    contactPlaceholder: 'Tamaru naam ke contact (optional)',
    sendToTeam: 'Team ne moklo',
    sending: 'Moklay rahyu chhe...',
    cancel: 'Cancel',
    close: 'Band karo',
    thankYou: 'Aabhar!',
    feedbackSentMsg: 'Tamaro sandesho sidho team sudhi pahonchi gayo chhe.',
    errorRefresh: 'Live suggestions load na thai shakya. Fari prayas karo athva potano review lakho.',
    retry: '🔄 Fari prayas karo',
    retrying: 'Prayas chalu chhe...',
    cookieMsg: 'Review pasand karta j clipboard par copy thai jashe. Google par paste kari submit karo.',
    gotIt: 'Samji gaya ✓',
  },
};

// ─── DRAFT RECOVERY UTILITIES (Session & Tenant Isolated) ────────────────────
const DRAFT_MAX_AGE_MS = 2 * 60 * 60 * 1000; // 2 hours

const getDraftStorageKey = (bId) => `nastaGhar_draft_${bId || 'default'}`;

const loadDraft = (bId) => {
  try {
    const raw = sessionStorage.getItem(getDraftStorageKey(bId));
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return null;
    if (parsed.savedAt && Date.now() - parsed.savedAt > DRAFT_MAX_AGE_MS) {
      sessionStorage.removeItem(getDraftStorageKey(bId));
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
};

const saveDraft = (bId, updates) => {
  try {
    const current = loadDraft(bId) || {};
    const merged = { ...current, ...updates, savedAt: Date.now() };
    sessionStorage.setItem(getDraftStorageKey(bId), JSON.stringify(merged));
  } catch {}
};

const clearSessionDraft = (bId) => {
  try {
    sessionStorage.removeItem(getDraftStorageKey(bId));
    sessionStorage.removeItem('nastaGharSelectedReview');
    sessionStorage.removeItem('nastaGharSelectedReviewId');
    sessionStorage.removeItem('nastaGharDraftReview');
    sessionStorage.removeItem('nastaGharSelectedRating');
    sessionStorage.removeItem('nastaGharSelectedTopics');
    sessionStorage.removeItem('nastaGharNothingSpecific');
    sessionStorage.removeItem('nastaGharPersonalNote');
    sessionStorage.removeItem('nastaGharReviewStarted');
    sessionStorage.removeItem('nastaGharClipboardCopied');
  } catch {}
};

// ─── STRICT GROUNDED FALLBACK SUGGESTIONS ───────────────────────────────────
const getFallbackIdeas = (r, note = '', lang = 'english', bizName = BRAND.name, aspects = []) => {
  const noteFragment = note && note.trim() ? ` ${note.trim().replace(/[.!]+$/, '')}.` : '';
  const l = (lang || 'english').toLowerCase();
  const name = bizName || BRAND.name;

  const cleanedAspects = Array.isArray(aspects) ? aspects.map((a) => String(a).toLowerCase().trim()).filter(Boolean) : [];
  const hasBreakfast = cleanedAspects.some((a) => a.includes('breakfast') || a.includes('nasto') || a.includes('nasta'));
  const hasCoffee = cleanedAspects.some((a) => a.includes('coffee') || a.includes('chai') || a.includes('tea') || a.includes('drink') || a.includes('beverage'));
  const hasFood = cleanedAspects.some((a) => a.includes('food') || a.includes('taste') || a.includes('breakfast') || a.includes('snack') || a.includes('bakery'));
  const hasService = cleanedAspects.some((a) => a.includes('service') || a.includes('staff'));
  const hasAmbience = cleanedAspects.some((a) => a.includes('ambience') || a.includes('atmosphere') || a.includes('vibe'));
  const hasClean = cleanedAspects.some((a) => a.includes('clean') || a.includes('sitting'));

  let topicEn = '';
  let topicHi = '';
  let topicGu = '';

  if (hasBreakfast && hasCoffee) {
    topicEn = 'breakfast and chai';
    topicHi = 'breakfast aur chai';
    topicGu = 'breakfast ane chai';
  } else if (hasBreakfast) {
    topicEn = 'breakfast';
    topicHi = 'breakfast';
    topicGu = 'breakfast';
  } else if (hasCoffee) {
    topicEn = 'coffee and tea';
    topicHi = 'chai';
    topicGu = 'chai';
  } else if (hasFood) {
    topicEn = 'food';
    topicHi = 'khana';
    topicGu = 'food';
  } else if (hasService) {
    topicEn = 'service';
    topicHi = 'service';
    topicGu = 'service';
  } else if (hasAmbience) {
    topicEn = 'atmosphere';
    topicHi = 'atmosphere';
    topicGu = 'atmosphere';
  } else if (hasClean) {
    topicEn = 'sitting area';
    topicHi = 'sitting area';
    topicGu = 'sitting area';
  }

  let shortText = '';
  let detailedText = '';
  let personalText = '';

  if (l.includes('hin')) {
    if (r === 5) {
      if (topicHi) {
        shortText = `${name} me ${topicHi} bahut pasand aaya!${noteFragment} Maza aa gaya 🍳☕`;
        detailedText = `${name} me ${topicHi} ka experience lajawab raha.${noteFragment} Sab kuch accha manage kiya hua tha 😊✨`;
        personalText = `Personal taur par ${name} me ${topicHi} bahut accha laga.${noteFragment} Very happy with the visit ❤️`;
      } else {
        shortText = `Bahut hi accha anubhav raha at ${name}!${noteFragment} Maza aa gaya 😊✨`;
        detailedText = `Overall visit bahut shandar rahi at ${name}.${noteFragment} Sab kuch kaafi accha arrange tha 👍`;
        personalText = `Mere liye ${name} ka visit kaafi positive raha.${noteFragment} Happy with my visit ❤️`;
      }
    } else if (r === 4) {
      if (topicHi) {
        shortText = `${name} me ${topicHi} kaafi accha tha.${noteFragment} Accha anubhav raha 👍`;
        detailedText = `${name} me ${topicHi} ka overall experience accha raha.${noteFragment} Visit se khushi hui 🙂`;
        personalText = `${name} ka visit pasand aaya, khas taur par ${topicHi}.${noteFragment} Good visit overall 👍`;
      } else {
        shortText = `Accha anubhav raha at ${name}.${noteFragment} Thik se sab manage tha 👍`;
        detailedText = `Overall visit acchi rahi at ${name}.${noteFragment} Satisfied with today's visit 🙂`;
        personalText = `Mere liye ${name} ka visit accha raha.${noteFragment} Thik thaak arrange tha 👍`;
      }
    } else if (r === 3) {
      if (topicHi) {
        shortText = `${name} me ${topicHi} thik-thak raha.${noteFragment} Average experience 🙂`;
        detailedText = `${name} me ${topicHi} theek tha par kuch cheezein aur behtar ho sakti hain.${noteFragment} Standard visit 🙂`;
        personalText = `Mere hisab se ${name} me ${topicHi} average tha.${noteFragment} Normal visit overall 🙂`;
      } else {
        shortText = `Aaj ${name} ka anubhav thik-thak raha.${noteFragment} Normal visit 🙂`;
        detailedText = `Overall thik experience tha at ${name}.${noteFragment} Kuch sudhar ki gunjaish hai 🙂`;
        personalText = `Mera experience at ${name} average raha.${noteFragment} Standard experience 🙂`;
      }
    } else if (r === 2) {
      if (topicHi) {
        shortText = `${name} me ${topicHi} ummeed ke mutabik nahi tha.${noteFragment} 😕`;
        detailedText = `${name} me ${topicHi} se thodi nirasha hui.${noteFragment} Sudhar ki zaroorat hai 😕`;
        personalText = `${name} me ${topicHi} se jaisi ummeed thi waisa anubhav nahi mila.${noteFragment} 😕`;
      } else {
        shortText = `Aaj ${name} ka anubhav ummeed se kam raha.${noteFragment} 😕`;
        detailedText = `${name} ka visit satisfactory nahi raha.${noteFragment} Kafi cheezon par dhyan dene ki zaroorat hai 😕`;
        personalText = `Mujhe aaj ${name} ka visit pasand nahi aaya.${noteFragment} Needs improvement 😕`;
      }
    } else {
      if (topicHi) {
        shortText = `${name} me ${topicHi} ka anubhav bahut niraashajanak raha.${noteFragment} 😞`;
        detailedText = `Aaj ${name} me ${topicHi} se bilkul santusht nahi huye.${noteFragment} Bada sudhar chahiye 😞`;
        personalText = `${name} me ${topicHi} ka visit mere liye kafi kharab raha.${noteFragment} 😞`;
      } else {
        shortText = `Aaj ${name} me bahut kharab anubhav raha.${noteFragment} 😞`;
        detailedText = `${name} me aaj ka visit bilkul accha nahi raha.${noteFragment} Quality aur dhyan dono me kami thi 😞`;
        personalText = `Mujhe aaj ${name} me bilkul accha anubhav nahi mila.${noteFragment} Highly dissatisfied 😞`;
      }
    }
  } else if (l.includes('guj')) {
    if (r === 5) {
      if (topicGu) {
        shortText = `${name} ma ${topicGu} khub j gamyu!${noteFragment} Majo avi gayo ✨`;
        detailedText = `${name} ma ${topicGu} no anubhav lajawab rahyo.${noteFragment} Badhu vyavasthit hatu 😊`;
        personalText = `Mane ${name} ma ${topicGu} khub saras lagyu.${noteFragment} Khub santosh thayo ❤️`;
      } else {
        shortText = `Khub j saras anubhav rahyo at ${name}!${noteFragment} Majo avi gayo ✨`;
        detailedText = `${name} ni mulakat khub shandar rahi.${noteFragment} Badhi vyavastha saras hati 😊`;
        personalText = `Mane ${name} ni mulakat khub j pasand avi.${noteFragment} Khub anand thayo ❤️`;
      }
    } else if (r === 4) {
      if (topicGu) {
        shortText = `${name} ma ${topicGu} saru hatu.${noteFragment} Saras anubhav 👍`;
        detailedText = `${name} ma ${topicGu} no anubhav ekandare saras rahyo.${noteFragment} Khushi thai 🙂`;
        personalText = `Mane ${name} ma ${topicGu} pasand aavyu.${noteFragment} Good experience overall 👍`;
      } else {
        shortText = `Saras anubhav rahyo at ${name}.${noteFragment} Badhu barabar hatu 👍`;
        detailedText = `${name} ni mulakat ekandare sari rahi.${noteFragment} Santoshjanak anubhav 🙂`;
        personalText = `Mane ${name} ni mulakat sari lagi.${noteFragment} Overall good visit 👍`;
      }
    } else if (r === 3) {
      if (topicGu) {
        shortText = `${name} ma ${topicGu} thik-thak hatu.${noteFragment} Sadharan anubhav 🙂`;
        detailedText = `${name} ma ${topicGu} thik hatu pan thodu sudhari shakay em chhe.${noteFragment} Average visit 🙂`;
        personalText = `Mara mate ${name} ma ${topicGu} sadharan rahyu.${noteFragment} Normal experience 🙂`;
      } else {
        shortText = `Aaj no anubhav at ${name} thik-thak rahyo.${noteFragment} Sadharan mulakat 🙂`;
        detailedText = `${name} ni mulakat ekandare average rahi.${noteFragment} Sudhara ni jarur chhe 🙂`;
        personalText = `Mane ${name} no anubhav average lagyo.${noteFragment} Normal experience 🙂`;
      }
    } else if (r === 2) {
      if (topicGu) {
        shortText = `${name} ma ${topicGu} apeksha mujab na hatu.${noteFragment} 😕`;
        detailedText = `${name} ma ${topicGu} no anubhav thodo nirashajanak rahyo.${noteFragment} Sudhar ni jarur chhe 😕`;
        personalText = `Mane ${name} ma ${topicGu} thi jash na malyo.${noteFragment} 😕`;
      } else {
        shortText = `Aaj ni mulakat at ${name} apeksha karata ochhi rahi.${noteFragment} 😕`;
        detailedText = `${name} ni mulakat santoshjanak na rahi.${noteFragment} Dhyan aapvani jarur chhe 😕`;
        personalText = `Mane aaj no anubhav at ${name} pasand na aavyo.${noteFragment} 😕`;
      }
    } else {
      if (topicGu) {
        shortText = `${name} ma ${topicGu} ange khub nirasha thai.${noteFragment} 😞`;
        detailedText = `${name} ma ${topicGu} no anubhav bilkul saras na rahyo.${noteFragment} Sudharo jaruri chhe 😞`;
        personalText = `Mane ${name} ma ${topicGu} thi bilkul santosh na thayo.${noteFragment} 😞`;
      } else {
        shortText = `Aaj no anubhav at ${name} khub kharab rahyo.${noteFragment} 😞`;
        detailedText = `${name} ni mulakat bilkul sari na rahi.${noteFragment} Motu sudhar jaruri chhe 😞`;
        personalText = `Mane aaj no anubhav at ${name} bilkul pasand na aavyo.${noteFragment} 😞`;
      }
    }
  } else {
    // English
    if (r === 5) {
      if (topicEn) {
        shortText = `Really enjoyed the ${topicEn} at ${name}!${noteFragment} Great experience ✨`;
        detailedText = `Had a wonderful time with the ${topicEn} at ${name}.${noteFragment} Everything went smoothly 😊`;
        personalText = `Personally loved the ${topicEn} at ${name}.${noteFragment} Very pleased with this visit 👍`;
      } else {
        shortText = `Excellent experience at ${name}!${noteFragment} Thoroughly enjoyed it ✨`;
        detailedText = `Everything went smoothly during today's visit to ${name}.${noteFragment} Really pleased with the experience 😊`;
        personalText = `A truly great visit to ${name} for me.${noteFragment} Very satisfied with everything 👍`;
      }
    } else if (r === 4) {
      if (topicEn) {
        shortText = `Good experience with the ${topicEn} at ${name}.${noteFragment} 👍`;
        detailedText = `Overall a solid experience with the ${topicEn} at ${name}.${noteFragment} Glad I visited 🙂`;
        personalText = `Had a good visit for ${topicEn} at ${name}.${noteFragment} Happy with how things went 👍`;
      } else {
        shortText = `Good visit overall at ${name}.${noteFragment} Everything was in order 👍`;
        detailedText = `Overall a solid and enjoyable experience at ${name}.${noteFragment} Everything was well arranged 😊`;
        personalText = `Had a good visit at ${name}.${noteFragment} Happy with my experience overall 👍`;
      }
    } else if (r === 3) {
      if (topicEn) {
        shortText = `Decent visit for ${topicEn} at ${name}.${noteFragment} Standard experience 🙂`;
        detailedText = `The ${topicEn} at ${name} was fine overall.${noteFragment} An average visit with room for minor improvement 🙂`;
        personalText = `It was a pretty average experience for ${topicEn} at ${name}.${noteFragment} Decent visit overall 🙂`;
      } else {
        shortText = `Decent visit today at ${name}.${noteFragment} Standard experience 🙂`;
        detailedText = `Overall a fair and average experience at ${name}. A few good points, but there is room for improvement.${noteFragment} Decent visit 🙂`;
        personalText = `It was a pretty average visit for me at ${name}.${noteFragment} Fair experience overall 🙂`;
      }
    } else if (r === 2) {
      if (topicEn) {
        shortText = `The ${topicEn} at ${name} fell below expectations today.${noteFragment} 😕`;
        detailedText = `Disappointed with the ${topicEn} at ${name}.${noteFragment} The experience needs attention and improvement 😕`;
        personalText = `Expected a better experience with the ${topicEn} at ${name}.${noteFragment} Hope to see improvements 😕`;
      } else {
        shortText = `Visit fell below expectations today at ${name}.${noteFragment} 😕`;
        detailedText = `Somewhat disappointed with the visit at ${name}.${noteFragment} Several areas need attention and better care 😕`;
        personalText = `Expected a better experience than what I had at ${name} today.${noteFragment} Hope to see improvements 😕`;
      }
    } else {
      if (topicEn) {
        shortText = `Very disappointing experience with the ${topicEn} at ${name} today.${noteFragment} 😞`;
        detailedText = `Unsatisfied with the ${topicEn} during today's visit to ${name}.${noteFragment} Major improvements are needed 😞`;
        personalText = `Really unhappy with the ${topicEn} at ${name} today.${noteFragment} Disappointed with how things went 😞`;
      } else {
        shortText = `Very disappointing experience today at ${name}.${noteFragment} 😞`;
        detailedText = `Extremely unsatisfied with today's visit at ${name}.${noteFragment} Major improvements are needed in service and quality 😞`;
        personalText = `Really unhappy with the experience today.${noteFragment} Disappointed with how things were handled at ${name} 😞`;
      }
    }
  }

  return [
    { id: 'opt1', focus: 'Short & Natural', text: shortText },
    { id: 'opt2', focus: 'Detailed & Expressive', text: detailedText },
    { id: 'opt3', focus: 'Simple & Personal', text: personalText },
  ];
};

export default function CustomerReview({
  businessId = 'default_business',
  onSwitchToOwner = null,
  isPreview = false,
}) {
  const urlParams = new URLSearchParams(window.location.search);
  const tableParam = urlParams.get('table') || null;
  const isPreviewMode = isPreview || urlParams.get('preview') === 'true';

  // Automatic browser-side language detection ONLY (no manual UI, consistent across all components)
  const language = detectBrowserLanguage();
  const t = UI_STRINGS[language] || UI_STRINGS.english;

  // Custom editor view toggle (inline)
  const [showCustomEditor, setShowCustomEditor] = useState(false);
  const reviewCardRef = useRef(null);
  const editorRef = useRef(null);
  const topicsSectionRef = useRef(null);

  // Load existing session draft if valid and not expired
  const initialDraft = loadDraft(businessId);

  // Rating
  const [rating, setRating] = useState(() => (initialDraft?.rating >= 1 && initialDraft?.rating <= 5 ? initialDraft.rating : 5));
  const [hoverRating, setHoverRating] = useState(0);
  const [reviewStarted, setReviewStarted] = useState(() => Boolean(initialDraft?.reviewStarted));

  // Business Category & Dynamic Branding
  const [businessName, setBusinessName] = useState(() => (businessId === 'default_business' || businessId === 'nasta_ghar' ? BRAND.name : ''));
  const [primaryAccent, setPrimaryAccent] = useState('#f97316');
  const [businessDescription, setBusinessDescription] = useState('');
  const [businessCategory, setBusinessCategory] = useState('Breakfast & Snacks');
  const [notFound, setNotFound] = useState(false);
  const [notFoundId, setNotFoundId] = useState('');

  // Topics
  const [availableTopics, setAvailableTopics] = useState(DEFAULT_TOPICS);
  const [selectedTopics, setSelectedTopics] = useState(() => (Array.isArray(initialDraft?.selectedTopics) ? initialDraft.selectedTopics : ['Breakfast', 'Chai & Tea']));
  const [nothingSpecific, setNothingSpecific] = useState(() => Boolean(initialDraft?.nothingSpecific));
  const [personalNote, setPersonalNote] = useState(() => initialDraft?.personalNote || '');

  // Keep Google Maps pointed at the restaurant's selected destination.
  const [googleReviewUrl, setGoogleReviewUrl] = useState(BRAND.googleMapUrl);

  // Ideas initialized with fallback ideas (no empty screen, instant feedback)
  const [ideas, setIdeas] = useState(() => getFallbackIdeas(rating, personalNote, language, businessName || BRAND.name, nothingSpecific ? [] : selectedTopics));
  const [loadingIdeas, setLoadingIdeas] = useState(false);
  const [ideasError, setIdeasError] = useState(false);
  const isFetchingIdeasRef = useRef(false);
  const [selectedIdeaId, setSelectedIdeaId] = useState(() => initialDraft?.selectedIdeaId || null);
  const fetchIdeasDebounceRef = useRef(null);

  // Editor
  const [draftReview, setDraftReview] = useState(() => initialDraft?.draftReview || '');
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Session & analytics
  const [sessionId, setSessionId] = useState('');

  // Handoff
  const [handoffOpen, setHandoffOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [copyingReview, setCopyingReview] = useState(false);
  const [showCopyToast, setShowCopyToast] = useState(false);
  const [copyAgainSuccess, setCopyAgainSuccess] = useState(false);

  // Private feedback
  const [showPrivate, setShowPrivate] = useState(false);
  const [privateNote, setPrivateNote] = useState('');
  const [privateContact, setPrivateContact] = useState('');
  const [privateSent, setPrivateSent] = useState(false);
  const [privateError, setPrivateError] = useState('');
  const [isSubmittingPrivate, setIsSubmittingPrivate] = useState(false);

  // Clean tenant storage isolation when switching between businesses
  useEffect(() => {
    try {
      const savedBusinessId = sessionStorage.getItem('nastaGharActiveBusinessId');
      if (savedBusinessId && savedBusinessId !== businessId) {
        clearSessionDraft(savedBusinessId);
        setDraftReview('');
        setSelectedIdeaId(null);
        setSelectedTopics(['Breakfast', 'Chai & Tea']);
        setNothingSpecific(false);
        setPersonalNote('');
        setReviewStarted(false);
        setCopied(false);
        setHandoffOpen(false);
      }
      sessionStorage.setItem('nastaGharActiveBusinessId', businessId);
      const activeDraft = loadDraft(businessId);
      if (activeDraft) {
        if (activeDraft.rating) setRating(activeDraft.rating);
        if (activeDraft.selectedTopics) setSelectedTopics(activeDraft.selectedTopics);
        if (activeDraft.personalNote) setPersonalNote(activeDraft.personalNote);
        if (activeDraft.draftReview) setDraftReview(activeDraft.draftReview);
        if (activeDraft.reviewStarted) setReviewStarted(true);
      }
    } catch {
      // Session storage can be unavailable in restricted contexts.
    }
  }, [businessId]);

  // Acknowledgement for clipboard handoff instructions
  const [cookieConsent, setCookieConsent] = useState(() => {
    try {
      return localStorage.getItem('ng_clipboard_notice_seen') === 'true';
    } catch {
      return false;
    }
  });

  const handleAcceptConsent = () => {
    try {
      localStorage.setItem('ng_clipboard_notice_seen', 'true');
    } catch {}
    setCookieConsent(true);
  };

  // ─── FETCH CONFIG (dynamic per business ID) ──────────────────────────────
  useEffect(() => {
    let active = true;
    setNotFound(false);

    apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/review-link`)
      .then(async (r) => {
        if (!r.ok) {
          if (r.status === 404 || r.status === 422) {
            if (active) {
              setNotFound(true);
              setNotFoundId(businessId);
            }
            return null;
          }
          throw new Error('Config load failed');
        }
        return r.json();
      })
      .then((d) => {
        if (!d || !active) return;
        const resolvedName = d.business_name || (businessId === 'default_business' ? BRAND.name : businessId);
        setBusinessName(resolvedName);
        if (d.review_url) setGoogleReviewUrl(d.review_url);
        if (d.category) setBusinessCategory(d.category);
        if (d.primary_accent) setPrimaryAccent(d.primary_accent);
        if (d.description) setBusinessDescription(d.description);
        if (d.topics && d.topics.length > 0) {
          const enriched = d.topics.map((item) => ({
            label: item,
            icon: getTopicIcon(item),
          }));
          setAvailableTopics(enriched);
          const currentDraft = loadDraft(businessId);
          if (!currentDraft?.selectedTopics) {
            setSelectedTopics(d.topics.slice(0, 2));
            saveDraft(businessId, { selectedTopics: d.topics.slice(0, 2) });
          }
        }
        setIdeas(getFallbackIdeas(rating, personalNote, language, resolvedName, nothingSpecific ? [] : selectedTopics));
      })
      .catch(() => {
        if (businessId === 'default_business' || businessId === 'nasta_ghar') {
          if (active) setBusinessName(BRAND.name);
        }
      });

    // Initialize session
    apiFetch(`/api/reviews/session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        business_id: businessId,
        table_number: tableParam || 'Walk-in',
        dining_type: 'dine_in',
      }),
    })
      .then((r) => r.json())
      .then((d) => { if (active) setSessionId(d.session_id); })
      .catch(() => { if (active) setSessionId(`local-${Date.now()}`); });

    return () => { active = false; };
  }, [businessId, tableParam]);

  function getTopicIcon(label) {
    const l = label.toLowerCase();
    if (l.includes('breakfast') || l.includes('nasta')) return '🍳';
    if (l.includes('chai') || l.includes('tea') || l.includes('coffee') || l.includes('drink') || l.includes('beverage')) return '☕';
    if (l.includes('snack')) return '🥪';
    if (l.includes('taste') || l.includes('flavour') || l.includes('food')) return '😋';
    if (l.includes('staff') || l.includes('service') || l.includes('friendly')) return '😊';
    if (l.includes('clean')) return '✨';
    if (l.includes('value') || l.includes('money') || l.includes('price')) return '💰';
    if (l.includes('quick') || l.includes('fast') || l.includes('speed')) return '⚡';
    if (l.includes('atmosphere') || l.includes('vibe') || l.includes('ambience')) return '🌟';
    return '👍';
  }

  // ─── ANALYTICS ──────────────────────────────────────────────────────────────
  const logEvent = (name, meta = {}) => {
    if (!sessionId) return;
    apiFetch(`/api/reviews/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      keepalive: true,
      body: JSON.stringify({
        session_id: sessionId,
        event_name: name,
        metadata: { business_id: businessId, rating, ...meta },
      }),
    }).catch(() => {});
  };

  // ─── BULLETPROOF CLIPBOARD COPY ─────────────────────────────────────────────
  const copyTextToClipboard = async (text) => {
    if (!text) return false;
    let ok = false;
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(text);
        ok = true;
      } catch (e) {
        console.warn('navigator.clipboard failed:', e);
      }
    }
    if (!ok) {
      let ta;
      try {
        ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        ta.style.top = '-9999px';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        ok = document.execCommand('copy');
      } catch (e) {
        console.error('execCommand copy failed:', e);
      } finally {
        ta?.remove();
      }
    }
    return ok;
  };

  // ─── HANDLERS ───────────────────────────────────────────────────────────────
  const handleRating = (s) => {
    setRating(s);
    saveDraft(businessId, { rating: s });
    logEvent('rating_selected', { rating: s });
  };

  const handleContinueReview = () => {
    setReviewStarted(true);
    saveDraft(businessId, { reviewStarted: true });
    setTimeout(() => {
      topicsSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 60);
  };

  const toggleTopic = (label) => {
    setNothingSpecific(false);
    setSelectedTopics((prev) => {
      const next = prev.includes(label) ? prev.filter((item) => item !== label) : [...prev, label];
      saveDraft(businessId, { selectedTopics: next, nothingSpecific: false });
      logEvent('aspects_selected', { aspects: next });
      return next;
    });
  };

  const handleNothingSpecific = () => {
    setNothingSpecific(true);
    setSelectedTopics([]);
    saveDraft(businessId, { selectedTopics: [], nothingSpecific: true });
    logEvent('aspects_selected', { aspects: [] });
  };

  // Dedicated fetcher for candidate ideas with concurrent lock and explicit retry
  const fetchAiIdeas = async (isManualRetry = false) => {
    if (isFetchingIdeasRef.current) return;
    isFetchingIdeasRef.current = true;
    setLoadingIdeas(true);
    if (isManualRetry) setIdeasError(false);

    try {
      const res = await apiFetch('/api/reviews/ideas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: businessId,
          rating,
          aspects: nothingSpecific ? [] : selectedTopics,
          user_note: personalNote.trim(),
          language,
          category: businessCategory,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.ideas && Array.isArray(data.ideas) && data.ideas.length > 0) {
          setIdeas(data.ideas.slice(0, 3));
          setIdeasError(false);
        } else {
          setIdeasError(true);
        }
      } else {
        setIdeasError(true);
      }
    } catch {
      setIdeasError(true);
    } finally {
      setLoadingIdeas(false);
      isFetchingIdeasRef.current = false;
    }
  };

  // Automatically keep ideas synchronized with rating, topics, and personal note
  useEffect(() => {
    setIdeas(getFallbackIdeas(rating, personalNote, language, businessName || BRAND.name, nothingSpecific ? [] : selectedTopics));
    setIdeasError(false);

    if (fetchIdeasDebounceRef.current) {
      clearTimeout(fetchIdeasDebounceRef.current);
    }

    fetchIdeasDebounceRef.current = setTimeout(() => {
      fetchAiIdeas(false);
    }, 350);

    return () => {
      if (fetchIdeasDebounceRef.current) {
        clearTimeout(fetchIdeasDebounceRef.current);
      }
    };
  }, [rating, selectedTopics, nothingSpecific, personalNote, businessId, language, businessCategory]);

  const handlePostDirectly = async (idea) => {
    if (copyingReview) return;
    await startReviewHandoff(idea.text, idea.id);
  };

  const startReviewHandoff = async (reviewText, reviewId) => {
    if (!reviewText?.trim()) return;
    setSelectedIdeaId(reviewId);
    setDraftReview(reviewText);
    setHandoffOpen(true);
    setCopyingReview(true);
    setShowCopyToast(false);
    logEvent('review_selected', { review_id: reviewId });
    logEvent('idea_selected', { idea_id: reviewId });
    logEvent('review_approved', { length: reviewText.length, direct_post: true });
    logEvent('google_review_handoff_started', { review_id: reviewId });

    saveDraft(businessId, { draftReview: reviewText, selectedIdeaId: reviewId });

    const copiedSuccessfully = await copyTextToClipboard(reviewText);
    setCopyingReview(false);
    setCopied(copiedSuccessfully);
    setShowCopyToast(true);
    setTimeout(() => setShowCopyToast(false), 3500);
    logEvent(copiedSuccessfully ? 'review_clipboard_success' : 'review_clipboard_failed', { review_id: reviewId });

    if (copiedSuccessfully) {
      logEvent('google_maps_redirect', { destination: googleReviewUrl });
      logEvent('google_review_link_opened');
      // Clear draft upon successful completion so customer or new session does not restore stale draft
      clearSessionDraft(businessId);
      window.location.href = googleReviewUrl;
      return;
    }

    setHandoffOpen(true);
  };

  const handleMakeNatural = async () => {
    setIsRegenerating(true);
    try {
      const res = await apiFetch(`/api/reviews/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: businessId,
          rating,
          aspects: selectedTopics,
          user_note: personalNote.trim(),
          selected_idea: draftReview || undefined,
          emoji_preference: 'light',
          language,
          category: businessCategory,
        }),
      });
      const data = await res.json();
      if (data.review) {
        setDraftReview(data.review);
        saveDraft(businessId, { draftReview: data.review });
      }
    } catch { /* keep current */ }
    finally { setIsRegenerating(false); }
  };

  const handleContinueToGoogle = async () => {
    if (!draftReview.trim()) return;
    await startReviewHandoff(draftReview, selectedIdeaId);
  };

  const handlePrivateFeedback = async (e) => {
    e.preventDefault();
    if (isSubmittingPrivate || !privateNote.trim()) return;
    setIsSubmittingPrivate(true);
    setPrivateError('');
    try {
      const response = await apiFetch(`/api/reviews/private-feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_id: businessId,
          table_number: tableParam,
          rating,
          diner_note: privateNote,
          aspects: selectedTopics,
          guest_contact: privateContact,
        }),
      });
      if (!response.ok) throw new Error('Feedback request failed');
      setPrivateSent(true);
      logEvent('private_feedback_sent');
      // Clear draft upon completed private submission
      clearSessionDraft(businessId);
    } catch {
      setPrivateError('We couldn’t send your message right now. Please try again.');
    } finally {
      setIsSubmittingPrivate(false);
    }
  };

  const activeRating = hoverRating || rating;
  const ratingLabel = t.ratings[activeRating] || t.ratings[5];

  // ─── RENDER ─────────────────────────────────────────────────────────────────
  if (notFound) {
    return (
      <div className="ng-page">
        {isPreviewMode && (
          <div className="ng-preview-bar">
            <span>👁️ Owner Preview Mode</span>
            {onSwitchToOwner && (
              <button type="button" className="ng-preview-back" onClick={onSwitchToOwner}>
                ← Back to Dashboard
              </button>
            )}
          </div>
        )}
        <div className="ng-card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem', margin: '2rem auto', maxWidth: '480px' }}>
          <div style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>🔍</div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: '700', marginBottom: '0.75rem', color: '#1e293b' }}>
            Business Not Found
          </h2>
          <p style={{ color: '#64748b', fontSize: '0.95rem', lineHeight: '1.5', marginBottom: '1.5rem' }}>
            We could not find any business matching <strong>{notFoundId}</strong>. Please check your link or scan the QR code again.
          </p>
          {onSwitchToOwner && (
            <button type="button" className="ng-btn-primary" onClick={onSwitchToOwner} style={{ margin: '0 auto' }}>
              Open Owner Portal
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="ng-page">
      {/* Preview Banner */}
      {isPreviewMode && (
        <div className="ng-preview-bar">
          <span>👁️ Owner Preview Mode</span>
          {onSwitchToOwner && (
            <button type="button" className="ng-preview-back" onClick={onSwitchToOwner}>
              ← Back to Dashboard
            </button>
          )}
        </div>
      )}

      {(businessId === 'default_business' || businessId === 'nasta_ghar') ? (
        <RestaurantWorld />
      ) : (
        <div className="ng-scene-wrapper compact" style={{ minHeight: '140px', background: `linear-gradient(135deg, ${primaryAccent}15, ${primaryAccent}30)` }}>
          <div style={{ padding: '2rem 1rem', textAlign: 'center' }}>
            <span style={{ fontSize: '3rem' }}>
              {businessCategory.toLowerCase().includes('cafe') ? '☕' : businessCategory.toLowerCase().includes('hotel') ? '🏨' : '🍽️'}
            </span>
          </div>
        </div>
      )}

      <div
        ref={reviewCardRef}
        className={`ng-card ${!reviewStarted ? 'ng-initial-card' : 'ng-expanded-card'}`}
      >
        {/* ── HEADER ─────────────────────────────────────────────────────── */}
        <header className="ng-header">
          {(businessId === 'default_business' || businessId === 'nasta_ghar') ? (
            <>
              <h1 className="ng-brand-name">નાસ્તા ઘર</h1>
              <p className="ng-brand-sub">Homestyle Breakfast & Chai • Rajkot</p>
            </>
          ) : (
            <>
              <h1 className="ng-brand-name">{businessName || 'Review Assistant'}</h1>
              <p className="ng-brand-sub">{businessDescription || businessCategory || 'Hospitality Review Assistant'}</p>
            </>
          )}
          {tableParam && (
            <span className="ng-table-pill">📍 {tableParam}</span>
          )}
        </header>

        {/* ── SECTION 1: RATING ─────────────────────────────────────────── */}
        <section className="ng-section" aria-label="Rating selection">
          <h2 className="ng-section-title">{t.howWasVisit}</h2>
          <p className="ng-section-sub">{t.tapStar}</p>

          <div className="ng-stars-row" role="radiogroup" aria-label="Star rating">
            {[1, 2, 3, 4, 5].map((s) => (
              <button
                key={s}
                type="button"
                className={`ng-star ${activeRating >= s ? 'lit' : ''}`}
                onClick={() => handleRating(s)}
                onMouseEnter={() => setHoverRating(s)}
                onMouseLeave={() => setHoverRating(0)}
                aria-label={`${s} star${s > 1 ? 's' : ''}`}
                aria-pressed={activeRating >= s}
              >
                ★
              </button>
            ))}
          </div>

          <div className="ng-rating-label">
            <span className="ng-rating-emoji">{ratingLabel.emoji}</span>
            <span>{ratingLabel.text}</span>
          </div>

          {!reviewStarted && (
            <button
              type="button"
              className="ng-btn-primary ng-btn-continue-initial"
              onClick={handleContinueReview}
            >
              {t.continueBtn}
            </button>
          )}
        </section>

        {reviewStarted && (
          <>
            <div className="ng-section-divider" aria-hidden="true" />

            {/* ── SECTION 2: TOPICS / HIGHLIGHTS (Automatic detected language applied, no manual language selector) ── */}
            <section ref={topicsSectionRef} className="ng-section ng-fade-in" aria-label="Visit highlights">
              <h2 className="ng-section-title">{t.whatStoodOut}</h2>
              <p className="ng-section-sub">{t.pickMatched}</p>

              <div className="ng-chips-grid">
                {availableTopics.map(({ label, icon }) => {
                  const selected = selectedTopics.includes(label);
                  return (
                    <button
                      key={label}
                      type="button"
                      className={`ng-chip ${selected ? 'selected' : ''}`}
                      onClick={() => toggleTopic(label)}
                      aria-pressed={selected}
                    >
                      <span className="ng-chip-icon">{icon}</span>
                      <span>{label}</span>
                    </button>
                  );
                })}
                <button
                  type="button"
                  className={`ng-chip ng-chip-neutral ${nothingSpecific ? 'selected' : ''}`}
                  onClick={handleNothingSpecific}
                  aria-pressed={nothingSpecific}
                >
                  <span className="ng-chip-icon">—</span>
                  <span>{t.nothingSpecific}</span>
                </button>
              </div>

              <div className="ng-note-wrap">
                <label htmlFor="ng-note" className="ng-note-label">
                  {t.personalNote} <span className="ng-optional">({t.optional})</span>
                </label>
                <input
                  id="ng-note"
                  type="text"
                  className="ng-note-input"
                  placeholder={t.notePlaceholder}
                  value={personalNote}
                  onChange={(e) => {
                    const val = e.target.value;
                    setPersonalNote(val);
                    saveDraft(businessId, { personalNote: val });
                  }}
                  maxLength={100}
                  data-gramm="false"
                  data-enable-grammarly="false"
                />
              </div>
            </section>

            <div className="ng-section-divider" aria-hidden="true" />

            {/* ── SECTION 3: REVIEW IDEAS / CUSTOM EDITOR ───────────────────── */}
            {!showCustomEditor ? (
              <section className="ng-section" aria-label="Review suggestions">
                <div className="ng-ideas-header">
                  <h2 className="ng-section-title">{t.reviewIdeas}</h2>
                  <p className="ng-section-sub">{t.tapFavourite}</p>
                  {loadingIdeas && (
                    <div className="ng-updating-badge">
                      <span>✨</span>
                      <span>{t.refiningIdeas}</span>
                    </div>
                  )}
                </div>

                {ideasError && (
                  <div className="ng-ideas-error-banner" role="alert">
                    <div className="ng-ideas-error-content">
                      <span className="ng-ideas-error-icon">⚠️</span>
                      <span className="ng-ideas-error-text">{t.errorRefresh}</span>
                    </div>
                    <button
                      type="button"
                      className="ng-btn-retry-ideas"
                      onClick={() => fetchAiIdeas(true)}
                      disabled={loadingIdeas}
                    >
                      {loadingIdeas ? t.retrying : t.retry}
                    </button>
                  </div>
                )}

                <div className="ng-ideas-list">
                  {ideas.map((idea, i) => (
                    <div
                      key={idea.id || i}
                      className={`ng-idea-card ${selectedIdeaId === idea.id ? 'picked' : ''}`}
                      onClick={() => handlePostDirectly(idea)}
                      role="button"
                      tabIndex={0}
                      aria-label={`Option ${i + 1}: ${idea.text}`}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          handlePostDirectly(idea);
                        }
                      }}
                    >
                      <div className="ng-idea-meta">
                        <span className="ng-idea-num">{idea.focus || `Option ${i + 1}`}</span>
                        <span className="ng-idea-lang">{getLanguageLabel(language)}</span>
                        <span className="ng-idea-stars">{'★'.repeat(rating)}</span>
                      </div>
                      <p className="ng-idea-text">"{idea.text}"</p>
                      <div className="ng-idea-action">
                        <span>{t.useThisReview}</span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="ng-divider"><span>or</span></div>

                <button
                  type="button"
                  className="ng-btn-write-own"
                  aria-expanded={showCustomEditor}
                  aria-controls="ng-custom-editor-section"
                  onClick={() => {
                    setSelectedIdeaId('custom');
                    if (!draftReview) setDraftReview('');
                    setShowCustomEditor(true);
                    setTimeout(() => editorRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
                  }}
                >
                  {t.writeOwn}
                </button>
              </section>
            ) : (
              <section id="ng-custom-editor-section" ref={editorRef} className="ng-section ng-fade-in" aria-label="Custom review editor">
                <div className="ng-editor-header">
                  <h2 className="ng-section-title" style={{ margin: 0 }}>{t.writeTitle}</h2>
                  <span className="ng-char-pill">{draftReview.length} {t.chars}</span>
                </div>
                <p className="ng-section-sub">{t.writeSub}</p>

                <div className="ng-textarea-wrap">
                  <textarea
                    className="ng-textarea"
                    rows={5}
                    value={draftReview}
                    onChange={(e) => {
                      const val = e.target.value;
                      setDraftReview(val);
                      saveDraft(businessId, { draftReview: val });
                    }}
                    placeholder={t.feedbackPlaceholder}
                    data-gramm="false"
                    data-enable-grammarly="false"
                  />
                </div>

                <div className="ng-editor-tools">
                  <button
                    type="button"
                    className="ng-btn-tool"
                    onClick={handleMakeNatural}
                    disabled={isRegenerating || !draftReview.trim()}
                  >
                    {isRegenerating ? t.refiningNatural : t.makeNatural}
                  </button>
                  <button
                    type="button"
                    className="ng-btn-tool"
                    onClick={() => setShowCustomEditor(false)}
                  >
                    {t.backToIdeas}
                  </button>
                </div>

                <div className="ng-google-notice">
                  {t.googleNotice}
                </div>

                <button
                  type="button"
                  className="ng-btn-primary ng-btn-cta"
                  onClick={handleContinueToGoogle}
                  disabled={!draftReview.trim()}
                >
                  {t.copyAndOpenGoogle}
                </button>
              </section>
            )}

            {/* ── SECTION 4: PRIVATE FEEDBACK PROMPT ────────────────────────── */}
            <div className="ng-private-prompt">
              {rating <= 3 ? t.privatePromptBad : t.privatePromptGood}
              <button type="button" className="ng-link-btn" onClick={() => setShowPrivate(true)}>
                {t.sendPrivateNote}
              </button>
            </div>
          </>
        )}
      </div>

      {/* ════════ FLOATING COPY TOAST ════════ */}
      {showCopyToast && (
        <div className="ng-toast" role="alert">
          <span className="ng-toast-icon">📋</span>
          <span className="ng-toast-msg">
            {copied
              ? (language === 'hindi'
                  ? "Aapka review copy ho gaya hai ✓ Google Maps par 'Write a review' tap karein, same rating select karke Paste karein."
                  : language === 'gujarati'
                  ? "તમારો review copy થઈ ગયો છે ✓ Google Maps માં 'Write a review' tap કરો, same rating select કરીને Paste કરો."
                  : "Your review is copied ✓ On Google Maps, tap 'Write a review', select the same rating, and paste.")
              : (language === 'hindi'
                  ? "Review copy nahi hua. Dobara koshish karne ke liye 'Copy Review' tap karein."
                  : language === 'gujarati'
                  ? "Review copy na thayu. Fari prayas karva 'Copy Review' par tap karo."
                  : "Review could not be copied. Tap 'Copy Review' to try again.")}
          </span>
        </div>
      )}

      {/* ════════ HANDOFF MODAL ════════ */}
      {handoffOpen && (
        <div className="ng-modal-backdrop">
          <div className="ng-modal ng-modal-bounce">
            <div className="ng-modal-icon">📋</div>
            <h3 className="ng-modal-title">
              {copyingReview
                ? (language === 'hindi' ? 'Review taiyar ho raha hai…' : language === 'gujarati' ? 'Review તૈયાર થઈ રહ્યો છે…' : 'Preparing your review…')
                : copied
                ? (language === 'hindi' ? 'Review Clipboard par Copy Ho Gaya ✓' : language === 'gujarati' ? 'Review Clipboard પર Copy થઈ ગયો ✓' : 'Review Copied to Clipboard ✓')
                : (language === 'hindi' ? 'Review Copy Karke Aage Badhein' : language === 'gujarati' ? 'Review Copy Kari Aagal Vadho' : 'Copy Your Review to Continue')}
            </h3>
            <p className="ng-modal-body">
              {copyingReview ? (
                language === 'hindi' ? (
                  <>Aapka review taiyar hai. Clipboard par copy karke Google Maps khol rahe hain…</>
                ) : language === 'gujarati' ? (
                  <>તમારો review તૈયાર છે. Clipboard પર copy કરી રહ્યા છીએ અને Google Maps ખોલી રહ્યા છીએ…</>
                ) : (
                  <>Preparing your review. Copying to clipboard and opening Google Maps…</>
                )
              ) : copied ? (
                language === 'hindi' ? (
                  <>
                    Aapka review copy ho gaya hai ✓ Aapne yahan <strong>{rating}★</strong> chuna hai. Google Maps par <strong>Write a review</strong> tap karein, same rating select karein aur paste karein.
                  </>
                ) : language === 'gujarati' ? (
                  <>
                    તમારો review copy થઈ ગયો છે ✓ તમે અહીં <strong>{rating}★</strong> પસંદ કર્યા છે. Google Maps પર <strong>Write a review</strong> tap કરો, same rating પસંદ કરો અને review paste કરો.
                  </>
                ) : (
                  <>
                    Your review is copied ✓ You selected <strong>{rating}★</strong> here. On Google Maps, tap <strong>Write a review</strong>, select the same rating, then paste your review.
                  </>
                )
              ) : (
                language === 'hindi' ? (
                  <>
                    Review copy nahi hua. Niche diye gaye review ko copy karein aur Google Maps par paste karein (aapne yahan <strong>{rating}★</strong> chuna tha).
                  </>
                ) : language === 'gujarati' ? (
                  <>
                    Review copy na thayu. Niche aapyelo review copy karo ane Google Maps ma paste karo (tame ahiya <strong>{rating}★</strong> પસંદ કર્યા છે).
                  </>
                ) : (
                  <>
                    Review copy failed. Your selected review is saved below; copy it manually and paste into Google Maps (you selected <strong>{rating}★</strong> here).
                  </>
                )
              )}
            </p>

            <div className="ng-modal-steps">
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">1</span>
                <span>
                  {language === 'hindi'
                    ? <>Google par wahi rating chunein jo yahan chuni thi (aapne <strong>{rating} stars</strong> chune hain)</>
                    : language === 'gujarati'
                    ? <>Google par ae j rating select karo je ahiya select kari hati (tame <strong>{rating} stars</strong> select karya chhe)</>
                    : <>Choose the rating that reflects your visit on Google (you selected <strong>{rating} stars</strong> here)</>}
                </span>
              </div>
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">2</span>
                <span>
                  {copyingReview
                    ? (language === 'hindi' ? 'Selected review copy ho raha hai…' : language === 'gujarati' ? 'Selected review copy thai rahyo chhe…' : 'Copying selected review…')
                    : copied
                    ? (language === 'hindi'
                        ? <>Copied review ko <strong>Paste</strong> karein (apne device ka Paste command use karein)</>
                        : language === 'gujarati'
                        ? <>Copied review ne <strong>Paste</strong> karo (screen par long-press kari Paste karo)</>
                        : <><strong>Paste</strong> the copied review (use your device's Paste command, or long-press → Paste on mobile)</>)
                    : (language === 'hindi'
                        ? <>Niche se review copy karein aur Google par <strong>Paste</strong> karein</>
                        : language === 'gujarati'
                        ? <>Niche thi review copy karo ane Google par <strong>Paste</strong> karo</>
                        : <>Copy the review below, then <strong>paste</strong> it into Google</>)}
                </span>
              </div>
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">3</span>
                <span>
                  {language === 'hindi'
                    ? <>Review check karein aur Google ke <strong>Post</strong> button par tap karein.</>
                    : language === 'gujarati'
                    ? <>Review check karo ane Google na <strong>Post</strong> button par tap karo.</>
                    : <>Review it, then tap Google's <strong>Post</strong> button when you're ready.</>}
                </span>
              </div>
            </div>

            <div className="ng-preview-box">
              <p className="ng-preview-text">"{draftReview}"</p>
              <button
                type="button"
                className="ng-btn-copy-mini"
                disabled={copyingReview}
                onClick={async () => {
                  const ok = await copyTextToClipboard(draftReview);
                  setCopied(ok);
                  setCopyAgainSuccess(ok);
                  logEvent(ok ? 'review_clipboard_success' : 'review_clipboard_failed', { review_id: selectedIdeaId });
                  if (ok) setTimeout(() => setCopyAgainSuccess(false), 2000);
                }}
              >
                {copyAgainSuccess
                  ? '✓ Copied!'
                  : copied
                  ? (language === 'hindi' ? '📋 Dobara Copy Karein' : language === 'gujarati' ? '📋 Fari Copy Karo' : '📋 Copy Again')
                  : (language === 'hindi' ? '📋 Review Copy Karein' : language === 'gujarati' ? '📋 Review Copy Karo' : '📋 Copy Review')}
              </button>
            </div>

            <div className="ng-modal-actions">
              <button
                type="button"
                className="ng-btn-primary"
                disabled={copyingReview}
                onClick={() => {
                  logEvent('google_maps_redirect', { destination: googleReviewUrl });
                  logEvent('google_review_link_opened');
                  clearSessionDraft(businessId);
                  window.location.href = googleReviewUrl;
                }}
              >
                {language === 'hindi' ? '↗ Google Maps Kholein' : language === 'gujarati' ? '↗ Google Maps Kholo' : '↗ Continue to Google Maps'}
              </button>
              <button
                type="button"
                className="ng-btn-secondary"
                onClick={() => setHandoffOpen(false)}
              >
                Done ✓
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ════════ PRIVATE FEEDBACK MODAL ════════ */}
      {showPrivate && (
        <div className="ng-modal-backdrop">
          <div className="ng-modal ng-modal-bounce">
            <h3 className="ng-modal-title">{t.directNoteTo} {businessName || BRAND.name}</h3>
            <p className="ng-modal-body">{t.sharePrivately}</p>

            {privateSent ? (
              <div className="ng-private-success">
                <span style={{ fontSize: '2rem' }}>💌</span>
                <h4>{t.thankYou}</h4>
                <p>{t.feedbackSentMsg}</p>
                <button
                  type="button"
                  className="ng-btn-primary"
                  onClick={() => setShowPrivate(false)}
                  style={{ marginTop: '1rem' }}
                >
                  {t.close}
                </button>
              </div>
            ) : (
              <form onSubmit={handlePrivateFeedback} className="ng-private-form">
                {privateError && <p className="warning-box" role="alert">{privateError}</p>}
                <textarea
                  className="ng-textarea"
                  rows={4}
                  placeholder={t.feedbackPlaceholder}
                  value={privateNote}
                  onChange={(e) => setPrivateNote(e.target.value)}
                  required
                  data-gramm="false"
                  data-enable-grammarly="false"
                />
                <input
                  type="text"
                  className="ng-note-input"
                  placeholder={t.contactPlaceholder}
                  value={privateContact}
                  onChange={(e) => setPrivateContact(e.target.value)}
                  style={{ marginTop: '0.75rem' }}
                />
                <div className="ng-modal-actions" style={{ marginTop: '1.25rem' }}>
                  <button type="submit" className="ng-btn-primary" disabled={isSubmittingPrivate}>
                    {isSubmittingPrivate ? t.sending : t.sendToTeam}
                  </button>
                  <button type="button" className="ng-btn-secondary" onClick={() => setShowPrivate(false)}>
                    {t.cancel}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* ════════ CLIPBOARD INFORMATION ════════ */}
      {!cookieConsent && (
        <div className="ng-cookie-bar" role="region" aria-label="Review and clipboard information">
          <div className="ng-cookie-content">
            <span className="ng-cookie-emoji">🍪</span>
            <div className="ng-cookie-msg">
              {t.cookieMsg}
            </div>
          </div>
          <button
            type="button"
            className="ng-cookie-btn"
            onClick={handleAcceptConsent}
          >
            {t.gotIt}
          </button>
        </div>
      )}
    </div>
  );
}
