import { useEffect, useRef, useState } from 'react';

/**
 * VajraIntroLoader
 *
 * Sequence requirements:
 * 0.0s        Original VAJRA logo appears very close to the viewer.
 * 0.2s - 0.5s Logo subtly stabilizes / breathes.
 * 0.5s - 1.0s Smooth cinematic ZOOM-OUT reveals world & content behind.
 * 1.0s - 1.2s Loader transitions seamlessly into the hero.
 * 1.2s - 1.4s Completely removed from DOM.
 * Target duration: ~1.2s - 1.4s max.
 */
export default function VajraIntroLoader({ onComplete }) {
  const [stage, setStage] = useState('initial');
  const completeRef = useRef(onComplete);
  completeRef.current = onComplete;

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setStage('done');
      completeRef.current?.();
      return undefined;
    }
    // 0.2s: transition to breathing
    const t1 = setTimeout(() => {
      setStage('breathing');
    }, 200);

    // 0.5s: zoom-out commences
    const t2 = setTimeout(() => {
      setStage('zoomout');
    }, 520);

    // 1.05s: fade out veil
    const t3 = setTimeout(() => {
      setStage('fading');
    }, 1050);

    // 1.35s: remove from DOM
    const t4 = setTimeout(() => {
      setStage('done');
      completeRef.current?.();
    }, 1350);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
    };
  }, []);

  if (stage === 'done') return null;

  return (
    <div
      className={`vajra-loader-overlay ${stage}`}
      aria-hidden="true"
      role="presentation"
    >
      <div className="vajra-loader-backdrop" />
      <div className="vajra-loader-rings">
        <div className="loader-ring loader-ring-1" />
        <div className="loader-ring loader-ring-2" />
      </div>
      <div className="vajra-loader-content">
        <div className="vajra-loader-logo-wrapper">
          <img
            src="/vajra-logo.png"
            alt="VAJRA"
            className="vajra-loader-logo"
            draggable="false"
          />
        </div>
        <div className="vajra-loader-aura" />
      </div>
    </div>
  );
}
