import { lazy, Suspense, useState } from 'react';
import './VajraDesignSystem.css';
import VajraIntroLoader from './components/VajraIntroLoader';
import VajraNavbar from './components/VajraNavbar';
import VajraExperience from './components/VajraExperience';

const VajraCanvas = lazy(() => import('./components/VajraCanvas'));

function App() {
  const [introCompleted, setIntroCompleted] = useState(false);

  return (
    <div className="vajra-app-viewport">
      {!introCompleted && <VajraIntroLoader onComplete={() => setIntroCompleted(true)} />}
      <Suspense fallback={null}>
        <VajraCanvas />
      </Suspense>
      <div className="vajra-atmospheric-gradient" aria-hidden="true" />
      <div className="vajra-vignette-overlay" aria-hidden="true" />
      <VajraNavbar />
      <main>
        <VajraExperience />
      </main>
    </div>
  );
}

export default App;
