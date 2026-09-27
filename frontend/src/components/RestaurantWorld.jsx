import { useState } from 'react';
import './RestaurantWorld.css';

const guests = [
  [292,315,0],[350,305,1],[410,322,2],[470,305,3],[530,323,4],[590,305,5],[650,320,0],[710,305,2],
  [320,385,1],[380,372,4],[440,390,3],[500,370,0],[560,390,2],[620,372,1],[680,390,5],[740,372,4],
  [285,448,2],[345,438,5],[405,455,1],[465,438,4],[525,455,3],[585,438,0],[645,455,2],[705,438,1],
];
const servers = [
  [270,350,0],[325,410,1],[390,350,2],[455,420,3],[520,350,4],[585,420,5],
  [650,350,1],[715,420,2],[760,350,3],[350,465,4],[560,465,0],[700,465,5],
];
const shirts = ['#a83226','#2c6b43','#d28b25','#315a8c','#8d4d83','#397c76'];
const skin = ['#b9754c','#d99b70','#8c563d','#efbd91','#ad6a49','#e2a27a'];

function Person({ x, y, variant = 0, role = 'guest', onClick, label, delay = 0 }) {
  const isServer = role === 'server';
  const isChef = role === 'chef';
  const shirt = isChef ? '#f7f0dc' : isServer ? shirts[(variant + 1) % shirts.length] : shirts[variant % shirts.length];
  return (
    <g
      className={`ng-svg-person ng-svg-${role}`}
      transform={`translate(${x} ${y})`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      aria-label={label}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') onClick(); } : undefined}
      style={{ animationDelay: `${delay}s`, cursor: onClick ? 'pointer' : 'default' }}
    >
      {isServer && <ellipse cx="0" cy="0" rx="19" ry="5" fill="#342619" opacity=".16" />}
      <g className="ng-svg-body">
        <path d="M-12 20 Q-16 29 -13 43 L-8 45 L-5 30 L-3 48 L4 48 L6 30 L10 44 L15 42 L12 20Z" fill={isChef ? '#eee5cf' : '#3b3028'} stroke="#493322" strokeWidth="1.5"/>
        <path d="M-15 5 Q-18 10 -16 24 L-11 29 L-6 15 L6 15 L12 29 L17 24 L14 7 Q0 -1 -15 5Z" fill={shirt} stroke="#493322" strokeWidth="1.5"/>
        <path d="M-13 9 L-22 20 L-18 25 L-7 16 M13 9 L22 20 L18 25 L8 16" fill="none" stroke={skin[variant % skin.length]} strokeWidth="6" strokeLinecap="round"/>
        <ellipse cx="0" cy="-7" rx="12" ry="14" fill={skin[variant % skin.length]} stroke="#493322" strokeWidth="1.5"/>
        <path d={variant % 3 === 0 ? 'M-12 -8 Q-14 -25 0 -23 Q13 -24 12 -8 L7 -14 L-4 -16 L-10 -10Z' : 'M-12 -9 Q-15 -24 0 -23 Q13 -22 12 -7 L8 -14 L1 -12 L-5 -16 L-10 -8Z'} fill="#30241d"/>
        <circle cx="-4" cy="-6" r="1.25" fill="#30241d"/><circle cx="4" cy="-6" r="1.25" fill="#30241d"/>
        <path d="M-3 0 Q0 2 3 0" fill="none" stroke="#6b3527" strokeWidth="1.2" strokeLinecap="round"/>
        {isChef && <g><path d="M-12 -17 Q-17 -30 -7 -31 Q0 -40 8 -31 Q19 -30 12 -17Z" fill="#fff9e9" stroke="#493322" strokeWidth="1.5"/><path d="M-10 -16 L10 -16 L9 -11 L-9 -11Z" fill="#e7ddc7"/></g>}
        {isServer && <g className="ng-svg-tray-group"><path d="M-25 9 L25 9 L21 14 L-21 14Z" fill="#b78339" stroke="#493322" strokeWidth="1.5"/><ellipse cx="0" cy="8" rx="25" ry="4" fill="#f0d99a" stroke="#493322" strokeWidth="1.5"/><circle cx="-8" cy="6" r="3" fill="#b84c25"/><circle cx="1" cy="5" r="3" fill="#5c8b3c"/><circle cx="9" cy="6" r="3" fill="#e6b943"/></g>}
      </g>
    </g>
  );
}

export default function RestaurantWorld() {
  const [dialogue, setDialogue] = useState('');
  const [teaPour, setTeaPour] = useState(false);

  const speak = (text) => {
    setDialogue(text);
    window.setTimeout(() => setDialogue(''), 3600);
  };

  return (
    <section className="ng-world" aria-label="The living Nasta Ghar restaurant">
      <div className="ng-world-topline">
        <div className="ng-world-brand">
          <span className="ng-brand-seal">ન</span>
          <span><strong>NASTA GHAR</strong><small>ગરમાગરમ નાસ્તો • રાજકોટ</small></span>
        </div>
        <div className="ng-live-label"><i /> A LITTLE WORLD OF ITS OWN</div>
      </div>

      <div className="ng-scene-shell">
        <svg className="ng-scene-svg" viewBox="0 0 1000 560" preserveAspectRatio="none" role="group" aria-label="A lively Gujarati snack restaurant with a working kitchen, diners, servers, and Babalal Ni Chai stall">
          <defs>
            <linearGradient id="ngWall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#fff1cb"/><stop offset="1" stopColor="#e9c58a"/></linearGradient>
            <linearGradient id="ngFloor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#bd8650"/><stop offset="1" stopColor="#805033"/></linearGradient>
            <linearGradient id="ngGreen" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#275a32"/><stop offset="1" stopColor="#103820"/></linearGradient>
            <linearGradient id="ngStall" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#f7d99d"/><stop offset="1" stopColor="#d69b53"/></linearGradient>
            <pattern id="ngTiles" width="44" height="34" patternUnits="userSpaceOnUse"><path d="M44 0H0V34" fill="none" stroke="#b17b4c" strokeWidth="1" opacity=".22"/></pattern>
            <filter id="ngShadow" x="-30%" y="-30%" width="160%" height="180%"><feDropShadow dx="0" dy="5" stdDeviation="5" floodColor="#392516" floodOpacity=".24"/></filter>
          </defs>
          {/* warm, illustrated room */}
          <rect width="1000" height="560" fill="url(#ngWall)"/>
          <rect width="1000" height="355" fill="url(#ngTiles)"/>
          <path d="M0 345 H1000 V560 H0Z" fill="url(#ngFloor)"/>
          <path d="M0 365 H1000" stroke="#f8dfaa" strokeWidth="8"/>
          {Array.from({length:23},(_,i)=><path key={i} d={`M${i*46} 366 l-16 194`} stroke="#633e29" strokeWidth="2" opacity=".18"/>)}
          {/* back windows and wall details */}
          <g filter="url(#ngShadow)"><rect x="35" y="65" width="145" height="175" rx="5" fill="#805235"/><rect x="45" y="75" width="125" height="155" fill="#9ccfc6"/><path d="M107 75V230 M45 151H170" stroke="#fff0c8" strokeWidth="8"/><circle cx="143" cy="108" r="23" fill="#f7c44e"/><path d="M143 73V64 M143 143V151 M108 108H99 M178 108H187" stroke="#f7c44e" strokeWidth="4" strokeLinecap="round"/></g>
          <g><path d="M218 0V57 M500 0V48 M785 0V55" stroke="#805235" strokeWidth="4"/><g className="ng-lamp-left"><path d="M218 54 L198 82 H238Z" fill="#b57c34" stroke="#684525" strokeWidth="3"/><path d="M205 82H231L224 102H212Z" fill="#ffe08b"/><circle cx="218" cy="90" r="15" fill="#ffdf75" opacity=".3"/></g><g className="ng-lamp-center"><path d="M500 45L475 77H525Z" fill="#b57c34" stroke="#684525" strokeWidth="3"/><path d="M482 77H518L510 100H490Z" fill="#ffe08b"/></g><g className="ng-lamp-right"><path d="M785 52L765 80H805Z" fill="#b57c34" stroke="#684525" strokeWidth="3"/><path d="M772 80H798L791 100H779Z" fill="#ffe08b"/></g></g>
          <g filter="url(#ngShadow)"><rect x="315" y="36" width="370" height="80" rx="9" fill="#173b20" stroke="#c9ff00" strokeWidth="5"/><text x="500" y="75" textAnchor="middle" fontSize="30" fontWeight="900" fill="#f4f66a" letterSpacing="3">નાસ્તા ઘર</text><text x="500" y="99" textAnchor="middle" fontSize="11" fontWeight="700" fill="#fff8e8" letterSpacing="3">FRESH • HOT • HOMELY</text></g>
          {/* kitchen, left */}
          <g filter="url(#ngShadow)"><rect x="20" y="270" width="245" height="215" rx="9" fill="#dba96e" stroke="#71492d" strokeWidth="5"/><rect x="29" y="279" width="227" height="196" rx="4" fill="#f2d09a" stroke="#fff0c9" strokeWidth="3"/><rect x="44" y="295" width="196" height="14" rx="3" fill="#71492d"/><rect x="53" y="310" width="178" height="7" fill="#9a6a3e"/><g stroke="#71492d" strokeWidth="2.5" fill="#f7e8c5"><path d="M52 280H78L75 291Q65 298 55 291Z"/><path d="M100 278H123V293H100Z"/><path d="M103 275H120V279H103Z"/><ellipse cx="163" cy="286" rx="14" ry="6"/><ellipse cx="163" cy="286" rx="8" ry="3" fill="#e4a52e"/><path d="M194 291V279Q194 275 199 275H220Q225 275 225 280V291Z"/><path d="M199 275V270H220V275" fill="none"/></g><rect x="42" y="411" width="145" height="42" rx="7" fill="#593a28" stroke="#35251b" strokeWidth="3"/><rect x="52" y="405" width="125" height="9" rx="4" fill="#34241a"/><ellipse cx="112" cy="404" rx="42" ry="12" fill="#6f4a2d"/><ellipse cx="112" cy="398" rx="33" ry="8" fill="#d4d0bc" stroke="#493322" strokeWidth="3"/><ellipse cx="112" cy="397" rx="24" ry="5" fill="#e1a62c"/><g className="ng-burner-glow"><path d="M83 394 Q75 375 89 369 Q88 384 98 387 Q101 372 111 367 Q121 380 115 390 Q132 380 137 393Z" fill="#e96e25"/><path d="M98 392 Q95 382 106 377 Q113 386 109 392Z" fill="#ffe06c"/></g><path d="M150 397 Q145 376 157 363 Q169 376 163 393" fill="none" stroke="#fffdf1" strokeWidth="4" strokeLinecap="round" className="ng-steam-wisp-1"/><path d="M171 398 Q166 378 179 365" fill="none" stroke="#fffdf1" strokeWidth="3" strokeLinecap="round" className="ng-steam-wisp-2"/><rect x="35" y="457" width="216" height="17" rx="3" fill="#24542f"/><text x="143" y="469" textAnchor="middle" fontSize="10" fill="#f7f0d4" fontWeight="800" letterSpacing="1">KITCHEN • રસોડું</text></g>
          {/* central dining area */}
          <g><rect x="278" y="185" width="505" height="302" rx="10" fill="#f3d39c" stroke="#9a653d" strokeWidth="5"/><rect x="287" y="194" width="487" height="284" rx="7" fill="#e6bd7e"/><path d="M287 285H774 M287 378H774" stroke="#bd8b54" strokeWidth="2" opacity=".7"/><rect x="288" y="194" width="486" height="284" fill="url(#ngTiles)" opacity=".45"/></g>
          {/* dining tables */}
          {[[315,250],[470,250],[625,250],[315,355],[470,355],[625,355]].map(([x,y],i)=><g key={i} filter="url(#ngShadow)"><rect x={x} y={y} width="118" height="45" rx="8" fill="#71472c" stroke="#4d301f" strokeWidth="3"/><rect x={x+5} y={y+4} width="108" height="34" rx="5" fill="#986137"/><ellipse cx={x+36} cy={y+20} rx="17" ry="11" fill="#f7e9c7" stroke="#d5b87d" strokeWidth="2"/><ellipse cx={x+36} cy={y+20} rx="11" ry="6" fill="#e4a52e"/><circle cx={x+31} cy={y+19} r="3" fill="#4f853c"/><circle cx={x+41} cy={y+21} r="3" fill="#b84728"/><ellipse cx={x+81} cy={y+20} rx="10" ry="8" fill="#d9eee0" stroke="#fff" strokeWidth="2"/><path d={`M${x+12} ${y+44}v22 M${x+105} ${y+44}v22`} stroke="#4d301f" strokeWidth="7"/></g>)}
          {/* customers, 24 total */}
          {guests.map(([x,y,v],i)=><Person key={i} x={x} y={y} variant={v} role="guest" delay={i*.13}/>)}
          {/* servers, 12 total; all have food trays */}
          {servers.map(([x,y,v],i)=><Person key={i} x={x} y={y} variant={v} role="server" delay={i*.21} onClick={()=>speak(['હમણાં જ લાવું છું!','ગરમાગરમ નાસ્તો આવી ગયો!','બીજું કઈ લાવું, સાહેબ?'][i%3])} label={`Serving staff member ${i+1}`}/>)}
          {/* Chef Darshan is a prominent clickable focal point */}
          <g className="ng-chef-station" filter="url(#ngShadow)"><rect x="28" y="178" width="230" height="70" rx="8" fill="#173b20" stroke="#c9ff00" strokeWidth="3"/><text x="143" y="201" textAnchor="middle" fill="#f4f66a" fontSize="13" fontWeight="900" letterSpacing="1">CHEF DARSHAN</text><text x="143" y="222" textAnchor="middle" fill="#fff8e8" fontSize="11">મહારાજની રસોઈ</text></g>
          <Person x={214} y={350} variant={1} role="chef" onClick={()=>speak('બોલો ને મોટા ભાઈ, શું જમવું?')} label="Talk to Chef Darshan"/>
          {/* Babalal Ni Chai, right */}
          <g className="ng-tea-building" filter="url(#ngShadow)"><rect x="800" y="220" width="180" height="265" rx="7" fill="url(#ngStall)" stroke="#70462b" strokeWidth="5"/><rect x="808" y="229" width="164" height="247" fill="#f8dfad" stroke="#fff0c9" strokeWidth="2"/><rect x="792" y="202" width="196" height="56" rx="5" fill="#173b20" stroke="#c9ff00" strokeWidth="4"/><text x="890" y="225" textAnchor="middle" fontSize="14" fontWeight="900" fill="#f4f66a">BABALAL NI CHAI</text><text x="890" y="244" textAnchor="middle" fontSize="10" fontWeight="800" fill="#fff8e8">બાબાલાલ ની ચા</text><path d="M808 265H972L960 298H820Z" fill="#c9ff00" stroke="#173b20" strokeWidth="2"/><path d="M832 265L837 298 M865 265L870 298 M898 265L903 298 M931 265L936 298 M964 265L969 298" stroke="#173b20" strokeWidth="2"/><rect x="815" y="374" width="150" height="48" rx="4" fill="#71472c" stroke="#4d301f" strokeWidth="3"/><rect x="821" y="380" width="138" height="8" fill="#b78339"/><g fill="#fff0ce" stroke="#71472c" strokeWidth="2"><path d="M862 395H879L877 410H864Z"/><path d="M879 398Q888 397 884 405H878" fill="none"/><path d="M896 395H913L911 410H898Z"/><path d="M913 398Q922 397 918 405H912" fill="none"/></g><path d="M849 365 Q842 349 851 337 M878 365 Q871 345 880 330 M907 365 Q900 347 909 334" fill="none" stroke="#fffdf1" strokeWidth="3" strokeLinecap="round" className="ng-steam-wisp-chai"/><g className="ng-tea-pot"><path d="M925 352 Q944 345 950 361 L948 377 Q937 387 922 377Z" fill="#b84728" stroke="#633b27" strokeWidth="3"/><path d="M949 359 Q965 354 963 366 Q958 372 948 368" fill="none" stroke="#633b27" strokeWidth="4"/><path d="M924 357 Q911 354 913 366" fill="none" stroke="#633b27" strokeWidth="4"/></g><rect x="812" y="453" width="156" height="19" rx="3" fill="#173b20"/><text x="890" y="466" textAnchor="middle" fontSize="10" fill="#f4f66a" fontWeight="900">એક કટિંગ થઈ જાય!</text></g>
          <Person x={836} y={350} variant={2} role="server" delay={.4} onClick={()=>{setTeaPour(true);speak('એક કટિંગ ચા થઈ જાય! ☕');window.setTimeout(()=>setTeaPour(false),1600);}} label="Order tea from Babalal Ni Chai"/>
          {teaPour && <g className="ng-tea-pour"><path d="M925 371 Q936 389 931 402" fill="none" stroke="#8b4a20" strokeWidth="4" strokeLinecap="round"/><ellipse cx="932" cy="403" rx="7" ry="3" fill="#8b4a20"/></g>}
          {/* front fascia */}
          <rect x="0" y="500" width="1000" height="60" fill="#173b20"/>
          <path d="M0 500H1000" stroke="#c9ff00" strokeWidth="5"/>
          <text x="500" y="526" textAnchor="middle" fontSize="15" fontWeight="900" fill="#f4f66a" letterSpacing="3">નાસ્તા ઘર • રાજકોટ</text>
          <text x="500" y="546" textAnchor="middle" fontSize="10" fontWeight="700" fill="#fff8e8" letterSpacing="2">GARMA GARAM • DIL THI SEVA</text>
          {/* warm ambient floating motes */}
          {[[275,160],[365,145],[550,160],[720,150],[765,300],[300,470],[760,455]].map(([x,y],i)=><circle key={i} className={`ng-particle ng-p${i+1}`} cx={x} cy={y} r="3" fill="#f9d46a"/>)}
        </svg>
        {dialogue && <button className="ng-scene-dialogue" onClick={()=>setDialogue('')} aria-live="polite">{dialogue}<span>×</span></button>}
        <div className="ng-live-badge"><i /> <span>THE KITCHEN IS OPEN</span></div>
      </div>
      <div className="ng-world-caption"><span><b>👨🏽‍🍳</b> Meet Chef Darshan</span><span><b>🍽</b> Fresh from the kitchen</span><span><b>☕</b> Babalal Ni Chai</span></div>
    </section>
  );
}
