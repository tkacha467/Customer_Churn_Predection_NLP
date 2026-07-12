import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const RiskBadge = ({ riskCategory, className }) => {
  const category = (riskCategory || '').toUpperCase();
  
  let colorStyles = '';
  
  if (category === 'HIGH') {
    colorStyles = 'bg-danger/10 text-danger border-danger/20';
  } else if (category === 'MEDIUM') {
    colorStyles = 'bg-warning/10 text-warning border-warning/20';
  } else if (category === 'LOW') {
    colorStyles = 'bg-success/10 text-success border-success/20';
  } else {
    colorStyles = 'bg-gray-500/10 text-gray-400 border-gray-500/20';
  }

  return (
    <span className={cn('px-2.5 py-1 rounded-full border text-xs font-bold tracking-wider', colorStyles, className)}>
      {category || 'UNKNOWN'}
    </span>
  );
};

export default RiskBadge;
