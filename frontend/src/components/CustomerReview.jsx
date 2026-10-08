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

const RATING_LABELS = {
  5: { text: 'Loved it!', emoji: '🤩' },
  4: { text: 'Really good', emoji: '😊' },
  3: { text: 'It was okay', emoji: '🙂' },
  2: { text: 'Disappointed', emoji: '😕' },
  1: { text: 'Not good', emoji: '😞' },
};

const getLanguageLabel = (l) => {
  if (l === 'hindi') return 'Hindi';
  if (l === 'gujarati') return 'Gujarati';
  return 'English';
};

const getFallbackIdeas = (r, note, lang = 'english') => {
  const noteText = note && note.trim() ? ` ${note.trim().replace(/[.!]+$/, '')}.` : '';
  const l = (lang || 'english').toLowerCase();

  if (l.includes('hin')) {
    if (r === 5) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Bahut hi tasty khana aur best chai!${noteText} Maza aa gaya 🍳☕` },
        { id: 'opt2', focus: 'Food & Taste', text: `Khana ekdum fresh aur lajawab tha.${noteText} Quick service too ☕😋` },
        { id: 'opt3', focus: 'Staff & Ambience', text: `Staff bahut polite hai aur safai ka pura dhyan rakha hai.${noteText} Family ke sath visit ke liye best jagah 😊✨` },
        { id: 'opt4', focus: 'Taste & Value', text: `Har cheez garam aur fresh mili. Snacks aur chai bahut acche the aur price bhi sahi hai.${noteText} Zaroor try karein 👌🍲` },
        { id: 'opt5', focus: 'Overall Visit', text: `Overall experience bahut shandar raha at ${BRAND.name}. Khana aur service dono top notch the.${noteText} Phir zaroor aayenge! 👨‍👩‍👧‍👦❤️` },
      ];
    } else if (r === 4) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Accha khana aur tasty chai!${noteText} Morning ke liye badhiya choice 🍳` },
        { id: 'opt2', focus: 'Food & Service', text: `Breakfast fresh tha aur service bhi fast thi.${noteText} Staff ka behaviour kaafi polite tha 👍☕` },
        { id: 'opt3', focus: 'Clean & Fair', text: `Clean sitting area aur achhi food quality.${noteText} Rates bhi pocket friendly hain 😊` },
        { id: 'opt4', focus: 'Snacks & Tea', text: `Snacks aur garam chai enjoy kiya. Food time pe serve hua aur taste accha tha.${noteText} Quick bite ke liye acchi jagah 🥪🍲` },
        { id: 'opt5', focus: 'Overall Visit', text: `Kaafi accha visit raha. Good taste, clean tables aur friendly service.${noteText} Definitely visit karne jaisa hai 🌟👍` },
      ];
    } else if (r === 3) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Khana theek tha, lekin service thodi slow lagi aaj.${noteText} 🙂` },
        { id: 'opt2', focus: 'Food & Wait', text: `Chai acchi thi par snacks thode thande the.${noteText} Average experience raha 🙂☕` },
        { id: 'opt3', focus: 'Service Pace', text: `Staff polite tha par order ke liye wait karna pada.${noteText} Decent visit 🙂` },
        { id: 'opt4', focus: 'Crowd & Cleaning', text: `Aaj bheed kaafi thi. Food taste theek tha lekin table cleaning mein thoda time lag gaya.${noteText} Hope agli baar fast service mile 🙂🥪` },
        { id: 'opt5', focus: 'Overall Visit', text: `Overall theek experience tha. Seating comfortable hai par service mein thoda improvement chahiye.${noteText} Okay visit 🙂` },
      ];
    } else if (r === 2) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Khana theek tha par wait time bahut zyada tha aaj.${noteText} 😕` },
        { id: 'opt2', focus: 'Order Delay', text: `Aaj service se khush nahi huye.${noteText} Order kaafi late aaya aur khana bhi lukewarm tha 😕` },
        { id: 'opt3', focus: 'Staff Attention', text: `Staff ka dhyaan nahi tha aur service kaafi slow thi.{noteText} Better service expected thi 😕` },
        { id: 'opt4', focus: 'Slow Service', text: `Khaane ke liye kaafi wait karna pada aur tables quickly clean nahi huye.{noteText} Service improve karni chahiye 😕⏳` },
        { id: 'opt5', focus: 'Overall Visit', text: `Disappointing visit raha. Chai theek thi par snacks fresh nahi the aur service slow thi.{noteText} Umeed hai agle baar sudhar hoga 😕` },
      ];
    } else {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Bahut slow service aur khana bhi thanda mila aaj.${noteText} 😞` },
        { id: 'opt2', focus: 'Order Issue', text: `Kharab experience raha aaj.${noteText} Bahut der wait kiya aur order bhi galat aaya 😞` },
        { id: 'opt3', focus: 'Cleanliness', text: `Staff unorganized tha aur tables bilkul clean nahi the.${noteText} Poor service 😞` },
        { id: 'opt4', focus: 'Food & Wait', text: `Disappointed with the visit. Khaana aane mein bahut time laga aur taste fresh nahi tha.${noteText} Koi theek se attend nahi kar raha tha 😞👎` },
        { id: 'opt5', focus: 'Overall Visit', text: `Kaafi poor experience raha. Long waiting time, cold food aur careless staff.{noteText} Major improvement ki zaroorat hai 😞` },
      ];
    }
  }

  if (l.includes('guj')) {
    if (r === 5) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Ahiya nu food ekdum mast hatu ane chai pan jordar!${noteText} Khub majja aavi 🍳☕` },
        { id: 'opt2', focus: 'Food & Taste', text: `Nasto ekdum fresh ane taste lajawab hato.${noteText} Quick service too ☕😋` },
        { id: 'opt3', focus: 'Staff & Ambience', text: `Staff khub polite chhe ane chokkhai pan saras chhe.${noteText} Family sathe aavva mate best jagya 😊✨` },
        { id: 'opt4', focus: 'Taste & Value', text: `Badhu garam ane fresh malyu. Snacks ane chai bahu saras hata ane bhav pan fair chhe.${noteText} Jarur try karva jevu chhe 👌🍲` },
        { id: 'opt5', focus: 'Overall Visit', text: `Overall experience bahu j saras rahyo at ${BRAND.name}. Food ane service banne top class.{noteText} Fari thi jarur aavishu! 👨‍👩‍👧‍👦❤️` },
      ];
    } else if (r === 4) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Saras khavanu ane kadak chai!${noteText} Savarni saras sharuat 🍳` },
        { id: 'opt2', focus: 'Food & Service', text: `Breakfast fresh hatu ane quick service mali.${noteText} Staff no swabhav pan vinamra hato 👍☕` },
        { id: 'opt3', focus: 'Clean & Fair', text: `Clean sitting area ane sari food quality.${noteText} Rates pan reasonable chhe 😊` },
        { id: 'opt4', focus: 'Snacks & Tea', text: `Snacks ane garam chai ni maja aavi. Food jaldi aavyu ane taste saro hato.${noteText} Quick bite mate saras jagya 🥪🍲` },
        { id: 'opt5', focus: 'Overall Visit', text: `Samagra mulakat khub sari rahi. Saro taste, clean tables ane friendly service.${noteText} Fari aavva jevu chhe 🌟👍` },
      ];
    } else if (r === 3) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Food thik hatu, pan service thodi slow lagi aaje.${noteText} 🙂` },
        { id: 'opt2', focus: 'Food & Wait', text: `Chai sari hati pan snacks thoda thanda hata.${noteText} Samanya anubhav rahyo 🙂☕` },
        { id: 'opt3', focus: 'Service Pace', text: `Staff saro hato pan order mate thodi vaar lagi.{noteText} Average visit 🙂` },
        { id: 'opt4', focus: 'Crowd & Cleaning', text: `Bheed vadhare hati aaje. Taste barabar hato pan table cleaning ma time lagyo.{noteText} Aavti vakhte better service ni apeksha 🙂🥪` },
        { id: 'opt5', focus: 'Overall Visit', text: `Overall thik anubhav rahyo. Seating comfortable chhe pan service thodi improve karvani jarur chhe.{noteText} Okay visit 🙂` },
      ];
    } else if (r === 2) {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Food thik hatu pan wait bahu karvu padyu aaje.${noteText} 😕` },
        { id: 'opt2', focus: 'Order Delay', text: `Aaje service thi santosh na thayo.{noteText} Order late aavyo ane food pan lukewarm hatu 😕` },
        { id: 'opt3', focus: 'Staff Attention', text: `Staff dhyan nhato aapi rahyo ane service slow hati.{noteText} Better service expected hati 😕` },
        { id: 'opt4', focus: 'Slow Service', text: `Order mate ghano wait karyo ane tables pan quickly clean na thaya.{noteText} Customer service improve karvani jarur chhe 😕⏳` },
        { id: 'opt5', focus: 'Overall Visit', text: `Nirashajanak visit rahi. Chai thik hati pan snacks fresh nahota ane service slow hati.{noteText} Management sudharo kare evi aasha 😕` },
      ];
    } else {
      return [
        { id: 'opt1', focus: 'Short & Sweet', text: `Bahu j slow service ane thandu khavanu aapyu aaje.${noteText} 😞` },
        { id: 'opt2', focus: 'Order Issue', text: `Kharab anubhav rahyo aaje.{noteText} Ghani vaar ubha rakhya ane order pan wrong aavyo 😞` },
        { id: 'opt3', focus: 'Cleanliness', text: `Staff unorganized hato ane tables bilkul clean nahota.{noteText} Bahu poor service 😞` },
        { id: 'opt4', focus: 'Food & Wait', text: `Disappointed with the visit. Food aavva ma khub time lagyo ane taste fresh nahoto.{noteText} Koi barabar attend pan na karyu 😞👎` },
        { id: 'opt5', focus: 'Overall Visit', text: `Experience bilkul saro na rahyo. Long waiting time, thandu food ane careless staff.{noteText} Service ma mota sudhara ni jarur chhe 😞` },
      ];
    }
  }

  // English fallback
  if (r === 5) {
    return [
      { id: 'opt1', focus: 'Short & Sweet', text: `Amazing breakfast and best chai in town!${noteText} Loved it 🍳☕` },
      { id: 'opt2', focus: 'Food & Tea', text: `The food was fresh and the tea was super tasty.${noteText} Quick service too ☕😋` },
      { id: 'opt3', focus: 'Staff & Place', text: `Very friendly staff and clean place.${noteText} We had a great time here 😊✨` },
      { id: 'opt4', focus: 'Taste & Value', text: `Everything was hot, fresh and full of flavour. The snacks and chai were really good and the price is also fair.${noteText} Must try 👌🍲` },
      { id: 'opt5', focus: 'Family Visit', text: `Had a wonderful breakfast with family at ${BRAND.name}. Great food, friendly people, and relaxed vibe.${noteText} Will surely visit again! 👨‍👩‍👧‍👦❤️` },
    ];
  } else if (r === 4) {
    return [
      { id: 'opt1', focus: 'Short & Sweet', text: `Good food and tasty chai!${noteText} Nice start to the morning 🍳` },
      { id: 'opt2', focus: 'Food & Service', text: `Fresh breakfast and quick service.${noteText} Staff was polite and helpful 👍☕` },
      { id: 'opt3', focus: 'Clean & Fair', text: `Clean sitting area and good food quality.${noteText} Prices are also reasonable 😊` },
      { id: 'opt4', focus: 'Snacks & Tea', text: `Enjoyed the snacks and hot tea. Food was served quickly and tasted nice.${noteText} Worth a visit for a quick bite 🥪🍲` },
      { id: 'opt5', focus: 'Overall Visit', text: `Overall a very pleasant visit. Good taste, clean tables, and friendly service.${noteText} Will definitely come back again 🌟👍` },
    ];
  } else if (r === 3) {
    return [
      { id: 'opt1', focus: 'Short & Sweet', text: `Decent food, but the service was a bit slow today.${noteText} 🙂` },
      { id: 'opt2', focus: 'Food & Tea', text: `The chai was nice, but the snacks could have been hotter.${noteText} Okay experience overall 🙂☕` },
      { id: 'opt3', focus: 'Wait Time', text: `Staff was polite, but we had to wait some time for our order.${noteText} Average visit 🙂` },
      { id: 'opt4', focus: 'Busy Hours', text: `The place was quite crowded today. Food taste was fine, but table cleaning took longer than expected.${noteText} Hope it gets faster next time 🙂🥪` },
      { id: 'opt5', focus: 'Overall Visit', text: `Fair experience overall. Tea was good and seating is comfortable, but service needs a little improvement.${noteText} It was an okay visit 🙂` },
    ];
  } else if (r === 2) {
    return [
      { id: 'opt1', focus: 'Short & Sweet', text: `Food was okay, but wait time was too long today.${noteText} 😕` },
      { id: 'opt2', focus: 'Order Delay', text: `Not satisfied with the service today.${noteText} Order was delayed and food was lukewarm 😕` },
      { id: 'opt3', focus: 'Attention', text: `The place was noisy and staff was not paying attention.${noteText} Expected better service 😕` },
      { id: 'opt4', focus: 'Slow Service', text: `We had to wait a long time to get our food and tables were not cleaned quickly.${noteText} Need to improve customer service 😕⏳` },
      { id: 'opt5', focus: 'Overall Visit', text: `Disappointing visit today. The chai was fine but snacks were not fresh and service was very slow.${noteText} Hope management fixes this 😕` },
    ];
  } else {
    return [
      { id: 'opt1', focus: 'Short & Sweet', text: `Very slow service and cold food today.${noteText} 😞` },
      { id: 'opt2', focus: 'Order Issue', text: `Bad experience today.${noteText} Waited very long and our order was wrong 😞` },
      { id: 'opt3', focus: 'Cleanliness', text: `Staff was unorganized and tables were not clean.${noteText} Very poor service 😞` },
      { id: 'opt4', focus: 'Food & Wait', text: `Disappointed with the visit. Food took forever to arrive and tasted stale.${noteText} Nobody came to attend us properly 😞👎` },
      { id: 'opt5', focus: 'Overall Visit', text: `Extremely poor experience today. Long waiting time, cold food, and careless staff.${noteText} Needs major improvement in service 😞` },
    ];
  }
};

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
  const topicsSectionRef = useRef(null);

  // Language selection: 'english' | 'hindi' | 'gujarati'
  const [language, setLanguage] = useState(() => {
    try {
      const savedLang = sessionStorage.getItem('nastaGharSelectedLanguage');
      return ['english', 'hindi', 'gujarati'].includes(savedLang) ? savedLang : 'english';
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
  const [ideas, setIdeas] = useState(() => getFallbackIdeas(rating, '', language));
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
      // Session storage can be unavailable in restricted browser contexts.
    }
  }, [businessId]);

  // Acknowledgement for the clipboard handoff instructions.
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

  // ─── FETCH CONFIG (optional enrichment, never overrides brand name) ─────────
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
    if (l.includes('taste') || l.includes('flavour') || l.includes('food')) return '😋';
    if (l.includes('staff') || l.includes('service') || l.includes('friendly')) return '😊';
    if (l.includes('clean')) return '✨';
    if (l.includes('value') || l.includes('money') || l.includes('price')) return '💰';
    if (l.includes('quick') || l.includes('fast') || l.includes('speed')) return '⚡';
    if (l.includes('atmosphere') || l.includes('vibe') || l.includes('ambience')) return '🌟';
    if (l.includes('room') || l.includes('bed')) return '🛏️';
    if (l.includes('comfort')) return '🛋️';
    if (l.includes('location')) return '📍';
    if (l.includes('hair') || l.includes('salon') || l.includes('result') || l.includes('treatment')) return '💇';
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
    try { sessionStorage.setItem('nastaGharSelectedRating', String(s)); } catch {}
    logEvent('rating_selected', { rating: s });
  };

  const handleLanguageSelect = (langKey) => {
    setLanguage(langKey);
    try { sessionStorage.setItem('nastaGharSelectedLanguage', langKey); } catch {}
    logEvent('language_selected', { language: langKey });
    setIdeas(getFallbackIdeas(rating, personalNote, langKey));
  };

  const handleContinueReview = () => {
    setReviewStarted(true);
    setTimeout(() => {
      topicsSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 60);
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

  // Automatically keep ideas synchronized with rating, topics, language, and personal note
  useEffect(() => {
    // 1. Instant fallback update for 0ms perceived latency
    setIdeas(getFallbackIdeas(rating, personalNote, language));

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
            language,
            category: businessCategory,
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
  }, [rating, selectedTopics, nothingSpecific, personalNote, businessId, language, businessCategory]);

  // Begin the handoff from the customer's tap; clipboard access is requested immediately.
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
    logEvent('review_selected', { review_id: reviewId });
    logEvent('idea_selected', { idea_id: reviewId });
    logEvent('review_approved', { length: reviewText.length, direct_post: true });
    logEvent('google_review_handoff_started', { review_id: reviewId });

    try {
      sessionStorage.setItem('nastaGharSelectedReview', reviewText);
      sessionStorage.setItem('nastaGharSelectedRating', String(rating));
      sessionStorage.setItem('nastaGharSelectedReviewId', String(reviewId ?? ''));
      sessionStorage.setItem('nastaGharSelectedAt', new Date().toISOString());
      sessionStorage.setItem('nastaGharBusinessId', businessId);
      sessionStorage.setItem('nastaGharGoogleMapsDestination', googleReviewUrl);
    } catch {
      // Continue the handoff even when session storage is unavailable.
    }

    const copiedSuccessfully = await copyTextToClipboard(reviewText);
    setCopyingReview(false);
    setCopied(copiedSuccessfully);
    setShowCopyToast(true);
    setTimeout(() => setShowCopyToast(false), 3500);
    try { sessionStorage.setItem('nastaGharClipboardCopied', String(copiedSuccessfully)); } catch {}
    logEvent(copiedSuccessfully ? 'review_clipboard_success' : 'review_clipboard_failed', { review_id: reviewId });

    if (copiedSuccessfully) {
      logEvent('google_maps_redirect', { destination: googleReviewUrl });
      logEvent('google_review_link_opened');
      window.location.href = googleReviewUrl;
      return;
    }

    // Keep the exact review visible with a retry and an explicit Maps fallback CTA.
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
        {/* ── HEADER ─────────────────────────────────────────────────────── */}
        <header className="ng-header">
          <h1 className="ng-brand-name">નાસ્તા ઘર</h1>
          <p className="ng-brand-sub">Homestyle Breakfast & Chai • Rajkot</p>
          {tableParam && (
            <span className="ng-table-pill">📍 {tableParam}</span>
          )}
        </header>

        {/* ── SECTION 1: RATING ─────────────────────────────────────────── */}
        <section className="ng-section" aria-label="Rating selection">
          <h2 className="ng-section-title">How was your visit?</h2>
          <p className="ng-section-sub">Tap a star to rate your experience</p>

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

            {/* ── SECTION: LANGUAGE SELECTION ────────────────────────── */}
            <section className="ng-section ng-fade-in" aria-label="Language selection">
              <h2 className="ng-section-title">Which language feels most natural to you?</h2>
              <p className="ng-section-sub">Choose your preferred language for the review</p>

              <div className="ng-lang-row" role="radiogroup" aria-label="Review language">
                {[
                  { id: 'english', label: 'English' },
                  { id: 'hindi', label: 'Hindi' },
                  { id: 'gujarati', label: 'Gujarati' },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={`ng-lang-btn ${language === item.id ? 'active' : ''}`}
                    onClick={() => handleLanguageSelect(item.id)}
                    role="radio"
                    aria-checked={language === item.id}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </section>

            <div className="ng-section-divider" aria-hidden="true" />

            {/* ── SECTION 2: TOPICS / HIGHLIGHTS ────────────────────────────── */}
            <section ref={topicsSectionRef} className="ng-section ng-fade-in" aria-label="Visit highlights">
          <h2 className="ng-section-title">What stood out?</h2>
          <p className="ng-section-sub">Pick anything that matched your visit</p>

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
              Personal note <span className="ng-optional">(optional)</span>
            </label>
            <input
              id="ng-note"
              type="text"
              className="ng-note-input"
              placeholder="e.g. The poha was absolutely perfect! 😋"
              value={personalNote}
              onChange={(e) => setPersonalNote(e.target.value)}
              maxLength={100}
            />
          </div>
        </section>

        <div className="ng-section-divider" aria-hidden="true" />

        {/* ── SECTION 3: REVIEW IDEAS / CUSTOM EDITOR ───────────────────── */}
        {!showCustomEditor ? (
          <section className="ng-section" aria-label="Review suggestions">
            <div className="ng-ideas-header">
              <h2 className="ng-section-title">Review ideas</h2>
              <p className="ng-section-sub">
                Tap your favourite to copy & open Google Review
              </p>
              {loadingIdeas && (
                <div className="ng-updating-badge">
                  <span>✨</span>
                  <span>Refining ideas...</span>
                </div>
              )}
            </div>

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
                    <span className="ng-idea-num">Option {i + 1}</span>
                    <span className="ng-idea-lang">{getLanguageLabel(language)}</span>
                    <span className="ng-idea-stars">{'★'.repeat(rating)}</span>
                  </div>
                  <p className="ng-idea-text">"{idea.text}"</p>
                  <div className="ng-idea-action">
                    <span>Use this review →</span>
                  </div>
                </div>
              ))}
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

            {/* ── SECTION 4: PRIVATE FEEDBACK PROMPT ────────────────────────── */}
            <div className="ng-private-prompt">
              {rating <= 3 ? "Want to tell the team what could have been better? " : "Want to tell us privately? "}
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
                ? "તમારો review તૈયાર છે ✓ Google Maps માં 'Write a review' tap કરો, same stars select કરીને Paste કરો."
                : 'Review copy na thayu. Tap Copy Review to try again.'}
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
                ? <>તમારો review તૈયાર છે. Copy કરી રહ્યા છીએ અને Google Maps ખોલી રહ્યા છીએ…</>
                : copied
                ? <>તમારો review તૈયાર છે ✓ You selected {rating}★ here. On Google Maps, tap <strong>Write a review</strong>, select the same rating, then paste your review.</>
                : <>Review copy na thayu. Your selected review is saved for this browser session; copy it below and try again. You selected {rating}★ here, so choose the same rating on Google Maps.</>}
            </p>

            <div className="ng-modal-steps">
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">1</span>
                <span>Choose the rating that reflects your visit on Google (you selected <strong>{rating} stars</strong> here)</span>
              </div>
              <div className="ng-modal-step">
                <span className="ng-modal-step-num">2</span>
                <span>{copyingReview ? 'Copying selected review…' : copied ? <><strong>Paste</strong> the copied review (use your device's Paste command, or long-press → Paste on mobile)</> : <>Copy the review below, then <strong>paste</strong> it into Google</>}</span>
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
