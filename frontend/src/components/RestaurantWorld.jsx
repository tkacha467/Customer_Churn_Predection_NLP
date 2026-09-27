import { useEffect, useRef, useState } from 'react';
import './RestaurantWorld.css';

export default function RestaurantWorld() {
  const [dialogue, setDialogue] = useState(null);
  const [teaActive, setTeaActive] = useState(false);
  const [pageActive, setPageActive] = useState(() => document.visibilityState === 'visible');
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

  const speak = (text, position) => {
    setDialogue({ text, position });
    window.clearTimeout(dialogueTimer.current);
    dialogueTimer.current = window.setTimeout(() => setDialogue(null), 2800);
  };

  const orderTea = () => {
    setTeaActive(true);
    speak('ચા પીશો મોટા ભાઈ?', { x: 76, y: 34 });
    window.clearTimeout(teaTimer.current);
    teaTimer.current = window.setTimeout(() => setTeaActive(false), 1700);
  };

  return (
    <section className={`ng-world${teaActive ? ' is-tea-active' : ''}`} data-active={pageActive} aria-label="Nasta Ghar, a Gujarati restaurant">
      <div className="ng-room-image ng-room-image-phone" aria-hidden="true" />
      <div className="ng-room-image ng-room-image-desktop" aria-hidden="true" />
      <div className="ng-room-ambient" aria-hidden="true" />

      <header className="ng-world-brand"><span>નાસ્તા ઘર</span></header>
      <div className="ng-tea-sign" aria-label="Babalal Ni Chai"><span>બાબાલાલ ની ચા</span><small>BABALAL NI CHAI</small></div>

      <div className="ng-steam ng-steam-kitchen" aria-hidden="true"><i /><i /></div>
      <div className="ng-steam ng-steam-chai" aria-hidden="true"><i /><i /><i /></div>

      <div className="ng-scene-hotspots" aria-label="Explore the restaurant">
        <button className="ng-hotspot ng-hotspot-kitchen" type="button" aria-label="See the cooks make fresh chapatis" onClick={() => speak('ગરમાગરમ રોટલી તૈયાર છે!', { x: 24, y: 35 })} />
        <button className="ng-hotspot ng-hotspot-chef" type="button" aria-label="Talk to Chef Darshan" onClick={() => speak('બોલો ને મોટા ભાઈ, શું જમવું?', { x: 38, y: 27 })} />
        <button className="ng-hotspot ng-hotspot-dining" type="button" aria-label="Tap a dining table to interact" onClick={() => speak('ભાઈ, અહીં ગરમાગરમ નાસ્તો મોકલશો?', { x: 54, y: 36 })} />
        <button className="ng-hotspot ng-hotspot-server" type="button" aria-label="Talk to a server" onClick={() => speak('લાવો મોટા ભાઈ, ગરમાગરમ જમવાનું!', { x: 47, y: 28 })} />
        <button className="ng-hotspot ng-hotspot-chai" type="button" aria-label="Order tea from Babalal Ni Chai" onClick={orderTea} />
      </div>

      {dialogue && (
        <div className="ng-scene-dialogue" style={{ '--bubble-x': `${dialogue.position.x}%`, '--bubble-y': `${dialogue.position.y}%` }} role="status" aria-live="polite">
          {dialogue.text}
        </div>
      )}
    </section>
  );
}
