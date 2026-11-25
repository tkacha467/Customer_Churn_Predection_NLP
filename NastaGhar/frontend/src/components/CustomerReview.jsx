import { useState, useEffect, useRef } from 'react';
import RestaurantWorld from './RestaurantWorld';
import TemplateRenderer from '../templates/TemplateRenderer';
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

export const getLanguageLabel = (l) => {
  if (l === 'hindi') return 'हिन्दी';
  if (l === 'gujarati') return 'ગુજરાતી';
  return 'English';
};

export const APPROVED_GOOGLE_HOSTS = [
  'search.google.com',
  'maps.google.com',
  'www.google.com',
  'google.com',
  'g.page',
  'maps.app.goo.gl',
  'goo.gl',
];

export const isSafeGoogleUrl = (url) => {
  if (!url || typeof url !== 'string') return false;
  try {
    const parsed = new URL(url.trim());
    if (parsed.protocol !== 'https:') return false;
    if (parsed.username || parsed.password) return false;
    if (parsed.port && parsed.port !== '443') return false;
    return APPROVED_GOOGLE_HOSTS.includes(parsed.hostname.toLowerCase());
  } catch {
    return false;
  }
};

export const getStyleLabel = (focus, lang) => {
  const f = String(focus || '').toLowerCase();
  const l = (lang || 'english').toLowerCase();
  if (l.includes('guj')) {
    if (f.includes('short') || f.includes('ટૂંકું')) return 'ટૂંકું અને સ્વાભાવિક';
    if (f.includes('detail') || f.includes('વિગતવાર')) return 'વિગતવાર અને અભિવ્યક્તિપૂર્ણ';
    if (f.includes('simple') || f.includes('person') || f.includes('સરળ')) return 'સરળ અને વ્યક્તિગત';
    return focus || 'વિકલ્પ';
  }
  if (l.includes('hin')) {
    if (f.includes('short') || f.includes('छोटा')) return 'छोटा और स्वाभाविक';
    if (f.includes('detail') || f.includes('विस्तृत')) return 'विस्तृत और स्पष्ट';
    if (f.includes('simple') || f.includes('person') || f.includes('सरल')) return 'सरल और व्यक्तिगत';
    return focus || 'विकल्प';
  }
  if (f.includes('short')) return 'Short & Natural';
  if (f.includes('detail')) return 'Detailed & Expressive';
  if (f.includes('simple') || f.includes('person')) return 'Simple & Personal';
  return focus || 'Option';
};

export const TOPIC_TRANSLATIONS = {
  gujarati: {
    'Breakfast': 'નાસ્તો',
    'Chai & Tea': 'ચા અને પીણાં',
    'Snacks': 'ફરસાણ અને સ્નેક્સ',
    'Taste & Flavour': 'સ્વાદ અને ગુણવત્તા',
    'Friendly Staff': 'સ્ટાફનો વ્યવહાર',
    'Cleanliness': 'સ્વચ્છતા',
    'Value for Money': 'વાજબી ભાવ',
    'Quick Service': 'ઝડપી સર્વિસ',
    'Chai / Coffee': 'ચા / કૉફી',
    'Food & Taste': 'ભોજન અને સ્વાદ',
    'Ambience': 'વાતાવરણ',
    'Sitting Area': 'બેઠક વ્યવસ્થા',
  },
  hindi: {
    'Breakfast': 'नाश्ता',
    'Chai & Tea': 'चाय और पेय',
    'Snacks': 'नाश्ता और स्नैक्स',
    'Taste & Flavour': 'स्वाद और गुणवत्ता',
    'Friendly Staff': 'मिलनसार स्टाफ',
    'Cleanliness': 'साफ़-सफ़ाई',
    'Value for Money': 'किफ़ायती दाम',
    'Quick Service': 'तेज़ सर्विस',
    'Chai / Coffee': 'चाय / कॉफ़ी',
    'Food & Taste': 'खाना और स्वाद',
    'Ambience': 'माहौल',
    'Sitting Area': 'बैठक व्यवस्था',
  },
};

export const getLocalizedTopic = (label, lang) => {
  const l = (lang || 'english').toLowerCase();
  if (l.includes('guj')) {
    return TOPIC_TRANSLATIONS.gujarati[label] || label;
  }
  if (l.includes('hin')) {
    return TOPIC_TRANSLATIONS.hindi[label] || label;
  }
  return label;
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
    howWasVisit: 'आपका अनुभव कैसा रहा?',
    tapStar: 'अपने अनुभव के अनुसार स्टार चुनें',
    continueBtn: 'आगे बढ़ें →',
    ratings: {
      5: { text: 'बहुत पसंद आया!', emoji: '🤩' },
      4: { text: 'काफी अच्छा लगा', emoji: '😊' },
      3: { text: 'ठीक-ठाक रहा', emoji: '🙂' },
      2: { text: 'खास नहीं था', emoji: '😕' },
      1: { text: 'अच्छा नहीं लगा', emoji: '😞' },
    },
    whatStoodOut: 'क्या सबसे अच्छा लगा?',
    pickMatched: 'जो आपकी विज़िट में अच्छा रहा उसे चुनें',
    nothingSpecific: 'कुछ खास नहीं',
    personalNote: 'व्यक्तिगत नोट',
    optional: 'वैकल्पिक',
    notePlaceholder: 'जैसे कि: पोहा बहुत ही स्वादिष्ट था! 😋',
    reviewIdeas: 'समीक्षा के सुझाव',
    tapFavourite: 'पसंदीदा समीक्षा चुनें और गूगल रिव्यू खोलें',
    refiningIdeas: 'सुझाव तैयार हो रहे हैं...',
    useThisReview: 'यह समीक्षा इस्तेमाल करें →',
    writeOwn: '✍️ अपनी खुद की समीक्षा लिखें',
    writeTitle: 'अपनी समीक्षा लिखें',
    chars: 'अक्षर',
    writeSub: 'पोस्ट करने से पहले कुछ भी बदल सकते हैं — यह आपके अपने शब्द हैं!',
    makeNatural: '✨ और स्वाभाविक बनाएं',
    refiningNatural: '✨ सुधार जारी है...',
    backToIdeas: '← वापस सुझावों पर जाएं',
    googleNotice: 'आपकी समीक्षा, आपके शब्द। गूगल पर पेस्ट करके खुद पोस्ट करें।',
    copyAndOpenGoogle: 'कॉपी करें और गूगल रिव्यू खोलें',
    privatePromptGood: 'क्या हमें निजी तौर पर कुछ बताना चाहते हैं? ',
    privatePromptBad: 'क्या टीम को बताना चाहते हैं कि क्या बेहतर हो सकता था? ',
    sendPrivateNote: 'निजी नोट भेजें',
    directNoteTo: 'सीधा संदेश:',
    sharePrivately: 'आप हमारी टीम से निजी तौर पर कुछ भी साझा कर सकते हैं।',
    feedbackPlaceholder: 'अपने विचार, सुझाव या प्रतिक्रिया यहाँ लिखें...',
    contactPlaceholder: 'आपका नाम या संपर्क (वैकल्पिक)',
    sendToTeam: 'टीम को भेजें',
    sending: 'भेजा जा रहा है...',
    cancel: 'रद्द करें',
    close: 'बंद करें',
    thankYou: 'धन्यवाद!',
    feedbackSentMsg: 'आपका संदेश सीधे टीम तक पहुँच गया है।',
    errorRefresh: 'लाइव सुझाव लोड नहीं हो सके। दोबारा कोशिश करें या अपनी समीक्षा लिखें।',
    retry: '🔄 दोबारा कोशिश करें',
    retrying: 'प्रयास जारी है...',
    cookieMsg: 'समीक्षा चुनने पर क्लिपबोर्ड पर कॉपी हो जाएगी। गूगल पर पेस्ट करके सबमिट करें।',
    gotIt: 'समझ गया ✓',
  },
  gujarati: {
    howWasVisit: 'તમારો અનુભવ કેવો રહ્યો?',
    tapStar: 'તમારા અનુભવ મુજબ સ્ટાર પસંદ કરો',
    continueBtn: 'આગળ વધો →',
    ratings: {
      5: { text: 'ખૂબ જ સરસ!', emoji: '🤩' },
      4: { text: 'ખૂબ ગમ્યું', emoji: '😊' },
      3: { text: 'ઠીક-ઠાક રહ્યું', emoji: '🙂' },
      2: { text: 'ખાસ ન હતું', emoji: '😕' },
      1: { text: 'સંતોષ ન થયો', emoji: '😞' },
    },
    whatStoodOut: 'શું સૌથી વધુ ગમ્યું?',
    pickMatched: 'તમારી મુલાકાત સાથે મેળ ખાતી બાબતો પસંદ કરો',
    nothingSpecific: 'ખાસ કંઈ નહીં',
    personalNote: 'વ્યક્તિગત નોંધ',
    optional: 'વૈકલ્પિક',
    notePlaceholder: 'જેમ કે: પૌંઆ ખૂબ જ સ્વાદિષ્ટ હતા! 😋',
    reviewIdeas: 'સમીક્ષાના સૂચનો',
    tapFavourite: 'તમારા મનપસંદ રિવ્યુ પર ટૅપ કરીને ગૂગલ રિવ્યુ ખોલો',
    refiningIdeas: 'સૂચનો તૈયાર થઈ રહ્યા છે...',
    useThisReview: 'આ સમીક્ષા વાપરો →',
    writeOwn: '✍️ તમારી પોતાની સમીક્ષા લખો',
    writeTitle: 'તમારી સમીક્ષા લખો',
    chars: 'અક્ષરો',
    writeSub: 'પોસ્ટ કરતાં પહેલાં કંઈ પણ બદલી શકો છો — આ તમારા પોતાના શબ્દો છે!',
    makeNatural: '✨ વધુ સ્વાભાવિક બનાવો',
    refiningNatural: '✨ સુધારી રહ્યા છીએ...',
    backToIdeas: '← પાછા સૂચનો પર જાઓ',
    googleNotice: 'તમારી સમીક્ષા, તમારા શબ્દો. ગૂગલ પર પેસ્ટ કરીને જાતે પોસ્ટ કરો.',
    copyAndOpenGoogle: 'કૉપિ કરીને ગૂગલ રિવ્યુ ખોલો',
    privatePromptGood: 'શું અમને ખાનગીમાં કંઈ જણાવવા માંગો છો? ',
    privatePromptBad: 'શું ટીમ સાથે શેર કરવા માંગો છો કે શું વધુ સારું થઈ શક્યું હોત? ',
    sendPrivateNote: 'ખાનગી નોંધ મોકલો',
    directNoteTo: 'સીધી નોંધ:',
    sharePrivately: 'તમે અમારી ટીમ સાથે ખાનગીમાં કંઈ પણ શેર કરી શકો છો.',
    feedbackPlaceholder: 'તમારા વિચારો, સૂચનો કે અન્ય કોઈ બાબત અહીં લખો...',
    contactPlaceholder: 'તમારું નામ અથવા સંપર્ક (વૈકલ્પિક)',
    sendToTeam: 'ટીમને મોકલો',
    sending: 'મોકલાઈ રહ્યું છે...',
    cancel: 'રદ કરો',
    close: 'બંધ કરો',
    thankYou: 'આભાર!',
    feedbackSentMsg: 'તમારો સંદેશો સીધો ટીમ સુધી પહોંચી ગયો છે.',
    errorRefresh: 'લાઇવ સૂચનો લોડ થઈ શક્યા નથી. ફરી પ્રયાસ કરો અથવા તમારી પોતાની સમીક્ષા લખો.',
    retry: '🔄 ફરી પ્રયાસ કરો',
    retrying: 'પ્રયાસ ચાલુ છે...',
    cookieMsg: 'સમીક્ષા પસંદ કરતાં જ ક્લિપબોર્ડ પર કૉપિ થઈ જશે. ગૂગલ પર પેસ્ટ કરીને સબમિટ કરો.',
    gotIt: 'સમજી ગયા ✓',
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
const getFallbackIdeas = (r, note = '', lang = 'english', bizName = '', aspects = [], indId = '') => {
  const noteFragment = note && note.trim() ? ` ${note.trim().replace(/[.!]+$/, '')}.` : '';
  const l = (lang || 'english').toLowerCase();

  // Clean business name to never show raw default_business placeholder
  let name = (bizName || '').trim();
  if (!name || name === 'default_business' || name === 'default' || name === 'nasta_ghar' || name === 'nasta-ghar') {
    if (l.includes('guj')) name = 'નાસ્તા ઘર';
    else if (l.includes('hin')) name = 'नाश्ता घर';
    else name = BRAND.name;
  } else if (name === 'Nasta Ghar' || name === 'NastaGhar') {
    if (l.includes('guj')) name = 'નાસ્તા ઘર';
    else if (l.includes('hin')) name = 'नाश्ता घर';
  }

  const isRestaurant = indId === 'restaurant' || indId === 'dining' || indId === 'ind_restaurant' ||
    (!indId && (name === 'Nasta Ghar' || name === 'નાસ્તા ઘર' || name === 'नाश्ता घर'));

  if (!isRestaurant) {
    let shortText = '';
    let detailedText = '';
    let personalText = '';

    const aspectStrEn = aspects && aspects.length > 0 ? aspects.slice(0, 2).join(' & ') : 'service';
    const aspectStrHi = aspects && aspects.length > 0 ? aspects.slice(0, 2).join(' और ') : 'सर्विस';
    const aspectStrGu = aspects && aspects.length > 0 ? aspects.slice(0, 2).join(' અને ') : 'સર્વિસ';

    if (l.includes('hin')) {
      if (r === 5) {
        shortText = `${name} ka anubhav bahut hi accha raha!${noteFragment} ${aspectStrHi} bahut badiya lagi 😊✨`;
        detailedText = `${name} ki ${aspectStrHi} aur arrangements bahut lajawab the.${noteFragment} Sab kuch acche se manage kiya hua tha 👍`;
        personalText = `Personal taur par ${name} ka experience kaafi shandar raha.${noteFragment} Very satisfied with the visit ❤️`;
      } else if (r === 4) {
        shortText = `${name} me accha anubhav raha.${noteFragment} Acchi ${aspectStrHi} aur support 👍`;
        detailedText = `Overall experience kaafi accha aur professional raha at ${name}.${noteFragment} Satisfied with today's visit 🙂`;
        personalText = `Mere liye ${name} ka visit accha raha.${noteFragment} Everything went smoothly 👍`;
      } else if (r === 3) {
        shortText = `Aaj ${name} ka anubhav thik-thak raha.${noteFragment} Normal visit 🙂`;
        detailedText = `Overall average experience tha at ${name}.${noteFragment} Kuch cheezon me sudhar ki gunjaish hai 🙂`;
        personalText = `Mera experience at ${name} standard raha.${noteFragment} Decent experience overall 🙂`;
      } else if (r === 2) {
        shortText = `Aaj ${name} ka anubhav ummeed se kam raha.${noteFragment} 😕`;
        detailedText = `${name} ka visit satisfactory nahi raha.${noteFragment} Kafi cheezon par dhyan dene ki zaroorat hai 😕`;
        personalText = `Mujhe aaj ${name} ka experience pasand nahi aaya.${noteFragment} Needs improvement 😕`;
      } else {
        shortText = `Aaj ${name} me bahut kharab anubhav raha.${noteFragment} 😞`;
        detailedText = `${name} me aaj ka visit bilkul accha nahi raha.${noteFragment} Service aur quality dono me bada sudhar chahiye 😞`;
        personalText = `Mujhe aaj ${name} me bilkul accha anubhav nahi mila.${noteFragment} Highly dissatisfied 😞`;
      }
    } else if (l.includes('guj')) {
      if (r === 5) {
        shortText = `Khub j saras anubhav rahyo at ${name}!${noteFragment} ${aspectStrGu} khub gami ✨`;
        detailedText = `${name} ni mulakat khub shandar rahi.${noteFragment} ${aspectStrGu} ane vyavastha khub saras hati 😊`;
        personalText = `Mane ${name} no anubhav khub j pasand aavyo.${noteFragment} Khub santosh thayo ❤️`;
      } else if (r === 4) {
        shortText = `Saras anubhav rahyo at ${name}.${noteFragment} ${aspectStrGu} barabar hatu 👍`;
        detailedText = `${name} ni mulakat ekandare sari rahi.${noteFragment} Santoshjanak anubhav 🙂`;
        personalText = `Mane ${name} ni service pasand avi.${noteFragment} Overall good visit 👍`;
      } else if (r === 3) {
        shortText = `Aaj no anubhav at ${name} thik-thak rahyo.${noteFragment} Sadharan mulakat 🙂`;
        detailedText = `${name} ni mulakat ekandare average rahi.${noteFragment} Sudhara ni jarur chhe 🙂`;
        personalText = `Mane ${name} no anubhav average lagyo.${noteFragment} Normal experience 🙂`;
      } else if (r === 2) {
        shortText = `Aaj ni mulakat at ${name} apeksha karata ochhi rahi.${noteFragment} 😕`;
        detailedText = `${name} ni mulakat santoshjanak na rahi.${noteFragment} Dhyan aapvani jarur chhe 😕`;
        personalText = `Mane aaj no anubhav at ${name} pasand na aavyo.${noteFragment} 😕`;
      } else {
        shortText = `Aaj no anubhav at ${name} khub kharab rahyo.${noteFragment} 😞`;
        detailedText = `${name} ni mulakat bilkul sari na rahi.${noteFragment} Motu sudhar jaruri chhe 😞`;
        personalText = `Mane aaj no anubhav at ${name} bilkul pasand na aavyo.${noteFragment} 😞`;
      }
    } else {
      if (r === 5) {
        shortText = `Excellent experience with ${name}!${noteFragment} Thoroughly impressed with the ${aspectStrEn} ✨`;
        detailedText = `Everything was handled smoothly and professionally at ${name}.${noteFragment} The ${aspectStrEn} was great and well managed 😊`;
        personalText = `A truly wonderful experience at ${name}.${noteFragment} Very pleased with the visit 👍`;
      } else if (r === 4) {
        shortText = `Good experience at ${name}.${noteFragment} Solid ${aspectStrEn} and reliable support 👍`;
        detailedText = `Overall a solid and enjoyable experience at ${name}.${noteFragment} Happy with the visit 😊`;
        personalText = `Had a good visit at ${name}.${noteFragment} Satisfied with my experience overall 👍`;
      } else if (r === 3) {
        shortText = `Decent visit today at ${name}.${noteFragment} Standard experience 🙂`;
        detailedText = `Overall an average experience at ${name}. A few good points, but there is room for improvement.${noteFragment} Decent visit 🙂`;
        personalText = `It was a pretty average visit for me at ${name}.${noteFragment} Fair experience overall 🙂`;
      } else if (r === 2) {
        shortText = `Experience fell below expectations today at ${name}.${noteFragment} 😕`;
        detailedText = `Somewhat disappointed with the visit at ${name}.${noteFragment} Several areas need attention and better care 😕`;
        personalText = `Expected a better experience than what I had at ${name} today.${noteFragment} Hope to see improvements 😕`;
      } else {
        shortText = `Very disappointing experience today at ${name}.${noteFragment} 😞`;
        detailedText = `Extremely unsatisfied with today's visit at ${name}.${noteFragment} Major improvements are needed in service and quality 😞`;
        personalText = `Really unhappy with the experience today.${noteFragment} Disappointed with how things were handled at ${name} 😞`;
      }
    }

    return [
      { id: 'opt1', focus: getStyleLabel('Short & Natural', lang), text: shortText },
      { id: 'opt2', focus: getStyleLabel('Detailed & Expressive', lang), text: detailedText },
      { id: 'opt3', focus: getStyleLabel('Simple & Personal', lang), text: personalText },
    ];
  }

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
    topicHi = 'नाश्ता और चाय';
    topicGu = 'નાસ્તો અને ચા';
  } else if (hasBreakfast) {
    topicEn = 'breakfast';
    topicHi = 'नाश्ता';
    topicGu = 'નાસ્તો';
  } else if (hasCoffee) {
    topicEn = 'coffee and tea';
    topicHi = 'चाय और कॉफ़ी';
    topicGu = 'ચા અને કૉફી';
  } else if (hasFood) {
    topicEn = 'food';
    topicHi = 'स्वादिष्ट भोजन';
    topicGu = 'સ્વાદિષ્ટ વાનગીઓ';
  } else if (hasService) {
    topicEn = 'service';
    topicHi = 'સર્વિસ';
    topicGu = 'સર્વિસ';
  } else if (hasAmbience) {
    topicEn = 'atmosphere';
    topicHi = 'माहौल';
    topicGu = 'વાતાવરણ';
  } else if (hasClean) {
    topicEn = 'seating area and cleanliness';
    topicHi = 'बैठक व्यवस्था और साफ़-सफ़ाई';
    topicGu = 'બેઠક વ્યવસ્થા અને સ્વચ્છતા';
  }

  let shortText = '';
  let detailedText = '';
  let personalText = '';

  if (l.includes('guj')) {
    if (r === 5) {
      if (topicGu) {
        shortText = `${name}માં ${topicGu} ખૂબ જ સરસ હતાં!${noteFragment} ખૂબ મજા આવી ગઈ 🍳☕`;
        detailedText = `${name}માં ${topicGu}નો અનુભવ ખરેખર લાજવાબ રહ્યો.${noteFragment} બધી વ્યવસ્થા એકદમ ઉત્તમ હતી 😊✨`;
        personalText = `મને ${name}માં ${topicGu} ખૂબ જ પસંદ આવ્યા.${noteFragment} મુલાકાતથી ઘણો આનંદ થયો ❤️`;
      } else {
        shortText = `${name}માં ખૂબ જ સરસ અનુભવ રહ્યો!${noteFragment} ખૂબ મજા આવી ગઈ 😊✨`;
        detailedText = `સમગ્ર મુલાકાત ${name} ખાતે ઘણી શાનદાર રહી.${noteFragment} બધી વ્યવસ્થા એકદમ સુવ્યવસ્થિત હતી 👍`;
        personalText = `મને ${name}ની મુલાકાત ખૂબ જ ગમી.${noteFragment} ખરેખર સંતોષકારક અનુભવ રહ્યો ❤️`;
      }
    } else if (r === 4) {
      if (topicGu) {
        shortText = `${name}માં ${topicGu} સરસ હતાં.${noteFragment} સારો અનુભવ રહ્યો 👍`;
        detailedText = `${name}માં ${topicGu}નો અનુભવ એકંદરે ઘણો સારો રહ્યો.${noteFragment} વ્યવસ્થા સારી લાગી 🙂`;
        personalText = `મને ${name}માં ${topicGu} ગમ્યા.${noteFragment} એકંદરે સારો સમય રહ્યો 👍`;
      } else {
        shortText = `${name}માં સારો અનુભવ રહ્યો.${noteFragment} બધું બરાબર હતું 👍`;
        detailedText = `${name}ની મુલાકાત એકંદરે ઘણી સારી રહી.${noteFragment} સંતોષકારક વ્યવસ્થા હતી 🙂`;
        personalText = `મને ${name}ની મુલાકાત સારી લાગી.${noteFragment} એકંદરે સારો સમય પસાર થયો 👍`;
      }
    } else if (r === 3) {
      if (topicGu) {
        shortText = `${name}માં ${topicGu} સામાન્ય રહ્યાં.${noteFragment} ઠીક મુલાકાત હતી 🙂`;
        detailedText = `${name}માં ${topicGu} ઠીક હતાં, પણ થોડા સુધારાની જરૂર જણાય છે.${noteFragment} સરેરાશ અનુભવ 🙂`;
        personalText = `મારા માટે ${name}માં ${topicGu}નો અનુભવ સરેરાશ રહ્યો.${noteFragment} સામાન્ય વિઝિટ 🙂`;
      } else {
        shortText = `આજનો અનુભવ ${name} ખાતે ઠીક-ઠાક રહ્યો.${noteFragment} સામાન્ય મુલાકાત રહી 🙂`;
        detailedText = `એકંદરે મુલાકાત ${name} ખાતે સામાન્ય રહી.${noteFragment} થોડા સુધારાની જરૂર છે 🙂`;
        personalText = `મારા માટે ${name}નો અનુભવ સામાન્ય રહ્યો.${noteFragment} સાધારણ મુલાકાત 🙂`;
      }
    } else if (r === 2) {
      if (topicGu) {
        shortText = `${name}માં ${topicGu} અપેક્ષા કરતાં ઓછા રહ્યાં.${noteFragment} 😕`;
        detailedText = `${name}માં ${topicGu}થી થોડી નિરાશા થઈ.${noteFragment} સુધારો કરવો જરૂરી છે 😕`;
        personalText = `મને ${name}માં ${topicGu} માટે આવી અપેક્ષા નહોતી.${noteFragment} 😕`;
      } else {
        shortText = `આજે ${name}માં અનુભવ સારો ન રહ્યો.${noteFragment} 😕`;
        detailedText = `${name}ની મુલાકાતથી નિરાશા થઈ.${noteFragment} સર્વિસ અને સંભાળમાં સુધારાની જરૂર છે 😕`;
        personalText = `મને ${name}માં આવી અપેક્ષા નહોતી.{noteFragment} 😕`;
      }
    } else {
      if (topicGu) {
        shortText = `${name}માં ${topicGu}નો અનુભવ ઘણો ખરાબ રહ્યો.${noteFragment} 😞`;
        detailedText = `${name}માં ${topicGu}થી બિલકુલ સંતોષ ન થયો.${noteFragment} મોટા સુધારાની જરૂર છે 😞`;
        personalText = `${name}માં ${topicGu}થી ખૂબ જ નિરાશાજનક મુલાકાત રહી.${noteFragment} 😞`;
      } else {
        shortText = `${name}માં આજનો અનુભવ ખૂબ ખરાબ રહ્યો.${noteFragment} 😞`;
        detailedText = `આજે ${name}ની મુલાકાતથી બિલકુલ સંતોષ ન થયો.${noteFragment} મોટા સુધારાની તાતી જરૂર છે 😞`;
        personalText = `${name} ખાતે આજની મુલાકાત ઘણી નિરાશાજનક રહી.${noteFragment} 😞`;
      }
    }
  } else if (l.includes('hin')) {
    if (r === 5) {
      if (topicHi) {
        shortText = `${name} में ${topicHi} बहुत पसंद आया!${noteFragment} मज़ा आ गया 🍳☕`;
        detailedText = `${name} में ${topicHi} का अनुभव वाकई लाजवाब रहा।${noteFragment} सब कुछ बहुत अच्छे से व्यवस्थित था 😊✨`;
        personalText = `व्यक्तिगत रूप से ${name} में ${topicHi} बहुत अच्छा लगा।${noteFragment} विज़िट से बहुत खुशी हुई ❤️`;
      } else {
        shortText = `बहुत ही अच्छा अनुभव रहा ${name} में!${noteFragment} मज़ा आ गया 😊✨`;
        detailedText = `समग्र विज़िट ${name} में काफी शानदार रही।${noteFragment} व्यवस्था बहुत अच्छी थी 👍`;
        personalText = `मुझे ${name} की विज़िट बहुत पसंद आई।${noteFragment} काफी सुखद अनुभव रहा ❤️`;
      }
    } else if (r === 4) {
      if (topicHi) {
        shortText = `${name} में ${topicHi} काफी अच्छा था।${noteFragment} अच्छा अनुभव रहा 👍`;
        detailedText = `${name} में ${topicHi} का अनुभव काफी सुखद रहा।${noteFragment} सब कुछ बढ़िया था 🙂`;
        personalText = `मुझे ${name} में ${topicHi} पसंद आया।${noteFragment} एक अच्छी विज़िट रही 👍`;
      } else {
        shortText = `काफी अच्छा अनुभव रहा ${name} में।${noteFragment} अच्छा लगा 👍`;
        detailedText = `कुल मिलाकर ${name} की विज़िट अच्छी रही।${noteFragment} व्यवस्था ठीक रही 🙂`;
        personalText = `मुझे ${name} की विज़िट पसंद आई।${noteFragment} बढ़िया समय बीता 👍`;
      }
    } else if (r === 3) {
      if (topicHi) {
        shortText = `${name} में ${topicHi} ठीक-ठाक रहा।${noteFragment} सामान्य अनुभव 🙂`;
        detailedText = `${name} में ${topicHi} औसत रहा।${noteFragment} थोड़े और सुधार की गुंजाइश है 🙂`;
        personalText = `मेरे लिए ${name} में ${topicHi} साधारण रहा।${noteFragment} सामान्य विज़िट 🙂`;
      } else {
        shortText = `आज ${name} का अनुभव सामान्य रहा।${noteFragment} ठीक-ठाक विज़िट 🙂`;
        detailedText = `कुल मिलाकर ${name} का अनुभव औसत रहा।${noteFragment} कुछ सुधार हो सकता है 🙂`;
        personalText = `मेरे लिए ${name} की विज़िट साधारण रही।${noteFragment} ठीक अनुभव रहा 🙂`;
      }
    } else if (r === 2) {
      if (topicHi) {
        shortText = `${name} में ${topicHi} उम्मीद के मुताबिक नहीं था।${noteFragment} 😕`;
        detailedText = `${name} में ${topicHi} से थोड़ी निराशा हुई।${noteFragment} सुधार की ज़रूरत है 😕`;
        personalText = `मुझे ${name} में ${topicHi} से ऐसी उम्मीद नहीं थी।${noteFragment} 😕`;
      } else {
        shortText = `आज ${name} का अनुभव उम्मीद से कम रहा।${noteFragment} 😕`;
        detailedText = `${name} की विज़िट से थोड़ी निराशा हुई।${noteFragment} सर्विस में सुधार की ज़रूरत है 😕`;
        personalText = `मुझे ऐसी उम्मीद नहीं थी ${name} में।${noteFragment} 😕`;
      }
    } else {
      if (topicHi) {
        shortText = `${name} में ${topicHi} का अनुभव खराब रहा।${noteFragment} 😞`;
        detailedText = `${name} में ${topicHi} से बिल्कुल संतुष्ट नहीं हुए।${noteFragment} बड़े सुधार की ज़रूरत है 😞`;
        personalText = `${name} में ${topicHi} से काफी निराशाजनक अनुभव रहा।${noteFragment} 😞`;
      } else {
        shortText = `आज ${name} में खराब अनुभव रहा।${noteFragment} 😞`;
        detailedText = `आज ${name} की विज़िट से बिल्कुल संतुष्ट नहीं हुए।${noteFragment} बड़े सुधार की ज़रूरत है 😞`;
        personalText = `${name} में आज का अनुभव काफी निराशाजनक रहा।${noteFragment} 😞`;
      }
    }
  } else {
    // English
    if (r === 5) {
      if (topicEn) {
        shortText = `Really enjoyed the ${topicEn} at ${name}!${noteFragment} Loved it 🍳☕`;
        detailedText = `Had a lovely visit at ${name}. The ${topicEn} was wonderful and prepared nicely.${noteFragment} Truly enjoyed it 😊✨`;
        personalText = `The ${topicEn} at ${name} was delicious today.${noteFragment} Very happy with my visit ❤️`;
      } else {
        shortText = `Had a wonderful visit at ${name}! Really enjoyed every moment.${noteFragment} Loved it 😊✨`;
        detailedText = `Had a lovely and wonderful visit at ${name}. Everything was handled nicely.${noteFragment} Truly enjoyed it 👍`;
        personalText = `I genuinely enjoyed my time at ${name}.${noteFragment} Very happy with my visit ❤️`;
      }
    } else if (r === 4) {
      if (topicEn) {
        shortText = `Good ${topicEn} at ${name}.${noteFragment} Nice visit 👍`;
        detailedText = `Solid and enjoyable experience with the ${topicEn} at ${name}.${noteFragment} Well managed throughout 😊`;
        personalText = `Had a good experience with the ${topicEn} at ${name}.${noteFragment} Happy with my visit overall 👍`;
      } else {
        shortText = `Very pleasant visit at ${name}.${noteFragment} Good spot to stop by 👍`;
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
        shortText = `Very disappointing experience with the ${topicEn} at ${name}.${noteFragment} 😞`;
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
    { id: 'opt1', focus: getStyleLabel('Short & Natural', lang), text: shortText },
    { id: 'opt2', focus: getStyleLabel('Detailed & Expressive', lang), text: detailedText },
    { id: 'opt3', focus: getStyleLabel('Simple & Personal', lang), text: personalText },
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

  const isDefaultTenant = businessId === 'default_business' || businessId === 'nasta_ghar';
  const formatInitialName = (id) => {
    if (!id || id === 'default_business' || id === 'nasta_ghar') {
      return language === 'gujarati' ? 'નાસ્તા ઘર' : language === 'hindi' ? 'नाश्ता घर' : BRAND.name;
    }
    return id.replace(/[-_]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  };

  // Business Category & Dynamic Branding
  const [businessName, setBusinessName] = useState(() => (isDefaultTenant ? (language === 'gujarati' ? 'નાસ્તા ઘર' : language === 'hindi' ? 'नाश्ता घर' : BRAND.name) : formatInitialName(businessId)));
  const [primaryAccent, setPrimaryAccent] = useState('#f97316');
  const [businessDescription, setBusinessDescription] = useState('');
  const [businessCategory, setBusinessCategory] = useState(isDefaultTenant ? 'Breakfast & Snacks' : '');
  const [industryId, setIndustryId] = useState(isDefaultTenant ? 'restaurant' : '');
  const [terminology, setTerminology] = useState(null);
  const [isRestricted, setIsRestricted] = useState(false);
  const [restrictionMessage, setRestrictionMessage] = useState('');
  const [notFound, setNotFound] = useState(false);
  const [notFoundId, setNotFoundId] = useState('');
  const [templateData, setTemplateData] = useState(null);
  const [loadingConfig, setLoadingConfig] = useState(true);

  // Topics
  const [availableTopics, setAvailableTopics] = useState(isDefaultTenant ? DEFAULT_TOPICS : []);
  const [selectedTopics, setSelectedTopics] = useState(() => (Array.isArray(initialDraft?.selectedTopics) ? initialDraft.selectedTopics : (isDefaultTenant ? ['Breakfast', 'Chai & Tea'] : [])));
  const [nothingSpecific, setNothingSpecific] = useState(() => Boolean(initialDraft?.nothingSpecific));
  const [personalNote, setPersonalNote] = useState(() => initialDraft?.personalNote || '');

  // Keep Google Maps pointed at the restaurant's selected destination.
  const [googleReviewUrl, setGoogleReviewUrl] = useState(BRAND.googleMapUrl);

  // Ideas initialized with fallback ideas (no empty screen, instant feedback)
  const [ideas, setIdeas] = useState(() => getFallbackIdeas(
    rating,
    personalNote,
    language,
    isDefaultTenant ? BRAND.name : formatInitialName(businessId),
    nothingSpecific ? [] : (Array.isArray(initialDraft?.selectedTopics) ? initialDraft.selectedTopics : (isDefaultTenant ? ['Breakfast', 'Chai & Tea'] : [])),
    isDefaultTenant ? 'restaurant' : ''
  ));
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
  const [previewToken, setPreviewToken] = useState(() => urlParams.get('preview_token') || '');
  const [trafficSource, setTrafficSource] = useState('customer');

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
    setLoadingConfig(true);
    setNotFound(false);
    setIsRestricted(false);
    setRestrictionMessage('');

    apiFetch(`/api/public/businesses/${encodeURIComponent(businessId)}/config`)
      .then(async (r) => {
        if (r.ok) return r.json();
        // Fallback to legacy endpoint if public config not yet provisioned
        const legacy = await apiFetch(`/api/businesses/${encodeURIComponent(businessId)}/review-link`);
        if (!legacy.ok) {
          if (legacy.status === 404 || legacy.status === 422) {
            if (active) {
              setNotFound(true);
              setNotFoundId(businessId);
            }
            return null;
          }
          if (r.status === 403) {
            const errData = await r.json().catch(() => ({}));
            if (active) {
              setIsRestricted(true);
              setRestrictionMessage(errData?.detail || 'This review service is currently unavailable for this business category.');
            }
            return null;
          }
          throw new Error('Config load failed');
        }
        return legacy.json();
      })
      .then((d) => {
        if (!d || !active) return;
        setTemplateData(d);
        const rawName = (d.businessName || d.business_name || '').trim();
        const isSlugOrPlaceholder = !rawName || rawName === 'default_business' || rawName === 'default' || rawName === 'nasta_ghar';
        const resolvedName = !isSlugOrPlaceholder
          ? rawName
          : (businessId === 'default_business' || businessId === 'nasta_ghar'
              ? (language === 'gujarati' ? 'નાસ્તા ઘર' : language === 'hindi' ? 'नाश्ता घर' : BRAND.name)
              : (d.category ? (language === 'gujarati' ? `આ ${d.category}` : language === 'hindi' ? `इस ${d.category}` : `The ${d.category}`) : 'Review Assistant'));
        setBusinessName(resolvedName);
        const rUrl = d.googleReviewUrl || d.review_url;
        if (rUrl && isSafeGoogleUrl(rUrl)) {
          setGoogleReviewUrl(rUrl);
        } else if (rUrl) {
          setGoogleReviewUrl(BRAND.googleMapUrl);
        }
        if (d.category) setBusinessCategory(d.category);
        const resolvedIndSlug = d.industry?.slug || d.industry_id || 'restaurant';
        setIndustryId(resolvedIndSlug);
        if (d.terminology) setTerminology(d.terminology);
        const accent = d.theme?.primaryAccent || d.primary_accent;
        if (accent) setPrimaryAccent(accent);
        if (d.description) setBusinessDescription(d.description);
        if (d.topics && d.topics.length > 0) {
          const enriched = d.topics.map((item) => {
            if (typeof item === 'object' && item.label) {
              return { label: item.label, icon: item.icon || getTopicIcon(item.label, resolvedIndSlug) };
            }
            return { label: item, icon: getTopicIcon(item, resolvedIndSlug) };
          });
          setAvailableTopics(enriched);
          const currentDraft = loadDraft(businessId);
          if (!currentDraft?.selectedTopics) {
            const initialLabels = enriched.slice(0, 2).map((t) => t.label);
            setSelectedTopics(initialLabels);
            saveDraft(businessId, { selectedTopics: initialLabels });
          }
        }
        setIdeas(getFallbackIdeas(rating, personalNote, language, resolvedName, nothingSpecific ? [] : selectedTopics, resolvedIndSlug));
      })
      .catch(() => {
        if (businessId === 'default_business' || businessId === 'nasta_ghar') {
          if (active) setBusinessName(BRAND.name);
        }
      })
      .finally(() => {
        if (active) setLoadingConfig(false);
      });

    // Acquire server-authenticated preview token if operating in preview mode
    if (isPreviewMode && !previewToken) {
      apiFetch(`/api/reviews/preview-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ business_id: businessId }),
      })
        .then((r) => (r.ok ? r.json() : null))
        .then((d) => {
          if (active && d?.preview_token) {
            setPreviewToken(d.preview_token);
            if (d.traffic_source) setTrafficSource(d.traffic_source);
          }
        })
        .catch(() => {});
    }

    // Initialize session with server-verified preview context
    const sessionHeaders = { 'Content-Type': 'application/json' };
    if (previewToken) {
      sessionHeaders['X-Preview-Token'] = previewToken;
    }

    apiFetch(`/api/reviews/session`, {
      method: 'POST',
      headers: sessionHeaders,
      body: JSON.stringify({
        business_id: businessId,
        table_number: tableParam || 'Walk-in',
        dining_type: 'dine_in',
        preview_token: previewToken || undefined,
        is_preview: isPreviewMode,
      }),
    })
      .then((r) => r.json())
      .then((d) => {
        if (active) {
          setSessionId(d.session_id);
          if (d.traffic_source) setTrafficSource(d.traffic_source);
          if (d.preview_token && !previewToken) setPreviewToken(d.preview_token);
        }
      })
      .catch(() => { if (active) setSessionId(`local-${Date.now()}`); });

    return () => { active = false; };
  }, [businessId, tableParam, isPreviewMode, previewToken]);

  function getTopicIcon(label, currentIndustryId = 'restaurant') {
    const l = (label || '').toLowerCase();
    // Hospitality / Restaurant
    if (l.includes('breakfast') || l.includes('nasta')) return '🍳';
    if (l.includes('chai') || l.includes('tea') || l.includes('coffee') || l.includes('drink') || l.includes('beverage')) return '☕';
    if (l.includes('snack') || l.includes('sandwich')) return '🥪';
    if (l.includes('taste') || l.includes('flavour') || l.includes('flavor') || l.includes('food') || l.includes('meal')) return '😋';
    // Hotel & Accommodation
    if (l.includes('room comfort') || l.includes('room') || l.includes('bed') || l.includes('stay') || l.includes('sleep')) return '🛏️';
    if (l.includes('amenit') || l.includes('pool')) return '🏊';
    if (l.includes('check-in') || l.includes('check in') || l.includes('reception')) return '⚡';
    if (l.includes('location') || l.includes('view')) return '📍';
    // Fitness & Gym
    if (l.includes('equipment') || l.includes('workout') || l.includes('weights')) return '🏋️';
    if (l.includes('trainer') || l.includes('coach') || l.includes('training')) return '👟';
    if (l.includes('locker') || l.includes('shower')) return '🚿';
    if (l.includes('class') || l.includes('yoga') || l.includes('session')) return '🧘';
    // Salon & Personal Care
    if (l.includes('hair') || l.includes('styling') || l.includes('cut') || l.includes('barber')) return '✂️';
    if (l.includes('spa') || l.includes('facial') || l.includes('massage')) return '💆';
    // Retail & Shopping
    if (l.includes('product') || l.includes('shopping') || l.includes('store') || l.includes('collection') || l.includes('merchandise')) return '🛍️';
    if (l.includes('checkout') || l.includes('billing')) return '⚡';
    // Automotive
    if (l.includes('service quality') || l.includes('repair') || l.includes('mechanic') || l.includes('maintenance') || l.includes('workshop')) return '🔧';
    if (l.includes('turnaround') || l.includes('delivery time') || l.includes('wait time') || l.includes('promptness')) return '⏱️';
    if (l.includes('pricing') || l.includes('transparency')) return '💰';
    // Education
    if (l.includes('course') || l.includes('curriculum') || l.includes('syllabus') || l.includes('content') || l.includes('study')) return '📚';
    if (l.includes('instructor') || l.includes('faculty') || l.includes('teacher') || l.includes('mentor')) return '🎓';
    // Events
    if (l.includes('event') || l.includes('party') || l.includes('wedding') || l.includes('gathering')) return '🎉';
    if (l.includes('catering') || l.includes('refreshment') || l.includes('buffet')) return '🍽️';
    // Travel
    if (l.includes('flight') || l.includes('itinerary') || l.includes('tour') || l.includes('trip') || l.includes('travel')) return '✈️';
    if (l.includes('guide') || l.includes('sightseeing')) return '🧭';
    if (l.includes('transport') || l.includes('transit') || l.includes('cab') || l.includes('bus') || l.includes('driver')) return '🚐';
    // General
    if (l.includes('clean') || l.includes('hygiene') || l.includes('tidy')) return '✨';
    if (l.includes('staff') || l.includes('service') || l.includes('friendly') || l.includes('helpfulness') || l.includes('professionalism')) return '😊';
    if (l.includes('value') || l.includes('money') || l.includes('price') || l.includes('cost') || l.includes('affordable')) return '💰';
    if (l.includes('quick') || l.includes('fast') || l.includes('speed') || l.includes('prompt')) return '⚡';
    if (l.includes('atmosphere') || l.includes('vibe') || l.includes('ambience') || l.includes('environment')) return '🌟';
    return '⭐';
  }

  // ─── ANALYTICS (Enforces strict 3-way separation & deduplication) ───────────
  const logEvent = (name, meta = {}) => {
    if (!sessionId) return;
    const eventHeaders = { 'Content-Type': 'application/json' };
    if (previewToken) {
      eventHeaders['X-Preview-Token'] = previewToken;
    }
    apiFetch(`/api/reviews/events`, {
      method: 'POST',
      headers: eventHeaders,
      keepalive: true,
      body: JSON.stringify({
        session_id: sessionId,
        event_name: name,
        preview_token: previewToken || undefined,
        idempotency_key: `${sessionId}-${name}-${meta?.rating || ''}`,
        metadata: {
          business_id: businessId,
          rating,
          is_preview: isPreviewMode,
          traffic_source: trafficSource,
          ...meta,
        },
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
          business_name: businessName || undefined,
          rating,
          aspects: nothingSpecific ? [] : selectedTopics,
          user_note: personalNote.trim(),
          language,
          category: businessCategory,
          industry_id: industryId || undefined,
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
    setIdeas(getFallbackIdeas(rating, personalNote, language, businessName || BRAND.name, nothingSpecific ? [] : selectedTopics, industryId));
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
  }, [rating, selectedTopics, nothingSpecific, personalNote, businessId, language, businessCategory, industryId]);

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
      if (!isSafeGoogleUrl(googleReviewUrl)) {
        console.error('Blocked redirect to unsafe review URL destination:', googleReviewUrl);
        setHandoffOpen(true);
        return;
      }
      logEvent('google_maps_redirect', { destination: googleReviewUrl });
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
          business_name: businessName || undefined,
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
            <span>👁️ {trafficSource === 'internal_admin' ? 'Admin Diagnostic Preview' : 'Owner Preview Mode'}</span>
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

  if (isRestricted) {
    return (
      <div className="ng-page">
        {isPreviewMode && (
          <div className="ng-preview-bar">
            <span>👁️ {trafficSource === 'internal_admin' ? 'Admin Diagnostic Preview' : 'Owner Preview Mode'}</span>
            {onSwitchToOwner && (
              <button type="button" className="ng-preview-back" onClick={onSwitchToOwner}>
                ← Back to Dashboard
              </button>
            )}
          </div>
        )}
        <div className="ng-card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem', margin: '2rem auto', maxWidth: '480px' }}>
          <div style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>🛡️</div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: '700', marginBottom: '0.75rem', color: '#1e293b' }}>
            Service Notice
          </h2>
          <p style={{ color: '#64748b', fontSize: '0.95rem', lineHeight: '1.5', marginBottom: '1.5rem' }}>
            {restrictionMessage || 'Customer review generation is not available for this business category.'}
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

  if (loadingConfig && !templateData) {
    return (
      <div className="vt-page-container" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a', color: '#f8fafc' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="admin-spinner" style={{ width: '40px', height: '40px', margin: '0 auto 16px', border: '3px solid rgba(255,255,255,0.1)', borderTopColor: '#3b82f6', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
          <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>Loading review experience…</p>
        </div>
      </div>
    );
  }

  const getNotePlaceholder = () => {
    if (templateData?.experienceLabels?.notePlaceholder) {
      return templateData.experienceLabels.notePlaceholder;
    }
    const ind = templateData?.industry?.slug || industryId;
    if (ind === 'salon' || ind === 'beauty') {
      return language === 'gujarati' ? 'જેમ કે: હેરકટ અને રિલેક્સિંગ સર્વિસ ખૂબ જ ગમી! ✨' : language === 'hindi' ? 'जैसे: हेयरकट और रिलैक्सिंग सर्विस बहुत पसंद आई! ✨' : 'e.g. Loved the haircut and relaxing service! ✨';
    }
    if (ind === 'retail' || ind === 'shopping') {
      return language === 'gujarati' ? 'જેમ કે: કલેક્શન અને ક્વોલિટી ખૂબ સરસ હતી! 🛍️' : language === 'hindi' ? 'जैसे: कलेक्शन और क्वालिटी बहुत बढ़िया थी! 🛍️' : 'e.g. Great collection and wonderful quality! 🛍️';
    }
    if (ind === 'hotel' || ind === 'hospitality') {
      return language === 'gujarati' ? 'જેમ કે: રૂમ અને સર્વિસ ખૂબ જ સરસ હતી! 🏨' : language === 'hindi' ? 'जैसे: रूम और आतिथ्य बहुत अच्छा था! 🏨' : 'e.g. Comfortable room and welcoming staff! 🏨';
    }
    if (ind === 'fitness' || ind === 'wellness') {
      return language === 'gujarati' ? 'જેમ કે: ટ્રેનર અને વાતાવરણ ખૂબ જ ઉત્સાહવર્ધક છે! 💪' : language === 'hindi' ? 'जैसे: ट्रेनर और माहौल बहुत ऊर्जावान है! 💪' : 'e.g. Great trainer energy and clean equipment! 💪';
    }
    if (ind === 'clinic' || ind === 'healthcare') {
      return language === 'gujarati' ? 'જેમ કે: ડૉક્ટરની સલાહ ખૂબ જ સંતોષકારક રહી! 🩺' : language === 'hindi' ? 'जैसे: डॉक्टर का परामर्श बहुत तसल्लीबख्श रहा! 🩺' : 'e.g. Clear consultation and gentle care! 🩺';
    }
    if (businessId === 'default_business' || businessId === 'nasta_ghar') {
      return t.notePlaceholder; // e.g. The poha was absolutely perfect! 😋
    }
    return language === 'gujarati' ? 'જેમ કે: સ્વાદ અને સર્વિસ ખૂબ સરસ રહી! 🍽️' : language === 'hindi' ? 'जैसे: स्वाद और सर्विस बहुत बढ़िया थी! 🍽️' : 'e.g. Great taste and wonderful service! 🍽️';
  };

  const isLegacyCanvas =
    templateData?.compatibility_flags?.legacy_experience === 'nasta_ghar_canvas_world' ||
    templateData?.theme?.heroBannerType === 'animated_world' ||
    (!templateData?.theme?.heroBannerType && (businessId === 'default_business' || businessId === 'nasta_ghar'));

  if (!isLegacyCanvas && templateData) {
    const journeyState = {
      rating,
      setRating: handleRating,
      hoverRating,
      setHoverRating,
      ratingLabel,
      availableTopics,
      selectedTopics,
      toggleTopic,
      personalNote,
      setPersonalNote: (val) => {
        setPersonalNote(val);
        saveDraft(businessId, { personalNote: val });
      },
      touchpointLabel: terminology?.touchpoint_noun || 'Table',
      touchpointValue: tableParam,
      ideas,
      selectedIdeaId,
      onSelectIdea: (idea) => handlePostDirectly(idea),
      draftReview,
      setDraftReview: (val) => {
        setDraftReview(val);
        saveDraft(businessId, { draftReview: val });
      },
      onDirectGoogleHandoff: handleContinueToGoogle,
      onOpenPrivateFeedback: () => setShowPrivate(true),
      notePlaceholder: getNotePlaceholder(),
      t,
      language,
      loadingIdeas,
      nothingSpecific,
      setNothingSpecific,
    };

    return (
      <div className="vt-dynamic-page-root" style={{ minHeight: '100vh', width: '100%' }}>
        {isPreviewMode && (
          <div className="ng-preview-bar">
            <span>👁️ {trafficSource === 'internal_admin' ? 'Admin Diagnostic Preview' : 'Owner Preview Mode'}</span>
            {onSwitchToOwner && (
              <button type="button" className="ng-preview-back" onClick={onSwitchToOwner}>
                ← Back to Dashboard
              </button>
            )}
          </div>
        )}

        <TemplateRenderer templateData={templateData} journeyState={journeyState} />

        {/* Private Feedback Modal Overlay */}
        {showPrivate && (
          <div className="ng-modal-backdrop" onClick={() => setShowPrivate(false)}>
            <div
              className="ng-modal"
              onClick={(e) => e.stopPropagation()}
              style={{
                background: '#ffffff',
                color: '#1f2937',
                borderRadius: '16px',
                padding: '24px',
                maxWidth: '460px',
                width: '90%',
                margin: 'auto',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#111827' }}>
                  {t.sendPrivateNote}
                </h3>
                <button
                  type="button"
                  className="ng-modal-close"
                  onClick={() => setShowPrivate(false)}
                  style={{ background: 'none', border: 'none', fontSize: '1.2rem', cursor: 'pointer', color: '#6b7280' }}
                >
                  ✕
                </button>
              </div>
              {privateSent ? (
                <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
                  <div style={{ fontSize: '3rem', marginBottom: '0.75rem', color: '#10b981' }}>✓</div>
                  <h4 style={{ margin: '0 0 8px 0', color: '#111827' }}>{t.thankYou}</h4>
                  <p style={{ margin: 0, color: '#4b5563', fontSize: '0.95rem' }}>{t.feedbackSentMsg}</p>
                </div>
              ) : (
                <form onSubmit={handlePrivateFeedback}>
                  <p style={{ color: '#4b5563', fontSize: '0.9rem', marginBottom: '16px' }}>
                    {t.sharePrivately}
                  </p>
                  <textarea
                    rows={4}
                    value={privateNote}
                    onChange={(e) => setPrivateNote(e.target.value)}
                    placeholder={t.feedbackPlaceholder}
                    required
                    style={{
                      width: '100%',
                      boxSizing: 'border-box',
                      borderRadius: '8px',
                      border: '1px solid #d1d5db',
                      padding: '10px 12px',
                      marginBottom: '12px',
                      fontFamily: 'inherit',
                      fontSize: '0.95rem',
                      color: '#1f2937',
                      background: '#ffffff',
                    }}
                  />
                  <input
                    type="text"
                    value={privateContact}
                    onChange={(e) => setPrivateContact(e.target.value)}
                    placeholder={t.contactPlaceholder}
                    style={{
                      width: '100%',
                      boxSizing: 'border-box',
                      borderRadius: '8px',
                      border: '1px solid #d1d5db',
                      padding: '10px 12px',
                      marginBottom: '16px',
                      fontFamily: 'inherit',
                      fontSize: '0.95rem',
                      color: '#1f2937',
                      background: '#ffffff',
                    }}
                  />
                  <button
                    type="submit"
                    disabled={isSubmittingPrivate}
                    className="ng-btn-primary"
                    style={{ width: '100%', padding: '12px', fontWeight: 700 }}
                  >
                    {isSubmittingPrivate ? t.sending : t.sendToTeam}
                  </button>
                </form>
              )}
            </div>
          </div>
        )}

        {/* Floating Copy Toast */}
        {showCopyToast && (
          <div className="ng-toast" role="alert">
            <span className="ng-toast-icon">📋</span>
            <span className="ng-toast-msg">
              {copied
                ? (language === 'hindi'
                    ? 'आपकी समीक्षा कॉपी हो गई है ✓ गूगल मैप्स पर पेस्ट करके सबमिट करें।'
                    : language === 'gujarati'
                    ? 'તમારી સમીક્ષા કૉપિ થઈ ગઈ છે ✓ ગૂગલ મેપ્સ પર પેસ્ટ કરીને સબમિટ કરો.'
                    : 'Review copied to clipboard ✓ Opening Google Maps...')
                : 'Opening Google Maps...'}
            </span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="ng-page">
      {/* Preview Banner */}
      {isPreviewMode && (
        <div className="ng-preview-bar">
          <span>👁️ {trafficSource === 'internal_admin' ? 'Admin Diagnostic Preview' : 'Owner Preview Mode'}</span>
          {onSwitchToOwner && (
            <button type="button" className="ng-preview-back" onClick={onSwitchToOwner}>
              ← Back to Dashboard
            </button>
          )}
        </div>
      )}

      {(() => {
        const heroType = templateData?.theme?.heroBannerType;
        const indSlug = templateData?.industry?.slug || industryId;

        // Signature Gujarati Restaurant Animated World (Nasta Ghar)
        if (heroType === 'animated_world' || (!heroType && (businessId === 'default_business' || businessId === 'nasta_ghar'))) {
          return <RestaurantWorld />;
        }

        // Dynamic Industry Template Hero (Hotel, Salon, Clinic, Fine Dining)
        const badge = templateData?.theme?.badgeText || (
          indSlug === 'hotel' ? 'Hospitality Stay'
          : indSlug === 'fitness' ? 'Fitness & Gym'
          : indSlug === 'salon' ? 'Studio & Spa'
          : indSlug === 'retail' ? 'Retail & Store'
          : indSlug === 'automotive' ? 'Auto Care'
          : indSlug === 'clinic' ? 'Healthcare Care'
          : 'Vraja Experience'
        );
        const icon = templateData?.industry?.icon || (
          indSlug === 'hotel' ? '🏨'
          : indSlug === 'fitness' ? '🏋️'
          : indSlug === 'salon' ? '✂️'
          : indSlug === 'retail' ? '🛍️'
          : indSlug === 'automotive' ? '🔧'
          : indSlug === 'education' ? '🎓'
          : indSlug === 'events' ? '🎉'
          : indSlug === 'travel' ? '✈️'
          : indSlug === 'clinic' ? '🩺'
          : businessCategory.toLowerCase().includes('cafe') ? '☕'
          : '⭐'
        );
        const bg = templateData?.theme?.cardBackground || '#162017';
        const accent = primaryAccent || templateData?.theme?.primaryAccent || '#f97316';

        return (
          <div
            className="ng-scene-wrapper dynamic-industry-hero"
            style={{
              minHeight: '150px',
              background: `linear-gradient(135deg, ${bg} 0%, ${accent}25 100%)`,
              borderBottom: `2px solid ${accent}`,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '22px 16px',
              textAlign: 'center',
            }}
          >
            <span style={{ fontSize: '2.6rem', marginBottom: '8px' }}>{icon}</span>
            <span
              style={{
                display: 'inline-block',
                backgroundColor: accent,
                color: '#ffffff',
                fontSize: '11px',
                fontWeight: '700',
                padding: '3px 10px',
                borderRadius: '9999px',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '6px',
              }}
            >
              {badge}
            </span>
            <span style={{ fontSize: '13px', color: '#94a3b8' }}>
              {templateData?.template?.name || businessCategory || 'Hospitality Review Assistant'}
            </span>
          </div>
        );
      })()}

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
              <p className="ng-brand-sub">{businessDescription || businessCategory || 'Review Assistant'}</p>
            </>
          )}
          {tableParam && (
            <span className="ng-table-pill">
              📍 {terminology?.touchpoint_noun && !tableParam.toLowerCase().includes(terminology.touchpoint_noun.toLowerCase())
                  ? `${terminology.touchpoint_noun} ${tableParam}`
                  : tableParam}
            </span>
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
                      <span>{getLocalizedTopic(label, language)}</span>
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
                  placeholder={
                    industryId === 'restaurant'
                      ? t.notePlaceholder
                      : (language === 'hindi'
                          ? 'Jaise ki prompt service, accha anubhav!'
                          : language === 'gujarati'
                            ? 'Jem ke saras vyavastha, saro anubhav!'
                            : 'e.g. Prompt service, friendly staff, great experience!')
                  }
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
                        <span className="ng-idea-num">{getStyleLabel(idea.focus, language) || `Option ${i + 1}`}</span>
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
                  ? "आपकी समीक्षा कॉपी हो गई है ✓ गूगल मैप्स पर 'Write a review' टैप करें, यही रेटिंग चुनकर समीक्षा पेस्ट करें।"
                  : language === 'gujarati'
                  ? "તમારી સમીક્ષા કૉપિ થઈ ગઈ છે ✓ ગૂગલ મેપ્સ પર 'Write a review' ટૅપ કરો, આ જ રેટિંગ પસંદ કરીને પેસ્ટ કરો."
                  : "Your review is copied ✓ On Google Maps, tap 'Write a review', select the same rating, and paste.")
              : (language === 'hindi'
                  ? "समीक्षा कॉपी नहीं हो सकी। दोबारा प्रयास करने के लिए 'समीक्षा कॉपी करें' पर टैप करें।"
                  : language === 'gujarati'
                  ? "સમીક્ષા કૉપિ થઈ શકી નથી. ફરી પ્રયાસ કરવા માટે 'સમીક્ષા કૉપિ કરો' પર ટૅપ કરો."
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
                ? (language === 'hindi' ? 'समीक्षा तैयार हो रही है…' : language === 'gujarati' ? 'સમીક્ષા તૈયાર થઈ રહી છે…' : 'Preparing your review…')
                : copied
                ? (language === 'hindi' ? 'समीक्षा क्लिपबोर्ड पर कॉपी हो गई ✓' : language === 'gujarati' ? 'સમીક્ષા ક્લિપબોર્ડ પર કૉપિ થઈ ગઈ ✓' : 'Review Copied to Clipboard ✓')
                : (language === 'hindi' ? 'समीक्षा कॉपी करके आगे बढ़ें' : language === 'gujarati' ? 'સમીક્ષા કૉપિ કરીને આગળ વધો' : 'Copy Your Review to Continue')}
            </h3>
            <p className="ng-modal-body">
              {copyingReview ? (
                language === 'hindi' ? (
                  <>आपकी समीक्षा तैयार है। क्लिपबोर्ड पर कॉपी कर रहे हैं और गूगल मैप्स खोल रहे हैं…</>
                ) : language === 'gujarati' ? (
                  <>તમારી સમીક્ષા તૈયાર છે. ક્લિપબોર્ડ પર કૉપિ કરી રહ્યા છીએ અને ગૂગલ મેપ્સ ખોલી રહ્યા છીએ…</>
                ) : (
                  <>Preparing your review. Copying to clipboard and opening Google Maps…</>
                )
              ) : copied ? (
                language === 'hindi' ? (
                  <>
                    आपकी समीक्षा कॉपी हो गई है ✓ आपने यहाँ <strong>{rating}★</strong> चुने हैं। गूगल मैप्स पर <strong>Write a review</strong> पर टैप करें, यही रेटिंग चुनें और समीक्षा पेस्ट करें।
                  </>
                ) : language === 'gujarati' ? (
                  <>
                    તમારી સમીક્ષા કૉપિ થઈ ગઈ છે ✓ તમે અહીં <strong>{rating}★</strong> પસંદ કર્યા છે. ગૂગલ મેપ્સ પર <strong>Write a review</strong> ટૅપ કરો, આ જ રેટિંગ પસંદ કરો અને સમીક્ષા પેસ્ટ કરો.
                  </>
                ) : (
                  <>
                    Your review is copied ✓ You selected <strong>{rating}★</strong> here. On Google Maps, tap <strong>Write a review</strong>, select the same rating, then paste your review.
                  </>
                )
              ) : (
                language === 'hindi' ? (
                  <>
                    समीक्षा कॉपी नहीं हो सकी। नीचे दी गई समीक्षा को कॉपी करें और गूगल मैप्स पर पेस्ट करें (आपने यहाँ <strong>{rating}★</strong> चुने थे)।
                  </>
                ) : language === 'gujarati' ? (
                  <>
                    સમીક્ષા કૉપિ થઈ શકી નથી. નીચે આપેલી સમીક્ષા કૉપિ કરો અને ગૂગલ મેપ્સ પર પેસ્ટ કરો (તમે અહીં <strong>{rating}★</strong> પસંદ કર્યા હતા).
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
                    ? <>गूगल पर वही रेटिंग चुनें जो यहाँ चुनी थी (आपने <strong>{rating} स्टार</strong> चुने हैं)</>
                    : language === 'gujarati'
                    ? <>ગૂગલ પર એ જ રેટિંગ પસંદ કરો જે અહીં પસંદ કર્યું હતું (તમે <strong>{rating} સ્ટાર</strong> પસંદ કર્યા છે)</>
                    : <>Choose the rating that reflects your visit on Google (you selected <strong>{rating} stars</strong> here)</>}
                </span>
              </div>
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">2</span>
                <span>
                  {copyingReview
                    ? (language === 'hindi' ? 'चुनी गई समीक्षा कॉपी हो रही है…' : language === 'gujarati' ? 'પસંદ કરેલી સમીક્ષા કૉપિ થઈ રહી છે…' : 'Copying selected review…')
                    : copied
                    ? (language === 'hindi'
                        ? <>कॉपी की गई समीक्षा को <strong>Paste</strong> करें (स्क्रीन पर देर तक दबाकर Paste करें)</>
                        : language === 'gujarati'
                        ? <>કૉપિ કરેલી સમીક્ષાને <strong>Paste</strong> કરો (સ્ક્રીન પર લોંગ-પ્રેસ કરીને Paste કરો)</>
                        : <><strong>Paste</strong> the copied review (use your device's Paste command, or long-press → Paste on mobile)</>)
                    : (language === 'hindi'
                        ? <>नीचे से समीक्षा कॉपी करें और गूगल पर <strong>Paste</strong> करें</>
                        : language === 'gujarati'
                        ? <>નીચેથી સમીક્ષા કૉપિ કરો અને ગૂગલ પર <strong>Paste</strong> કરો</>
                        : <>Copy the review below, then <strong>paste</strong> it into Google</>)}
                </span>
              </div>
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">3</span>
                <span>
                  {language === 'hindi'
                    ? <>समीक्षा जाँचें और गूगल के <strong>Post</strong> बटन पर टैप करें।</>
                    : language === 'gujarati'
                    ? <>સમીક્ષા તપાસો અને ગૂગલના <strong>Post</strong> બટન પર ટૅપ કરો.</>
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
                  ? (language === 'hindi' ? '📋 दोबारा कॉपी करें' : language === 'gujarati' ? '📋 ફરી કૉપિ કરો' : '📋 Copy Again')
                  : (language === 'hindi' ? '📋 समीक्षा कॉपी करें' : language === 'gujarati' ? '📋 સમીક્ષા કૉપિ કરો' : '📋 Copy Review')}
              </button>
            </div>

            <div className="ng-modal-actions">
              <button
                type="button"
                className="ng-btn-primary"
                disabled={copyingReview}
                onClick={() => {
                  if (!isSafeGoogleUrl(googleReviewUrl)) {
                    console.error('Blocked redirect to unsafe review URL destination:', googleReviewUrl);
                    return;
                  }
                  logEvent('google_maps_redirect', { destination: googleReviewUrl });
                  clearSessionDraft(businessId);
                  window.location.href = googleReviewUrl;
                }}
              >
                {language === 'hindi' ? '↗ गूगल मैप्स खोलें' : language === 'gujarati' ? '↗ ગૂગલ મેપ્સ ખોલો' : '↗ Continue to Google Maps'}
              </button>
              <button
                type="button"
                className="ng-btn-secondary"
                onClick={() => setHandoffOpen(false)}
              >
                {language === 'hindi' ? 'पूर्ण ✓' : language === 'gujarati' ? 'થઈ ગયું ✓' : 'Done ✓'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ════════ PRIVATE FEEDBACK MODAL ════════ */}
      {showPrivate && (
        <div className="ng-modal-backdrop">
          <div className="ng-modal ng-modal-bounce">
            <h3 className="ng-modal-title">
              {terminology?.private_feedback_title
                ? `${terminology.private_feedback_title} — ${businessName || BRAND.name}`
                : `${t.directNoteTo} ${businessName || BRAND.name}`}
            </h3>
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
