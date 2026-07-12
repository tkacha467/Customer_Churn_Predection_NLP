import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, TrendingDown, ShieldCheck, UserSearch, BrainCircuit } from 'lucide-react';
import { motion } from 'framer-motion';

const navItems = [
  { path: '/overview', name: 'Overview', icon: LayoutDashboard },
  { path: '/analysis', name: 'Churn Analysis', icon: TrendingDown },
  { path: '/integrity', name: 'Review Integrity', icon: ShieldCheck },
  { path: '/lookup', name: 'Customer Lookup', icon: UserSearch },
  { path: '/performance', name: 'Model Performance', icon: BrainCircuit },
];

const Sidebar = () => {
  return (
    <div className="w-20 lg:w-64 h-full bg-background border-r border-border flex flex-col transition-all duration-300 z-20">
      <div className="h-16 flex items-center justify-center lg:justify-start lg:px-6 border-b border-border">
        <div className="font-syne font-bold text-xl tracking-tight text-white flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-primary text-background flex items-center justify-center text-sm font-bold">C</div>
          <span className="hidden lg:inline">ChurnLens</span>
        </div>
      </div>
      
      <div className="flex-1 py-6 px-4 flex flex-col gap-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => 
              `relative flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors text-sm font-medium ${
                isActive ? 'text-primary' : 'text-gray-400 hover:text-white hover:bg-surface-hover'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.div
                    layoutId="active-nav"
                    className="absolute inset-0 bg-primary/10 rounded-md border border-primary/20"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
                <item.icon className={`w-4 h-4 relative z-10 ${isActive ? 'text-primary' : 'text-gray-500'}`} />
                <span className="hidden lg:block relative z-10">{item.name}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </div>
  );
};

export default Sidebar;
