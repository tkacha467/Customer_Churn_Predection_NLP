import { useState, useEffect, useRef } from 'react';
import RestaurantWorld from './RestaurantWorld';
import { apiFetch } from '../lib/api';

// ─── NASTA GHAR BRAND CONSTANTS ──────────────────────────────────────────────
// These are hardcoded. The API enriches config but NEVER overrides the name.
const BRAND = {
  name: 'Nasta Ghar',
  googleMapUrl:
    'https://search.google.com/local/writereview?placeid=ChIJZeK7NwDLWTkR1pOxt51jLro',
};

// ─── TRILINGUAL CHOICES ──────────────────────────────────────────────────────
const LANGUAGES = [
  { id: 'english', label: 'English', sub: 'English' },
  { id: 'hindi', label: 'Hindi', sub: 'Hinglish (Roman)' },
  { id: 'gujarati', label: 'Gujarati', sub: 'Gujlish (Roman)' },
];

// ─── HOSPITALITY TOPICS BY CATEGORY ──────────────────────────────────────────
const CATEGORY_TOPICS = {
  cafe: [
    { label: 'Food & Taste', icon: '😋' },
    { label: 'Chai / Coffee', icon: '☕' },
    { label: 'Staff', icon: '😊' },
    { label: 'Service', icon: '⚡' },
    { label: 'Ambience', icon: '🌟' },
    { label: 'Cleanliness', icon: '✨' },
    { label: 'Value for Money', icon: '💰' },
  ],
  restaurant: [
    { label: 'Food & Taste', icon: '😋' },
    { label: 'Service', icon: '⚡' },
    { label: 'Staff', icon: '😊' },
    { label: 'Ambience', icon: '🌟' },
    { label: 'Cleanliness', icon: '✨' },
    { label: 'Portion Size', icon: '🍽️' },
    { label: 'Value for Money', icon: '💰' },
  ],
  hotel: [
    { label: 'Room', icon: '🛏️' },
    { label: 'Cleanliness', icon: '✨' },
    { label: 'Staff', icon: '😊' },
    { label: 'Service', icon: '⚡' },
    { label: 'Breakfast', icon: '🍳' },
    { label: 'Location', icon: '📍' },
    { label: 'Comfort', icon: '✨' },
    { label: 'Ambience', icon: '🌟' },
  ],
  salon: [
    { label: 'Service', icon: '⚡' },
    { label: 'Staff', icon: '😊' },
    { label: 'Cleanliness', icon: '✨' },
    { label: 'Experience', icon: '🌟' },
    { label: 'Results', icon: '✨' },
    { label: 'Ambience', icon: '🌟' },
  ],
  breakfast: [
    { label: 'Breakfast', icon: '🍳' },
    { label: 'Chai & Tea', icon: '☕' },
    { label: 'Snacks', icon: '🥪' },
    { label: 'Taste & Flavour', icon: '😋' },
    { label: 'Friendly Staff', icon: '😊' },
    { label: 'Cleanliness', icon: '✨' },
    { label: 'Value for Money', icon: '💰' },
    { label: 'Quick Service', icon: '⚡' },
  ],
};

const DEFAULT_TOPICS = CATEGORY_TOPICS.breakfast;

function resolveCategoryTopics(category) {
  if (!category) return CATEGORY_TOPICS.breakfast;
  const c = category.toLowerCase();
  if (c.includes('cafe') || c.includes('coffee')) return CATEGORY_TOPICS.cafe;
  if (c.includes('hotel') || c.includes('stay') || c.includes('resort')) return CATEGORY_TOPICS.hotel;
  if (c.includes('salon') || c.includes('spa') || c.includes('parlour')) return CATEGORY_TOPICS.salon;
  if (c.includes('restaurant') || c.includes('dining') || c.includes('bistro')) return CATEGORY_TOPICS.restaurant;
  return CATEGORY_TOPICS.breakfast;
}

const RATING_LABELS = {
  5: { text: 'Loved it!', emoji: '🤩' },
  4: { text: 'Really good', emoji: '😊' },
  3: { text: 'It was okay', emoji: '🙂' },
  2: { text: 'Disappointed', emoji: '😕' },
  1: { text: 'Not good', emoji: '😞' },
};

function getFallbackIdeas(r, note, lang = 'english') {
  const noteText = note && note.trim() ? ` ${note.trim().replace(/[.!]+$/, '')}.` : '';

  if (lang === 'hindi') {
    // ─── HINDI (ROMAN SCRIPT / HINGLISH) ──────────────────────────────
    if (r === 5) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Bahut accha experience raha aur khana sach me lajawab tha!${noteText} Loved it 😊👌`, language: 'hindi' },
        { id: 'opt2', focus: 'Taste & Service', text: `Food ekdum fresh tha aur staff ka nature bhi kaafi polite tha.${noteText} Quick service mili 😋👍`, language: 'hindi' },
        { id: 'opt3', focus: 'Staff & Ambience', text: `Staff ka behaviour bahut friendly tha aur jagah bilkul clean thi.${noteText} Bohot achha time spend hua ✨😊`, language: 'hindi' },
        { id: 'opt4', focus: 'Taste & Value', text: `Har cheez garam aur fresh serve hui. Taste badhiya tha aur price bhi reasonable hai.${noteText} Jarur try karein 👌🍽️`, language: 'hindi' },
        { id: 'opt5', focus: 'Overall Visit', text: `Hamara visit ${BRAND.name} par bohot accha raha. Badhiya service, fresh taste aur welcoming log.${noteText} Definitely wapas aayenge! ❤️🌟`, language: 'hindi' },
      ];
    } else if (r === 4) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Accha khana aur pleasant atmosphere.${noteText} Ek badhiya visit rahi 👍😊`, language: 'hindi' },
        { id: 'opt2', focus: 'Taste & Service', text: `Khana fresh tha aur staff ne bhi achhe se attend kiya.${noteText} Service time par mili 👍☕`, language: 'hindi' },
        { id: 'opt3', focus: 'Clean & Fair', text: `Saaf-suthri jagah hai aur pricing bhi fair hai.{noteText} Food quality acchi lagi 😊`, language: 'hindi' },
        { id: 'opt4', focus: 'Staff & Ambience', text: `Staff helpful tha aur seating comfortable thi. Taste bhi accha tha.${noteText} Ek baar aane layak jagah hai 🌟👍`, language: 'hindi' },
        { id: 'opt5', focus: 'Overall Visit', text: `Overall kaafi accha experience raha. Taste aur service dono satisfactory the.${noteText} Fir se visit karenge 😊`, language: 'hindi' },
      ];
    } else if (r === 3) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Khana theek tha, lekin aaj service thodi slow lagi.${noteText} Average visit 🙂`, language: 'hindi' },
        { id: 'opt2', focus: 'Taste & Wait', text: `Taste decent tha, par order aane me thoda zyada time lag gaya.${noteText} Theek-thaak raha 🙂☕`, language: 'hindi' },
        { id: 'opt3', focus: 'Ambience & Service', text: `Staff polite tha par thoda rush zyada tha.${noteText} Service me thoda improvement ho sakta hai 🙂`, language: 'hindi' },
        { id: 'opt4', focus: 'Food & Prep', text: `Food theek-thaak tha, thoda garam hota toh aur accha lagta.${noteText} Average experience 🙂`, language: 'hindi' },
        { id: 'opt5', focus: 'Overall Visit', text: `Overall thik-thak visit raha. Jagah achhi hai par order delay hua.${noteText} Umeed hai agli baar behtar hoga 🙂`, language: 'hindi' },
      ];
    } else if (r === 2) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Khana average tha aur wait time kaafi lamba ho gaya.${noteText} Thoda disappointed 😕`, language: 'hindi' },
        { id: 'opt2', focus: 'Service Issue', text: `Aaj service se satisfaction nahi mila. Order late aaya aur khana lukewarm tha.${noteText} 😕`, language: 'hindi' },
        { id: 'opt3', focus: 'Cleanliness & Attention', text: `Staff ka dhyan nahi tha aur table safai me time laga.${noteText} Better service expect ki thi 😕`, language: 'hindi' },
        { id: 'opt4', focus: 'Taste & Delay', text: `Taste khas nahi tha aur order aane me kaafi der hui.${noteText} Management ko thoda dhyan dena chahiye 😕`, language: 'hindi' },
        { id: 'opt5', focus: 'Overall Visit', text: `Aaj ka visit disappointing raha. Service kaafi unorganized thi aur wait karna pada.{noteText} Hope this improves 😕`, language: 'hindi' },
      ];
    } else {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Bahut slow service aur khana bhi thanda tha.${noteText} Kaafi bura experience raha 😞`, language: 'hindi' },
        { id: 'opt2', focus: 'Order Delay', text: `Aaj ka experience bilkul accha nahi raha. Lamba wait karwaya aur order galat aaya.${noteText} 😞`, language: 'hindi' },
        { id: 'opt3', focus: 'Staff & Cleanliness', text: `Tables saaf nahi thi aur staff careless laga.${noteText} Service me kaafi kami hai 😞`, language: 'hindi' },
        { id: 'opt4', focus: 'Food & Attention', text: `Khana fresh nahi tha aur koi attend karne wala bhi nahi tha.${noteText} Total disappointment 😞`, language: 'hindi' },
        { id: 'opt5', focus: 'Overall Visit', text: `Bohot kharab experience raha aaj. Slow service aur thanda khana.{noteText} Management needs major improvement 😞`, language: 'hindi' },
      ];
    }
  }

  if (lang === 'gujarati') {
    // ─── GUJARATI (ROMAN SCRIPT / GUJLISH) ────────────────────────────
    if (r === 5) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Ahiya nu food ekdum mast hatu ane service pan jordar.${noteText} Bahu maza aavi! 🍳☕😋`, language: 'gujarati' },
        { id: 'opt2', focus: 'Taste & Service', text: `Food khub fresh ane tasty hatu. Staff pan ekdum polite ane helpful hato.${noteText} Quick service mali 👌😊`, language: 'gujarati' },
        { id: 'opt3', focus: 'Staff & Ambience', text: `Staff no swabhav bahu saras hato ane jagya ekdum chokhi hati.${noteText} Khub gamyu ahiya aavi ne ✨😊`, language: 'gujarati' },
        { id: 'opt4', focus: 'Taste & Value', text: `Badhu garam ane fresh hatu. Taste ekdum authentic ane rates pan reasonable che.${noteText} Must try 👌🍲`, language: 'gujarati' },
        { id: 'opt5', focus: 'Overall Visit', text: `{BRAND.name} ni visit ekdum saras rahi. Food mast, staff premal ane relaxed vatavaran.${noteText} Fari thi chokkas aavishu! ❤️👍`, language: 'gujarati' },
      ];
    } else if (r === 4) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Food saras hatu ane vatavaran pan acchu hatu.${noteText} Ek vaar javay evo anubhav 🍳👍`, language: 'gujarati' },
        { id: 'opt2', focus: 'Taste & Service', text: `Nasto ekdum garam ane tasty hato. Staff no response pan quick hato.${noteText} Saras service mali 😊☕`, language: 'gujarati' },
        { id: 'opt3', focus: 'Clean & Fair', text: `Chokkhai sarasi hati ane price pan yogya che.{noteText} Food quality acchi lagi 👍😊`, language: 'gujarati' },
        { id: 'opt4', focus: 'Staff & Ambience', text: `Staff helpful hato ane besvani vyavastha sari che.{noteText} Khub anand aavyo 🌟👍`, language: 'gujarati' },
        { id: 'opt5', focus: 'Overall Visit', text: `Overall visit khub sari rahi. Badhu vyavasthit hatu ane taste pan gamyu.{noteText} Fari mulakat laishu 😊`, language: 'gujarati' },
      ];
    } else if (r === 3) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Food theek hatu, pan aaje service thodi dhimi lagi.${noteText} Average anubhav 🙂`, language: 'gujarati' },
        { id: 'opt2', focus: 'Taste & Wait', text: `Taste barabar hato, pan order aavta vaar lagi.{noteText} Theek-thaak rahya aaje 🙂☕`, language: 'gujarati' },
        { id: 'opt3', focus: 'Ambience & Service', text: `Staff polite hato pan rush lidhe order delay thayo.{noteText} Service sudharvani jarur che 🙂`, language: 'gujarati' },
        { id: 'opt4', focus: 'Food & Prep', text: `Food thodu thandu hatu, thodu garam hoy to vadhare maza aave.{noteText} Average visit 🙂`, language: 'gujarati' },
        { id: 'opt5', focus: 'Overall Visit', text: `Overall theek-thaak visit rahi. Taste decent pan service thodi slow hati.{noteText} Aasha che aagal sudharo thase 🙂`, language: 'gujarati' },
      ];
    } else if (r === 2) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Food average hatu ane aaje wait time bahu vadhare hato.{noteText} Nirasha thai 😕`, language: 'gujarati' },
        { id: 'opt2', focus: 'Service Issue', text: `Service ma maza na aavi aaje. Order late aavyo ane food lukewarm hatu.{noteText} 😕`, language: 'gujarati' },
        { id: 'opt3', focus: 'Cleanliness & Attention', text: `Staff dhyan na aaptu hatu ane table chokkha na hata.{noteText} Vadhu sari service ni apeksha hati 😕`, language: 'gujarati' },
        { id: 'opt4', focus: 'Taste & Delay', text: `Taste khas na lagyo ane order mate lambo wait karvo padhyo.{noteText} Improvement joiye 😕`, language: 'gujarati' },
        { id: 'opt5', focus: 'Overall Visit', text: `Aaje visit disappointing rahi. Service unorganized hati ane time pan kharab thayo.{noteText} Hope this improves 😕`, language: 'gujarati' },
      ];
    } else {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Bahu slow service ane food pan thandu hatu.{noteText} Khub kharab anubhav thayo 😞`, language: 'gujarati' },
        { id: 'opt2', focus: 'Order Delay', text: `Aaje bilkul maza na aavi. Lambo wait karavyo ane order pan barabar na aavyo.{noteText} 😞`, language: 'gujarati' },
        { id: 'opt3', focus: 'Staff & Cleanliness', text: `Tables chokkha na hata ane staff beparwah hatu.{noteText} Service khub kharab hati 😞`, language: 'gujarati' },
        { id: 'opt4', focus: 'Food & Attention', text: `Food fresh na hatu ane koi dhyan pan aaptu na hatu.{noteText} Khub nirasha thai 😞`, language: 'gujarati' },
        { id: 'opt5', focus: 'Overall Visit', text: `Bahu kharab visit rahi aaje. Thandu food ane careless staff.{noteText} Management ne sudhara ni sakht jarur che 😞`, language: 'gujarati' },
      ];
    }
  }

  // ─── ENGLISH ──────────────────────────────────────────────────────
  if (r === 5) {
    return [
      { id: 'opt1', focus: 'Short & Sweet', text: `Amazing breakfast and best chai in town!${noteText} Loved it 🍳☕`, language: 'english' },
      { id: 'opt2', focus: 'Food & Tea', text: `The food was fresh and the tea was super tasty.${noteText} Quick service too ☕😋`, language: 'english' },
      { id: 'opt3', focus: 'Staff & Place', text: `Very friendly staff and clean place.${noteText} We had a great time here 😊✨`, language: 'english' },
      { id: 'opt4', focus: 'Taste & Value', text: `Everything was hot, fresh and full of flavour. The snacks and chai were really good and the price is also fair.${noteText} Must try 👌🍲`, language: 'english' },
      { id: 'opt5', focus: 'Family Visit', text: `Had a wonderful breakfast with family at ${BRAND.name}. Great food, friendly people, and relaxed vibe.${noteText} Will surely visit again! 👨‍👩‍👧‍👦❤️`, language: 'english' },
    ];
  } else if (r === 4) {
    return [
      { id: 'opt1', focus: 'Short & Sweet', text: `Good food and tasty chai!${noteText} Nice start to the morning 🍳`, language: 'english' },
      { id: 'opt2', focus: 'Food & Service', text: `Fresh breakfast and quick service.${noteText} Staff was polite and helpful 👍☕`, language: 'english' },
      { id: 'opt3', focus: 'Clean & Fair', text: `Clean sitting area and good food quality.${noteText} Prices are also reasonable 😊`, language: 'english' },
      { id: 'opt4', focus: 'Snacks & Tea', text: `Enjoyed the snacks and hot tea. Food was served quickly and tasted nice.${noteText} Worth a visit for a quick bite 🥪🍲`, language: 'english' },
      { id: 'opt5', focus: 'Overall Visit', text: `Overall a very pleasant visit. Good taste, clean tables, and friendly service.${noteText} Will definitely come back again 🌟👍`, language: 'english' },
    ];
  } else if (r === 3) {
    return [
      { id: 'opt1', focus: 'Short & Sweet', text: `Decent food, but the service was a bit slow today.${noteText} 🙂`, language: 'english' },
      { id: 'opt2', focus: 'Food & Tea', text: `The chai was nice, but the snacks could have been hotter.${noteText} Okay experience overall 🙂☕`, language: 'english' },
      { id: 'opt3', focus: 'Wait Time', text: `Staff was polite, but we had to wait some time for our order.${noteText} Average visit 🙂`, language: 'english' },
      { id: 'opt4', focus: 'Busy Hours', text: `The place was quite crowded today. Food taste was fine, but table cleaning took longer than expected.${noteText} Hope it gets faster next time 🙂🥪`, language: 'english' },
      { id: 'opt5', focus: 'Overall Visit', text: `Fair experience overall. Tea was good and seating is comfortable, but service needs a little improvement.${noteText} It was an okay visit 🙂`, language: 'english' },
    ];
  } else if (r === 2) {
    return [
      { id: 'opt1', focus: 'Short & Sweet', text: `Food was okay, but wait time was too long today.${noteText} 😕`, language: 'english' },
      { id: 'opt2', focus: 'Order Delay', text: `Not satisfied with the service today.${noteText} Order was delayed and food was lukewarm 😕`, language: 'english' },
      { id: 'opt3', focus: 'Attention', text: `The place was noisy and staff was not paying attention.${noteText} Expected better service 😕`, language: 'english' },
      { id: 'opt4', focus: 'Slow Service', text: `We had to wait a long time to get our food and tables were not cleaned quickly.${noteText} Need to improve customer service 😕⏳`, language: 'english' },
      { id: 'opt5', focus: 'Overall Visit', text: `Disappointing visit today. The chai was fine but snacks were not fresh and service was very slow.${noteText} Hope management fixes this 😕`, language: 'english' },
    ];
  } else {
    return [
      { id: 'opt1', focus: 'Short & Sweet', text: `Very slow service and cold food today.${noteText} 😞`, language: 'english' },
      { id: 'opt2', focus: 'Order Issue', text: `Bad experience today.${noteText} Waited very long and our order was wrong 😞`, language: 'english' },
      { id: 'opt3', focus: 'Cleanliness', text: `Staff was unorganized and tables were not clean.${noteText} Very poor service 😞`, language: 'english' },
      { id: 'opt4', focus: 'Food & Wait', text: `Disappointed with the visit. Food took forever to arrive and tasted stale.${noteText} Nobody came to attend us properly 😞👎`, language: 'english' },
      { id: 'opt5', focus: 'Overall Visit', text: `Extremely poor experience today. Long waiting time, cold food, and careless staff.${noteText} Needs major improvement in service 😞`, language: 'english' },
    ];
  }
}

export default function CustomerReview({
  businessId = 'default_business',
  onSwitchToOwner = null,
  isPreview = false,
}) {
  const urlParams = new URLSearchParams(window.location.search);
  const tableParam = urlParams.get('table') || null;
  const isPreviewMode = isPreview || urlParams.get('preview') === 'true';

  // Custom editor view toggle (inline)
  const [showCustomEditor, setShowCustomEditor] = useState(false);
  const reviewCardRef = useRef(null);
  const editorRef = useRef(null);
  const topicsSectionRef = useRef(null);

  // Rating
  const [rating, setRating] = useState(() => {
    try {
      const savedRating = Number(sessionStorage.getItem('nastaGharSelectedRating'));
      return savedRating >= 1 && savedRating <= 5 ? savedRating : 5;
    } catch {
      return 5;
    }
  });
  const [hoverRating, setHoverRating] = useState(0);
  const [reviewStarted, setReviewStarted] = useState(false);

  // Language selection
  const [selectedLanguage, setSelectedLanguage] = useState(() => {
    try {
      const savedLang = sessionStorage.getItem('nastaGharSelectedLanguage');
      return savedLang && ['english', 'hindi', 'gujarati'].includes(savedLang) ? savedLang : 'english';
    } catch {
      return 'english';
    }
  });

  // Business Category
  const [businessCategory, setBusinessCategory] = useState('Breakfast & Snacks');

  // Topics
  const [availableTopics, setAvailableTopics] = useState(DEFAULT_TOPICS);
  const [selectedTopics, setSelectedTopics] = useState(['Breakfast', 'Chai & Tea']);
  const [nothingSpecific, setNothingSpecific] = useState(false);
  const [personalNote, setPersonalNote] = useState('');

  // Keep Google Maps pointed at the restaurant's selected destination.
  const [googleReviewUrl, setGoogleReviewUrl] = useState(BRAND.googleMapUrl);

  // Ideas initialized with fallback ideas (no empty screen, instant feedback)
  const [ideas, setIdeas] = useState(() => getFallbackIdeas(rating, '', selectedLanguage));
  const [loadingIdeas, setLoadingIdeas] = useState(false);
  const [selectedIdeaId, setSelectedIdeaId] = useState(null);
  const fetchIdeasDebounceRef = useRef(null);

  // Editor
  const [draftReview, setDraftReview] = useState('');
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

  useEffect(() => {
    try {
      const savedReview = sessionStorage.getItem('nastaGharSelectedReview');
      const savedBusinessId = sessionStorage.getItem('nastaGharBusinessId');
      if (!savedReview || savedBusinessId !== businessId) return;
      setDraftReview(savedReview);
      setSelectedIdeaId(sessionStorage.getItem('nastaGharSelectedReviewId'));
      setRating(Number(sessionStorage.getItem('nastaGharSelectedRating')) || 5);
      setCopied(sessionStorage.getItem('nastaGharClipboardCopied') === 'true');
      setHandoffOpen(true);
    } catch {
      // Session storage can be unavailable in restricted contexts.
    }
  }, [businessId]);

  // Acknowledgement for clipboard handoff instructions.
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

  // ─── FETCH CONFIG ──────────────────────────────────────────────────────────
  useEffect(() => {
    apiFetch(`/api/businesses/${businessId}/review-link`)
      .then((r) => r.json())
      .then((d) => {
        if (d.review_url && d.is_configured) setGoogleReviewUrl(d.review_url);
        if (d.category) setBusinessCategory(d.category);
        if (d.topics && d.topics.length > 0) {
          const enriched = d.topics.map((t) => ({
            label: t,
            icon: getTopicIcon(t),
          }));
          setAvailableTopics(enriched);
          setSelectedTopics(d.topics.slice(0, 2));
        } else if (d.category) {
          const catTopics = resolveCategoryTopics(d.category);
          setAvailableTopics(catTopics);
          setSelectedTopics(catTopics.slice(0, 2).map((t) => t.label));
        }
      })
      .catch(() => {/* use defaults */});

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
      .then((d) => setSessionId(d.session_id))
      .catch(() => setSessionId(`local-${Date.now()}`));
  }, [businessId, tableParam]);

  function getTopicIcon(label) {
    const l = label.toLowerCase();
    if (l.includes('breakfast') || l.includes('nasta')) return '🍳';
    if (l.includes('chai') || l.includes('tea') || l.includes('coffee') || l.includes('drink') || l.includes('beverage')) return '☕';
    if (l.includes('snack')) return '🥪';
    if (l.includes('taste') || l.includes('flavour') || l.includes('flavor') || l.includes('food')) return '😋';
    if (l.includes('portion')) return '🍽️';
    if (l.includes('room') || l.includes('bed')) return '🛏️';
    if (l.includes('comfort')) return '✨';
    if (l.includes('location')) return '📍';
    if (l.includes('result')) return '✨';
    if (l.includes('staff') || l.includes('service') || l.includes('friendly') || l.includes('experience')) return '😊';
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
        metadata: { business_id: businessId, rating, language: selectedLanguage, ...meta },
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
    setReviewStarted(true);
    try { sessionStorage.setItem('nastaGharSelectedRating', String(s)); } catch {}
    logEvent('rating_selected', { rating: s });
  };

  const handleContinueReview = () => {
    setReviewStarted(true);
    setTimeout(() => {
      topicsSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 60);
  };

  const handleLanguageSelect = (langId) => {
    setSelectedLanguage(langId);
    try {
      sessionStorage.setItem('nastaGharSelectedLanguage', langId);
    } catch {}
    logEvent('language_selected', { language: langId });
    // Instant fallback update in selected language
    setIdeas(getFallbackIdeas(rating, personalNote, langId));
  };

  const toggleTopic = (label) => {
    setNothingSpecific(false);
    setSelectedTopics((prev) => {
      const next = prev.includes(label) ? prev.filter((t) => t !== label) : [...prev, label];
      logEvent('aspects_selected', { aspects: next });
      return next;
    });
  };

  const handleNothingSpecific = () => {
    setNothingSpecific(true);
    setSelectedTopics([]);
    logEvent('aspects_selected', { aspects: [] });
  };

  // Keep ideas synchronized with rating, topics, personal note, and language
  useEffect(() => {
    // 1. Instant fallback update for 0ms perceived latency
    setIdeas(getFallbackIdeas(rating, personalNote, selectedLanguage));

    // 2. Debounce background request to enrich with AI-crafted candidate ideas
    if (fetchIdeasDebounceRef.current) {
      clearTimeout(fetchIdeasDebounceRef.current);
    }

    fetchIdeasDebounceRef.current = setTimeout(async () => {
      setLoadingIdeas(true);
      try {
        const res = await apiFetch(`/api/reviews/ideas`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            business_id: businessId,
            rating,
            aspects: nothingSpecific ? [] : selectedTopics,
            user_note: personalNote.trim(),
            language: selectedLanguage,
            business_category: businessCategory,
          }),
        });
        if (res.ok) {
          const data = await res.json();
          if (data.ideas && data.ideas.length >= 3) {
            setIdeas(data.ideas);
          }
        }
      } catch {
        // Fallback ideas are already in place
      } finally {
        setLoadingIdeas(false);
      }
    }, 350);

    return () => {
      if (fetchIdeasDebounceRef.current) {
        clearTimeout(fetchIdeasDebounceRef.current);
      }
    };
  }, [rating, selectedTopics, nothingSpecific, personalNote, selectedLanguage, businessCategory, businessId]);

  const handlePostDirectly = async (idea) => {
    await startReviewHandoff(idea.text, idea.id);
  };

  const startReviewHandoff = async (reviewText, reviewId) => {
    if (!reviewText?.trim()) return;
    setSelectedIdeaId(reviewId);
    setDraftReview(reviewText);
    setHandoffOpen(true);
    setCopyingReview(true);
    setShowCopyToast(false);
    logEvent('review_selected', { review_id: reviewId, language: selectedLanguage });
    logEvent('idea_selected', { idea_id: reviewId, language: selectedLanguage });
    logEvent('review_approved', { length: reviewText.length, direct_post: true, language: selectedLanguage });
    logEvent('google_review_handoff_started', { review_id: reviewId, language: selectedLanguage });

    try {
      sessionStorage.setItem('nastaGharSelectedReview', reviewText);
      sessionStorage.setItem('nastaGharSelectedRating', String(rating));
      sessionStorage.setItem('nastaGharSelectedLanguage', selectedLanguage);
      sessionStorage.setItem('nastaGharSelectedReviewId', String(reviewId ?? ''));
      sessionStorage.setItem('nastaGharSelectedAt', new Date().toISOString());
      sessionStorage.setItem('nastaGharBusinessId', businessId);
      sessionStorage.setItem('nastaGharGoogleMapsDestination', googleReviewUrl);
    } catch {
      // Continue handoff even when session storage is unavailable.
    }

    const copiedSuccessfully = await copyTextToClipboard(reviewText);
    setCopyingReview(false);
    setCopied(copiedSuccessfully);
    setShowCopyToast(true);
    setTimeout(() => setShowCopyToast(false), 3500);
    try { sessionStorage.setItem('nastaGharClipboardCopied', String(copiedSuccessfully)); } catch {}
    logEvent(copiedSuccessfully ? 'review_clipboard_success' : 'review_clipboard_failed', { review_id: reviewId, language: selectedLanguage });

    if (copiedSuccessfully) {
      logEvent('google_maps_redirect', { destination: googleReviewUrl, language: selectedLanguage });
      logEvent('google_review_link_opened');
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
          language: selectedLanguage,
          business_category: businessCategory,
        }),
      });
      const data = await res.json();
      if (data.review) setDraftReview(data.review);
    } catch { /* keep current */ }
    finally { setIsRegenerating(false); }
  };

  const handleContinueToGoogle = async () => {
    if (!draftReview.trim()) return;
    await startReviewHandoff(draftReview, selectedIdeaId);
  };

  const handlePrivateFeedback = async (e) => {
    e.preventDefault();
    if (!privateNote.trim()) return;
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
    } catch {
      setPrivateError('We couldn’t send your message right now. Please try again.');
    }
  };

  const activeRating = hoverRating || rating;
  const ratingLabel = RATING_LABELS[activeRating] || RATING_LABELS[5];

  // ─── RENDER ─────────────────────────────────────────────────────────────────
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

      <RestaurantWorld />

      <div
        ref={reviewCardRef}
        className={`ng-card ${!reviewStarted ? 'ng-initial-card' : 'ng-expanded-card'}`}
      >
        {/* ── HEADER: BUSINESS WELCOME ─────────────────────────────────── */}
        <header className="ng-header">
          <h1 className="ng-brand-name">નાસ્તા ઘર</h1>
          <p className="ng-brand-sub">Homestyle Breakfast & Chai • Rajkot</p>
          {tableParam && (
            <span className="ng-table-pill">📍 {tableParam}</span>
          )}
        </header>

        {/* ── SECTION 1: RATING ─────────────────────────────────────────── */}
        <section className="ng-section" aria-label="Rating selection">
          <h2 className="ng-section-title">How was your experience?</h2>
          <p className="ng-section-sub">Tap a star to rate your visit</p>

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
              Continue →
            </button>
          )}
        </section>

        {reviewStarted && (
          <>
            <div className="ng-section-divider" aria-hidden="true" />

            {/* ── SECTION 2: LANGUAGE SELECTION ────────────────────────────── */}
            <section className="ng-section ng-fade-in" aria-label="Language selection">
              <h2 className="ng-section-title">Which language feels most natural to you?</h2>
              <p className="ng-section-sub">We'll craft review ideas in your preferred style</p>

              <div className="ng-lang-row" role="radiogroup" aria-label="Select review language">
                {LANGUAGES.map((lang) => {
                  const isSelected = selectedLanguage === lang.id;
                  return (
                    <button
                      key={lang.id}
                      type="button"
                      role="radio"
                      aria-checked={isSelected}
                      className={`ng-lang-btn ${isSelected ? 'selected' : ''}`}
                      onClick={() => handleLanguageSelect(lang.id)}
                    >
                      <span className="ng-lang-label">{lang.label}</span>
                      <span className="ng-lang-sub">{lang.sub}</span>
                    </button>
                  );
                })}
              </div>
            </section>

            <div className="ng-section-divider" aria-hidden="true" />

            {/* ── SECTION 3: HOSPITALITY TOPICS ────────────────────────────── */}
            <section ref={topicsSectionRef} className="ng-section ng-fade-in" aria-label="Visit highlights">
              <h2 className="ng-section-title">
                {rating >= 4 ? 'What did you enjoy?' : 'What stood out?'}
              </h2>
              <p className="ng-section-sub">
                {rating >= 4 ? 'Tap anything you liked during your visit' : 'Pick anything matching your experience'}
              </p>

              <div className="ng-chips-grid">
                {availableTopics.map(({ label, icon }) => {
                  const selected = selectedTopics.includes(label);
                  return (
                    <button
                      key={label}
                      type="button"
                      className={`ng-chip ${selected ? 'selected' : ''}`}
                      onClick={() => toggleTopic(label)}
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
                >
                  <span className="ng-chip-icon">—</span>
                  <span>Nothing specific</span>
                </button>
              </div>

              <div className="ng-note-wrap">
                <label htmlFor="ng-note" className="ng-note-label">
                  Anything else you'd like to mention? <span className="ng-optional">(optional)</span>
                </label>
                <input
                  id="ng-note"
                  type="text"
                  className="ng-note-input"
                  placeholder="e.g. The staff was super friendly! 😋"
                  value={personalNote}
                  onChange={(e) => setPersonalNote(e.target.value)}
                  maxLength={100}
                />
              </div>
            </section>

            <div className="ng-section-divider" aria-hidden="true" />

            {/* ── SECTION 4: REVIEW SUGGESTIONS / CUSTOM EDITOR ──────────── */}
            {!showCustomEditor ? (
              <section className="ng-section" aria-label="Review suggestions">
                <div className="ng-ideas-header">
                  <h2 className="ng-section-title">Here are a few ways to say it</h2>
                  <p className="ng-section-sub">
                    Tap any review below to copy & continue to Google
                  </p>
                  {loadingIdeas && (
                    <div className="ng-updating-badge">
                      <span>✨</span>
                      <span>Refining suggestions...</span>
                    </div>
                  )}
                </div>

                <div className="ng-ideas-list">
                  {ideas.map((idea, i) => {
                    const cardLang = idea.language || selectedLanguage;
                    const langDisplay = cardLang === 'gujarati' ? 'Gujarati' : (cardLang === 'hindi' ? 'Hindi' : 'English');
                    return (
                      <div
                        key={idea.id || i}
                        className={`ng-idea-card ${selectedIdeaId === idea.id ? 'picked' : ''}`}
                        onClick={() => handlePostDirectly(idea)}
                        role="button"
                        tabIndex={0}
                        aria-label={`Option ${i + 1} (${langDisplay}): ${idea.text}`}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handlePostDirectly(idea);
                          }
                        }}
                      >
                        <div className="ng-idea-top-row">
                          <div className="ng-idea-meta">
                            <span className="ng-idea-num">Option {i + 1}</span>
                            <span className="ng-idea-lang-badge">{langDisplay}</span>
                          </div>
                          <div className="ng-idea-stars" aria-hidden="true">
                            {'★'.repeat(rating)}
                          </div>
                        </div>
                        <p className="ng-idea-text">"{idea.text}"</p>
                        <div className="ng-idea-card-action">
                          <span className="ng-idea-action-text">Use this review →</span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="ng-divider"><span>or</span></div>

                <button
                  type="button"
                  className="ng-btn-write-own"
                  onClick={() => {
                    setSelectedIdeaId('custom');
                    if (!draftReview) setDraftReview('');
                    setShowCustomEditor(true);
                    setTimeout(() => editorRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
                  }}
                >
                  ✍️ Write my own review
                </button>
              </section>
            ) : (
              <section ref={editorRef} className="ng-section ng-fade-in" aria-label="Custom review editor">
                <div className="ng-editor-header">
                  <h2 className="ng-section-title" style={{ margin: 0 }}>Write your review</h2>
                  <span className="ng-char-pill">{draftReview.length} chars</span>
                </div>
                <p className="ng-section-sub">Edit anything before posting — it's your words!</p>

                <div className="ng-textarea-wrap">
                  <textarea
                    className="ng-textarea"
                    rows={5}
                    value={draftReview}
                    onChange={(e) => setDraftReview(e.target.value)}
                    placeholder="Write your review here..."
                  />
                </div>

                <div className="ng-editor-tools">
                  <button
                    type="button"
                    className="ng-btn-tool"
                    onClick={handleMakeNatural}
                    disabled={isRegenerating || !draftReview.trim()}
                  >
                    {isRegenerating ? '✨ Refining...' : '✨ Make it more natural'}
                  </button>
                  <button
                    type="button"
                    className="ng-btn-tool"
                    onClick={() => setShowCustomEditor(false)}
                  >
                    ← Back to review ideas
                  </button>
                </div>

                <div className="ng-google-notice">
                  Your words, your review. Paste the copy into Google and post it yourself.
                </div>

                <button
                  type="button"
                  className="ng-btn-primary ng-btn-cta"
                  onClick={handleContinueToGoogle}
                  disabled={!draftReview.trim()}
                >
                  Copy & open Google Review
                </button>
              </section>
            )}

            {/* ── SECTION 5: PRIVATE FEEDBACK PROMPT ────────────────────── */}
            <div className="ng-private-prompt">
              {rating <= 2
                ? 'Want to tell the team what could have been better?'
                : 'Want to tell us privately?'}{' '}
              <button type="button" className="ng-link-btn" onClick={() => setShowPrivate(true)}>
                Send private note
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
              ? "Review copied to clipboard ✓ On Google Maps, tap 'Write a review', select your stars and Paste."
              : 'Review could not be copied automatically. Tap Copy Review below.'}
          </span>
        </div>
      )}

      {/* ════════ HANDOFF MODAL ════════ */}
      {handoffOpen && (
        <div className="ng-modal-backdrop">
          <div className="ng-modal ng-modal-bounce">
            <div className="ng-modal-icon">📋</div>
            <h3 className="ng-modal-title">
              {copyingReview ? 'Preparing your review…' : copied ? 'Review Copied to Clipboard' : 'Copy Your Review to Continue'}
            </h3>
            <p className="ng-modal-body">
              {copyingReview
                ? <>Your review is ready. Copying to clipboard and opening Google Maps…</>
                : copied
                ? <>Your review is copied ✓ You selected {rating}★ here. On Google Maps, tap <strong>Write a review</strong>, select {rating} stars, then paste your review.</>
                : <>Your review is saved for this browser session. Tap Copy Review below, then paste it on Google Maps.</>}
            </p>

            <div className="ng-modal-steps">
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">1</span>
                <span>Choose the rating that reflects your visit on Google (you selected <strong>{rating} stars</strong> here)</span>
              </div>
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">2</span>
                <span>{copyingReview ? 'Copying selected review…' : copied ? <><strong>Paste</strong> the copied review (long-press → Paste on mobile)</> : <>Copy the review below, then <strong>paste</strong> it into Google</>}</span>
              </div>
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">3</span>
                <span>Review it, then tap Google's <strong>Post</strong> button when you're ready.</span>
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
                  try { sessionStorage.setItem('nastaGharClipboardCopied', String(ok)); } catch {}
                  logEvent(ok ? 'review_clipboard_success' : 'review_clipboard_failed', { review_id: selectedIdeaId });
                  if (ok) setTimeout(() => setCopyAgainSuccess(false), 2000);
                }}
              >
                {copyAgainSuccess ? '✓ Copied!' : copied ? '📋 Copy Again' : '📋 Copy Review'}
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
                  window.location.href = googleReviewUrl;
                }}
              >
                ↗ Continue to Google Maps
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
            <h3 className="ng-modal-title">Direct note to {BRAND.name}</h3>
            <p className="ng-modal-body">Share anything you'd like our team to know privately.</p>

            {privateSent ? (
              <div className="ng-private-success">
                <span style={{ fontSize: '2rem' }}>💌</span>
                <h4>Thank you!</h4>
                <p>Your message has been sent directly to the team.</p>
                <button
                  type="button"
                  className="ng-btn-primary"
                  onClick={() => setShowPrivate(false)}
                  style={{ marginTop: '1rem' }}
                >
                  Close
                </button>
              </div>
            ) : (
              <form onSubmit={handlePrivateFeedback} className="ng-private-form">
                {privateError && <p className="warning-box" role="alert">{privateError}</p>}
                <textarea
                  className="ng-textarea"
                  rows={4}
                  placeholder="Share your thoughts, suggestions, or anything else..."
                  value={privateNote}
                  onChange={(e) => setPrivateNote(e.target.value)}
                  required
                />
                <input
                  type="text"
                  className="ng-note-input"
                  placeholder="Your name or contact (optional)"
                  value={privateContact}
                  onChange={(e) => setPrivateContact(e.target.value)}
                  style={{ marginTop: '0.75rem' }}
                />
                <div className="ng-modal-actions" style={{ marginTop: '1.25rem' }}>
                  <button type="submit" className="ng-btn-primary">Send to Team</button>
                  <button type="button" className="ng-btn-secondary" onClick={() => setShowPrivate(false)}>
                    Cancel
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
              <strong>Your review is copied when you choose it.</strong> Paste it into Google and submit it yourself.
            </div>
          </div>
          <button
            type="button"
            className="ng-cookie-btn"
            onClick={handleAcceptConsent}
          >
            Got it ✓
          </button>
        </div>
      )}
    </div>
  );
}
