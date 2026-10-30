import { useEffect, useRef, useState } from 'react';
import './RestaurantWorld.css';

const DARSHAN_GREETINGS = [
  'કેમ ભાઈ, જમવામાં કેવી મજા આવી?',
  'બોલો ને મોટા ભાઈ, શું જમવું ગમ્યું?',
  'જમવાનું ભાવ્યું ને? દિલથી બનાવ્યું છે!',
  'નાસ્તા ઘરમાં ફરી આવજો હો!',
  'તમારો દિવસ મજાનો જાય, ફરી મળીએ!',
];

export default function RestaurantWorld() {
  const [dialogue, setDialogue] = useState(null);
  const [teaActive, setTeaActive] = useState(false);
  const [pageActive, setPageActive] = useState(() => document.visibilityState === 'visible');
  const [greetingIndex, setGreetingIndex] = useState(0);
  const dialogueTimer = useRef(null);
  const teaTimer = useRef(null);

  useEffect(() => () => {
    window.clearTimeout(dialogueTimer.current);
    window.clearTimeout(teaTimer.current);
  }, []);

  useEffect(() => {
    const updateVisibility = () => setPageActive(document.visibilityState === 'visible');
    document.addEventListener('visibilitychange', updateVisibility);
    return () => document.removeEventListener('visibilitychange', updateVisibility);
  }, []);

  const speak = (target, text, speaker = null) => {
    setDialogue({ target, text, speaker });
    window.clearTimeout(dialogueTimer.current);
    dialogueTimer.current = window.setTimeout(() => setDialogue(null), 3200);
  };

  const handleDarshanClick = () => {
    const text = DARSHAN_GREETINGS[greetingIndex];
    setGreetingIndex((prev) => (prev + 1) % DARSHAN_GREETINGS.length);
    speak('darshan', text, 'દર્શનભાઈ');
  };

  const orderTea = () => {
    setTeaActive(true);
    speak('chai', 'ચા પીશો મોટા ભાઈ?', 'બાબાલાલ');
    window.clearTimeout(teaTimer.current);
    teaTimer.current = window.setTimeout(() => setTeaActive(false), 1900);
  };

  return (
    <section
      className={`ng-world${teaActive ? ' is-tea-active' : ''}`}
      data-active={pageActive}
      aria-label="Nasta Ghar, a Gujarati restaurant"
    >
      <div className="ng-scene-stage">
        <div className="ng-scene-viewport">
          <img
            src="/restaurant/scene-phone.webp"
            alt=""
            className="ng-scene-img ng-scene-img-phone"
            aria-hidden="true"
          />
          <img
            src="/restaurant/scene-wide.webp"
            alt=""
            className="ng-scene-img ng-scene-img-desktop"
            aria-hidden="true"
          />
          <div className="ng-room-ambient" aria-hidden="true" />

          <header className="ng-world-brand"><span>નાસ્તા ઘર</span></header>
          <div className="ng-tea-sign" aria-label="Babalal Ni Chai">
            <span>બાબાલાલ ની ચા</span>
            <small>BABALAL NI CHAI</small>
          </div>

          <div className="ng-steam ng-steam-kitchen" aria-hidden="true"><i /><i /></div>
          <div className="ng-steam ng-steam-chai" aria-hidden="true"><i /><i /><i /></div>

          {/* Interactive Darshan Bhai Host */}
          <button
            className="ng-darshan-host"
            type="button"
            aria-label="Darshan Bhai — hear a greeting"
            onClick={handleDarshanClick}
          >
            {dialogue?.target === 'darshan' && (
              <div
                className="ng-host-dialogue"
                role="status"
                aria-live="polite"
              >
                <span className="ng-dialogue-speaker">{dialogue.speaker}</span>
                <span className="ng-dialogue-text">{dialogue.text}</span>
              </div>
            )}
            <img
              src="/restaurant/darshan-host.png"
              alt="Darshan Bhai"
              className="ng-darshan-img"
              draggable="false"
            />
            <span className="ng-darshan-shadow" aria-hidden="true" />
          </button>

          {/* Hotspots with directly anchored speech bubbles */}
          <div className="ng-scene-hotspots" aria-label="Explore the restaurant">
            {/* Kitchen Roti Cook */}
            <button
              className="ng-hotspot ng-hotspot-kitchen"
              type="button"
              aria-label="See the cooks make fresh chapatis"
              onClick={() => speak('kitchen', 'ગરમાગરમ રોટલી તૈયાર છે!', 'રસોડું')}
            >
              {dialogue?.target === 'kitchen' && (
                <div
                  className="ng-hotspot-dialogue ng-dialogue-kitchen"
                  role="status"
                  aria-live="polite"
                >
                  <span className="ng-dialogue-speaker">{dialogue.speaker}</span>
                  <span className="ng-dialogue-text">{dialogue.text}</span>
                </div>
              )}
            </button>

            {/* Dining Guests */}
            <button
              className="ng-hotspot ng-hotspot-dining"
              type="button"
              aria-label="Tap a dining table to interact"
              onClick={() => speak('dining', 'ભાઈ, અહીં ગરમાગરમ નાસ્તો મોકલશો?', 'ગ્રાહક')}
            >
              {dialogue?.target === 'dining' && (
                <div
                  className="ng-hotspot-dialogue ng-dialogue-dining"
                  role="status"
                  aria-live="polite"
                >
                  <span className="ng-dialogue-speaker">{dialogue.speaker}</span>
                  <span className="ng-dialogue-text">{dialogue.text}</span>
                </div>
              )}
            </button>

            {/* Server */}
            <button
              className="ng-hotspot ng-hotspot-server"
              type="button"
              aria-label="Talk to a server"
              onClick={() => speak('server', 'લાવો મોટા ભાઈ, ગરમાગરમ જમવાનું!', 'પીરસનાર')}
            >
              {dialogue?.target === 'server' && (
                <div
                  className="ng-hotspot-dialogue ng-dialogue-server"
                  role="status"
                  aria-live="polite"
                >
                  <span className="ng-dialogue-speaker">{dialogue.speaker}</span>
                  <span className="ng-dialogue-text">{dialogue.text}</span>
                </div>
              )}
            </button>

            {/* Babalal Chai Stall */}
            <button
              className="ng-hotspot ng-hotspot-chai"
              type="button"
              aria-label="Order tea from Babalal Ni Chai"
              onClick={orderTea}
            >
              {dialogue?.target === 'chai' && (
                <div
                  className="ng-hotspot-dialogue ng-dialogue-chai"
                  role="status"
                  aria-live="polite"
                >
                  <span className="ng-dialogue-speaker">{dialogue.speaker}</span>
                  <span className="ng-dialogue-text">{dialogue.text}</span>
                </div>
              )}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
