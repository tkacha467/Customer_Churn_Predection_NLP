import React, { useEffect, useState } from 'react';
import { motion, useInView } from 'framer-motion';

const StatCard = ({ title, value, prefix = '', suffix = '', icon: Icon, colorClass = 'text-white' }) => {
  const [displayValue, setDisplayValue] = useState(0);
  const ref = React.useRef(null);
  const inView = useInView(ref, { once: true, margin: "-50px" });
  
  useEffect(() => {
    if (inView && typeof value === 'number') {
      let startTimestamp = null;
      const duration = 1200; 
      
      const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const easeProgress = 1 - Math.pow(1 - progress, 3);
        setDisplayValue(value * easeProgress);
        if (progress < 1) window.requestAnimationFrame(step);
      };
      
      window.requestAnimationFrame(step);
    } else if (inView && typeof value !== 'number') {
      setDisplayValue(value);
    }
  }, [inView, value]);

  const formattedValue = typeof value === 'number' 
    ? (value % 1 === 0 ? Math.floor(displayValue).toLocaleString() : displayValue.toFixed(1))
    : displayValue;

  return (
    <motion.div 
      ref={ref}
      initial={{ opacity: 0, y: 10 }}
      animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
      transition={{ duration: 0.4 }}
      className="glass-panel p-5 flex flex-col justify-between"
    >
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-gray-400 font-semibold text-[11px] uppercase tracking-widest">{title}</h3>
        {Icon && (
          <div className="w-6 h-6 rounded flex items-center justify-center bg-white/5 border border-white/5">
            <Icon className={`w-3.5 h-3.5 ${colorClass}`} />
          </div>
        )}
      </div>
      
      <div className="flex items-baseline gap-1 font-syne font-semibold text-3xl">
        {prefix && <span className="text-sm text-gray-500 font-dmsans">{prefix}</span>}
        <span className="text-white">{formattedValue}</span>
        {suffix && <span className="text-sm text-gray-500 font-dmsans">{suffix}</span>}
      </div>
    </motion.div>
  );
};

export default StatCard;
