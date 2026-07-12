import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Users, AlertTriangle, UserMinus, Activity, ShieldAlert } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts';
import { useData } from '../hooks/useDataContext';
import StatCard from '../components/StatCard';
import RiskBadge from '../components/RiskBadge';

const Overview = () => {
  const { data } = useData();
  const { riskScores } = data;

  const stats = useMemo(() => {
    if (!riskScores) return null;
    
    let totalRisk = 0;
    let highRiskCount = 0;
    let mediumRiskCount = 0;
    let lowRiskCount = 0;
    let churnedCount = 0;

    riskScores.forEach(row => {
      totalRisk += (row.risk_score || 0);
      if (row.risk_category === 'HIGH') highRiskCount++;
      else if (row.risk_category === 'MEDIUM') mediumRiskCount++;
      else if (row.risk_category === 'LOW') lowRiskCount++;
      
      if (row.churn === 1) churnedCount++;
    });

    const avgRisk = totalRisk / riskScores.length;

    return {
      totalCustomers: riskScores.length,
      avgRisk,
      highRiskCount,
      mediumRiskCount,
      lowRiskCount,
      churnedCount
    };
  }, [riskScores]);

  if (!stats) return null;

  const pieData = [
    { name: 'High Risk', value: stats.highRiskCount, color: '#ff453a' },
    { name: 'Medium Risk', value: stats.mediumRiskCount, color: '#ffd60a' },
    { name: 'Low Risk', value: stats.lowRiskCount, color: '#32d74b' },
  ];

  const recentHighRisks = riskScores.filter(r => r.risk_category === 'HIGH').slice(0, 10);

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto w-full">
      {/* Clean Minimal Hero */}
      <motion.div 
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
        className="pt-2 pb-4 border-b border-border"
      >
        <h1 className="font-syne font-semibold text-3xl text-white mb-2 tracking-tight">Platform Overview</h1>
        <p className="text-gray-400 text-sm max-w-2xl leading-relaxed">
          Monitor customer risk distributions and predictive churn analytics in real time.
        </p>
      </motion.div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Customers" value={stats.totalCustomers} icon={Users} colorClass="text-white" />
        <StatCard title="Average Risk Score" value={stats.avgRisk * 100} suffix="%" icon={Activity} colorClass="text-accent" />
        <StatCard title="High Risk Accounts" value={stats.highRiskCount} icon={AlertTriangle} colorClass="text-danger" />
        <StatCard title="Total Churned" value={stats.churnedCount} icon={UserMinus} colorClass="text-warning" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Risk Donut Chart */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.4, delay: 0.1 }}
          className="xl:col-span-1 glass-panel p-6 flex flex-col min-h-[360px]"
        >
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-syne font-semibold text-[15px] text-gray-200">Risk Distribution</h3>
          </div>
          <div className="flex-1 w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={70} outerRadius={90} paddingAngle={2} dataKey="value" stroke="none" animationDuration={1000}>
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip 
                  cursor={false}
                  contentStyle={{ backgroundColor: '#000', borderColor: '#222', borderRadius: '6px', fontSize: '13px', padding: '8px 12px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}
                  itemStyle={{ color: '#fff', fontSize: '13px', fontWeight: 500 }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-2xl font-syne font-bold text-white">{stats.totalCustomers.toLocaleString()}</span>
              <span className="text-[10px] text-gray-500 uppercase tracking-widest mt-1">Total</span>
            </div>
          </div>
        </motion.div>

        {/* Risk Category breakdown */}
        <div className="xl:col-span-2 flex flex-col gap-4">
          <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 }} className="glass-panel flex-1 p-5 flex items-center justify-between border-l-2 border-l-danger hover:bg-surface-hover transition-colors">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-danger/10 border border-danger/20 flex items-center justify-center"><AlertTriangle className="w-4 h-4 text-danger"/></div>
              <div>
                <h4 className="font-syne font-bold text-sm text-white mb-0.5">High Risk</h4>
                <p className="text-gray-500 text-[13px]">Requires immediate intervention</p>
              </div>
            </div>
            <div className="text-3xl font-semibold font-syne text-white">{stats.highRiskCount.toLocaleString()}</div>
          </motion.div>
          
          <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }} className="glass-panel flex-1 p-5 flex items-center justify-between border-l-2 border-l-warning hover:bg-surface-hover transition-colors">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-warning/10 border border-warning/20 flex items-center justify-center"><Activity className="w-4 h-4 text-warning"/></div>
              <div>
                <h4 className="font-syne font-bold text-sm text-white mb-0.5">Medium Risk</h4>
                <p className="text-gray-500 text-[13px]">Monitor closely for behavioral changes</p>
              </div>
            </div>
            <div className="text-3xl font-semibold font-syne text-white">{stats.mediumRiskCount.toLocaleString()}</div>
          </motion.div>
          
          <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.25 }} className="glass-panel flex-1 p-5 flex items-center justify-between border-l-2 border-l-success hover:bg-surface-hover transition-colors">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-success/10 border border-success/20 flex items-center justify-center"><ShieldAlert className="w-4 h-4 text-success"/></div>
              <div>
                <h4 className="font-syne font-bold text-sm text-white mb-0.5">Low Risk</h4>
                <p className="text-gray-500 text-[13px]">Stable customer behavior</p>
              </div>
            </div>
            <div className="text-3xl font-semibold font-syne text-white">{stats.lowRiskCount.toLocaleString()}</div>
          </motion.div>
        </div>
      </div>

      {/* Live Ticker minimal styling */}
      <div className="mt-4 rounded-lg bg-surface border border-border h-10 flex items-center overflow-hidden relative">
        <div className="absolute left-0 z-10 bg-gradient-to-r from-surface to-transparent w-16 h-full"></div>
        <div className="absolute right-0 z-10 bg-gradient-to-l from-surface to-transparent w-16 h-full"></div>
        <div className="flex items-center absolute whitespace-nowrap animate-ticker">
          {[...recentHighRisks, ...recentHighRisks, ...recentHighRisks].map((risk, idx) => (
            <div key={idx} className="flex items-center gap-2 mx-6 text-[13px] font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-danger animate-pulse"></span>
              <span className="text-gray-400">ID:</span>
              <span className="text-gray-200 font-mono text-xs">{risk.customer_unique_id}</span>
              <span className="text-danger ml-2">{(risk.risk_score * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>
      </div>
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes ticker {
          0% { transform: translateX(0); }
          100% { transform: translateX(-33.33%); }
        }
        .animate-ticker {
          animation: ticker 40s linear infinite;
        }
      `}} />
    </div>
  );
};

export default Overview;
