import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import Overview from './pages/Overview';
import ChurnAnalysis from './pages/ChurnAnalysis';
import ReviewIntegrity from './pages/ReviewIntegrity';
import CustomerLookup from './pages/CustomerLookup';
import ModelPerformance from './pages/ModelPerformance';
import LoadingSkeleton from './components/LoadingSkeleton';
import { useData } from './hooks/useDataContext';

function App() {
  const { loading, error } = useData();

  return (
    <Router>
      <div className="flex h-screen bg-background overflow-hidden font-dmsans text-white">
        <Sidebar />
        <div className="flex-1 flex flex-col relative overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-y-auto p-6 scroll-smooth">
            {error ? (
              <div className="p-8 text-danger bg-danger/10 border border-danger/20 rounded-xl">
                <h2 className="font-syne font-bold text-xl mb-2">Failed to load data</h2>
                <p>{error.message}</p>
              </div>
            ) : loading ? (
              <LoadingSkeleton />
            ) : (
              <Routes>
                <Route path="/" element={<Navigate to="/overview" replace />} />
                <Route path="/overview" element={<Overview />} />
                <Route path="/analysis" element={<ChurnAnalysis />} />
                <Route path="/integrity" element={<ReviewIntegrity />} />
                <Route path="/lookup" element={<CustomerLookup />} />
                <Route path="/performance" element={<ModelPerformance />} />
              </Routes>
            )}
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
