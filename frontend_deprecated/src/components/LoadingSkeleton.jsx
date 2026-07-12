import React from 'react';
import { motion } from 'framer-motion';

const LoadingSkeleton = () => {
  return (
    <div className="w-full h-full flex flex-col gap-6 animate-pulse px-2">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="glass-panel h-28 p-5 flex flex-col justify-between">
            <div className="w-20 h-3 bg-border rounded"></div>
            <div className="w-12 h-6 bg-border rounded"></div>
          </div>
        ))}
      </div>
      
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-panel h-full min-h-[400px] p-6 flex flex-col gap-4">
          <div className="w-32 h-4 bg-border rounded mb-4"></div>
          <div className="w-full flex-1 bg-border/30 rounded-lg"></div>
        </div>
        <div className="glass-panel h-full min-h-[400px] p-6 flex flex-col gap-4">
          <div className="w-24 h-4 bg-border rounded mb-4"></div>
          {[...Array(6)].map((_, i) => (
            <div key={i} className="w-full h-10 bg-border/30 rounded-lg"></div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LoadingSkeleton;
