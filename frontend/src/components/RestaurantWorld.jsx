import { useState } from 'react';
import './RestaurantWorld.css';

const servers = Array.from({ length: 12 }, (_, i) => ({
  id: i + 1,
  x: [14, 22, 30, 38, 46, 54, 62, 70, 78, 84, 58, 34][i],
  y: [63, 73, 58, 76, 65, 79, 59, 72, 62, 77, 49, 50][i],
  delay: (i * 0.73) % 5,
}));
const guests = Array.from({ length: 24 }, (_, i) => ({
  id: i + 1,
  x: [18, 28, 39, 50, 61, 72, 82, 22, 34, 46, 58, 70, 80, 16, 30, 43, 55, 67, 78, 25, 38, 52, 64, 75][i],
  y: [43, 45, 42, 45, 42, 44, 43, 52, 54, 51, 54, 52, 54, 61, 62, 60, 62, 60, 62, 69, 70, 68, 70, 68][i],
  delay: (i * 0.41) % 4,
}));

export default function RestaurantWorld() {
  const [dialogue, setDialogue] = useState('');
  const [active, setActive] = useState('');
  const [teaPour, setTeaPour] = useState(false);

  const greetChef = () => {
    setActive('chef');
    setDialogue('બોલો ને મોટા ભાઈ, શું જમવું?');
    window.setTimeout(() => setActive(''), 1100);
  };
  const interact = (name, text) => {
    setActive(name);
    setDialogue(text);
    window.setTimeout(() => setActive(''), 1100);
  };

  return (
    <section className="ng-world" aria-label="Animated Nasta Ghar restaurant">
      <div className="ng-world-sky">
        <div className="ng-world-header">
          <div className="ng-world-brand"><span className="ng-brand-mark">NG</span><div><strong>NASTA GHAR</strong><small>ગરમ નાસ્તો • દિલથી સેવા</small></div></div>
          <span className="ng-world-live"><i /> LIVE RESTAURANT</span>
        </div>
        <div className="ng-world-scene">
          <div className="ng-back-wall">
            <div className="ng-window"><span>☀</span></div>
            <div className="ng-wall-sign">નાસ્તા ઘર <small>FRESH • HOT • HOMELY</small></div>
            <div className="ng-wall-lamp lamp-one">✦</div><div className="ng-wall-lamp lamp-two">✦</div>
          </div>
          <div className="ng-kitchen">
            <div className="ng-area-sign">KITCHEN · રસોડું</div>
            <div className="ng-shelf"><span>🥣</span><span>🫙</span><span>🍽️</span><span>🥘</span></div>
            <div className="ng-stove"><span className="ng-flame">♨</span><span className="ng-pot">🍲</span><span className="ng-steam">〰</span></div>
            <button className={`ng-character ng-chef ${active === 'chef' ? 'is-active' : ''}`} onClick={greetChef} aria-label="Talk to Chef Darshan">
              <span className="ng-char-sprite">👨🏽‍🍳</span><span className="ng-char-name">DARSHAN</span>
            </button>
            {dialogue && <button className="ng-speech" onClick={() => setDialogue('')} aria-label="Dismiss chef dialogue">{dialogue}<span> ×</span></button>}
          </div>
          <div className="ng-dining">
            <div className="ng-area-sign">DINING · જમવાની જગ્યા</div>
            {[0,1,2,3].map((n) => <div className={`ng-table table-${n}`} key={n}><span className="ng-plate">🍛</span><span className="ng-glass">🥛</span><i /><b /></div>)}
            {guests.map((g) => <button key={g.id} className="ng-character ng-guest" style={{ left: g.x + '%', top: g.y + '%', animationDelay: `${g.delay}s` }} onClick={() => interact(`guest-${g.id}`, 'આવજો! જમવાની મજા માણો.')} aria-label={`Restaurant guest ${g.id}`}><span className="ng-char-sprite">{['🧔🏽','👩🏽','👨🏻','👩🏻','🧑🏽','👨🏾'][g.id % 6]}</span></button>)}
            {servers.map((s) => <button key={s.id} className="ng-character ng-server" style={{ left: s.x + '%', top: s.y + '%', animationDelay: `${s.delay}s` }} onClick={() => interact(`server-${s.id}`, 'હમણાં જ લાવું છું!')} aria-label={`Serving staff member ${s.id}`}><span className="ng-char-sprite">🧑🏽‍🍳</span><span className="ng-tray">🍽️</span></button>)}
          </div>
          <div className="ng-tea-stall">
            <div className="ng-tea-sign">BABALAL NI CHAI<small>બાબાલાલ ની ચા</small></div>
            <div className="ng-tea-awning"><i/><i/><i/><i/><i/></div>
            <div className="ng-tea-counter"><span className={teaPour ? 'ng-kettle pouring' : 'ng-kettle'}>🫖</span><span>☕ ☕</span></div>
            <button className="ng-character ng-tea-worker" onClick={() => { setTeaPour(true); interact('tea', 'એક કટિંગ ચા થઈ જાય! ☕'); window.setTimeout(() => setTeaPour(false), 1500); }} aria-label="Order tea at Babalal Ni Chai"><span className="ng-char-sprite">👨🏽</span><span className="ng-char-name">CHAI</span></button>
            <div className="ng-tea-steam">〰 〰</div>
          </div>
          <div className="ng-floor"><span>નાસ્તા ઘર</span><span>ગરમાગરમ • સ્વાદિષ્ટ</span><span>☘</span></div>
        </div>
        <div className="ng-world-hint"><span className="ng-pulse-dot" /> Tap Chef Darshan, a server, or Babalal Ni Chai</div>
      </div>
    </section>
  );
}
