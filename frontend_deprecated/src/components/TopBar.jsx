import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const pageTitles = {
  '/overview': 'Overview',
  '/analysis': 'Churn Analysis',
  '/integrity': 'Review Integrity',
  '/lookup': 'Customer Lookup',
  '/performance': 'Model Performance',
};

const TopBar = () => {
  const location = useLocation();
  const title = pageTitles[location.pathname] || 'Dashboard';
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="h-16 bg-background border-b border-border flex items-center justify-between px-8 z-10 sticky top-0">
      <div className="flex items-center gap-4">
        <h1 className="font-syne font-semibold text-lg text-white">{title}</h1>
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-surface border border-border">
          <div className="w-1.5 h-1.5 rounded-full bg-success animate-pulse"></div>
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Live Demo</span>
        </div>
      </div>
      <div className="text-[11px] text-gray-500 uppercase tracking-widest font-medium">
        Updated: {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </div>
    </header>
  );
};

export default TopBar;
