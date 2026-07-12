import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, User, AlertCircle, DollarSign, Calendar, Clock, Star } from 'lucide-react';
import { useData } from '../hooks/useDataContext';
import RiskBadge from '../components/RiskBadge';

const CustomerLookup = () => {
  const { data } = useData();
  const { riskScores, churnPredictions, integrityScores, rfmFeatures } = data;

  const [searchTerm, setSearchTerm] = useState('');
  const [searchedId, setSearchedId] = useState('');
  const [sortField, setSortField] = useState('riskScore');
  const [sortDir, setSortDir] = useState('desc');

  const handleSearch = (e) => {
    e.preventDefault();
    setSearchedId(searchTerm.trim());
  };

  const customerData = useMemo(() => {
    if (!searchedId) return null;
    const r = riskScores.find(x => x.customer_unique_id === searchedId);
    if (!r) return null;
    
    const cp = churnPredictions.find(x => x.customer_unique_id === searchedId) || {};
    const it = integrityScores.find(x => x.customer_unique_id === searchedId) || {};
    const rfm = rfmFeatures.find(x => x.customer_unique_id === searchedId) || {};

    return { ...r, ...cp, ...it, ...rfm };
  }, [searchedId, riskScores, churnPredictions, integrityScores, rfmFeatures]);

  const top10 = useMemo(() => {
    if (!riskScores) return [];
    
    const tableData = riskScores.map(r => {
      const it = integrityScores.find(x => x.customer_unique_id === r.customer_unique_id) || {};
      const cp = churnPredictions.find(x => x.customer_unique_id === r.customer_unique_id) || {};
      return {
        id: r.customer_unique_id,
        riskScore: r.risk_score || 0,
        riskCategory: r.risk_category,
        monetary: r.monetary || 0,
        integrityScore: it.avg_integrity_score || 0,
        churnProb: cp.churn_probability || 0
      };
    });

    const highestRisk = [...tableData].sort((a,b) => b.riskScore - a.riskScore).slice(0, 10);
    
    highestRisk.sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];
      if (valA < valB) return sortDir === 'asc' ? -1 : 1;
      if (valA > valB) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });

    return highestRisk;
  }, [riskScores, integrityScores, churnPredictions, sortField, sortDir]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto w-full pb-10">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="pt-2 pb-4 border-b border-border">
        <h1 className="font-syne font-semibold text-3xl text-white mb-2 tracking-tight">Customer Lookup</h1>
        <p className="text-gray-400 text-sm max-w-2xl leading-relaxed">Search 360-degree risk profile of individual accounts.</p>
      </motion.div>

      <motion.form 
        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
        onSubmit={handleSearch}
        className="relative w-full max-w-2xl"
      >
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-gray-500" />
        </div>
        <input 
          type="text" 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Enter Customer ID (e.g. 0000366f...)" 
          className="w-full bg-[#0a0a0a] border border-border rounded-lg py-2.5 pl-10 pr-24 text-sm text-white focus:outline-none focus:border-gray-500 transition-colors placeholder:text-gray-600"
        />
        <div className="absolute inset-y-0 right-1.5 flex items-center">
          <button type="submit" className="bg-white text-black font-semibold px-3 py-1.5 rounded text-[13px] hover:bg-gray-200 transition-colors">
            Lookup
          </button>
        </div>
      </motion.form>

      <AnimatePresence mode="wait">
        {searchedId && (
          <motion.div 
            key={searchedId}
            initial={{ opacity: 0, height: 0 }} 
            animate={{ opacity: 1, height: 'auto' }} 
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="w-full overflow-hidden"
          >
            {customerData ? (
              <div className="glass-panel p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="flex flex-col items-center justify-center lg:border-r border-border/50 lg:pr-6">
                  <div className="w-16 h-16 rounded-full bg-[#111] border border-[#222] flex items-center justify-center mb-4">
                    <User className="w-6 h-6 text-gray-400" />
                  </div>
                  <h3 className="font-mono text-[11px] text-gray-500 mb-6 truncate w-full text-center">{customerData.customer_unique_id}</h3>
                  
                  <div className="flex flex-col items-center gap-1">
                    <span className="text-gray-500 font-semibold uppercase tracking-widest text-[10px]">Overall Risk</span>
                    <span className={`text-5xl font-syne font-bold ${
                      customerData.risk_category === 'HIGH' ? 'text-danger' : 
                      customerData.risk_category === 'MEDIUM' ? 'text-warning' : 'text-success'
                    }`}>
                      {(customerData.risk_score * 100).toFixed(1)}
                    </span>
                    <RiskBadge riskCategory={customerData.risk_category} className="mt-2 text-[10px] px-2.5 py-1" />
                  </div>
                </div>

                <div className="flex flex-col justify-center gap-5 lg:border-r border-border/50 lg:pr-6">
                  <div className="flex flex-col gap-1.5">
                    <div className="flex justify-between items-end">
                      <span className="font-semibold text-gray-400 text-xs uppercase tracking-widest">Churn Prob.</span>
                      <span className="text-sm font-mono font-medium text-white">{(customerData.churn_probability * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-[#000] border border-[#222] rounded-full h-1.5 overflow-hidden">
                      <motion.div initial={{ width: 0 }} animate={{ width: `${customerData.churn_probability * 100}%` }} transition={{ delay: 0.2 }} className="h-full bg-danger"></motion.div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <div className="flex justify-between items-end">
                      <span className="font-semibold text-gray-400 text-xs uppercase tracking-widest">Review Integrity</span>
                      <span className="text-sm font-mono font-medium text-white">{((customerData.avg_integrity_score||0) * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-[#000] border border-[#222] rounded-full h-1.5 overflow-hidden">
                      <motion.div initial={{ width: 0 }} animate={{ width: `${(customerData.avg_integrity_score||0) * 100}%` }} transition={{ delay: 0.3 }} className="h-full bg-success"></motion.div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: 'Monetary', val: `$${(customerData.monetary || 0).toFixed(2)}`, icon: DollarSign, color: 'text-gray-300' },
                    { label: 'Recency', val: `${customerData.recency || 0}d`, icon: Calendar, color: 'text-gray-300' },
                    { label: 'Avg Review', val: `${(customerData.avg_review_score || 0).toFixed(1)} / 5`, icon: Star, color: 'text-warning' },
                    { label: 'Delay', val: `${(customerData.avg_delivery_delay || 0).toFixed(1)}d`, icon: Clock, color: 'text-gray-300' }
                  ].map(stat => (
                    <div key={stat.label} className="bg-[#000] rounded-lg p-3 border border-border flex flex-col justify-between">
                      <div className="flex justify-between items-start mb-2"><span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">{stat.label}</span><stat.icon className="w-3.5 h-3.5 text-gray-600" /></div>
                      <span className={`text-base font-medium ${stat.color}`}>{stat.val}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="glass-panel p-10 flex flex-col items-center justify-center text-center gap-3">
                <AlertCircle className="w-6 h-6 text-gray-500 mb-1" />
                <h3 className="font-syne font-semibold text-lg text-gray-300">Customer Not Found</h3>
                <p className="text-gray-500 text-xs max-w-md">The ID "{searchedId}" does not exist. Please check the spelling.</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="glass-panel flex flex-col overflow-hidden">
        <div className="p-4 border-b border-border bg-[#0a0a0a]">
          <h3 className="font-syne font-semibold text-[15px] text-gray-200">Top 10 High Risk Accounts</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead className="bg-[#111] border-b border-border">
              <tr className="text-gray-400">
                {[{id: 'id', label: 'Customer ID'}, {id: 'riskCategory', label: 'Category'}, {id: 'riskScore', label: 'Risk Score'}, {id: 'churnProb', label: 'Churn Prob'}, {id: 'integrityScore', label: 'Integrity'}, {id: 'monetary', label: 'Monetary'}].map(col => (
                  <th key={col.id} className={`py-3 px-4 font-semibold uppercase tracking-widest text-[11px] cursor-pointer hover:text-white transition-colors ${col.id !== 'id' && col.id !== 'riskCategory' ? 'text-right' : ''}`} onClick={() => handleSort(col.id)}>
                    {col.label} {sortField === col.id && <span className="text-gray-600 ml-1">{sortDir==='asc'?'↑':'↓'}</span>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {top10.map((row) => (
                <tr 
                  key={row.id} 
                  className="hover:bg-white/[0.02] transition-colors group cursor-pointer"
                  onClick={() => { setSearchTerm(row.id); setSearchedId(row.id); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                >
                  <td className="py-3 px-4 font-mono text-[11px] text-gray-400 truncate max-w-[120px]">{row.id}</td>
                  <td className="py-3 px-4"><RiskBadge riskCategory={row.riskCategory} className="text-[10px] px-2 py-0.5" /></td>
                  <td className="py-3 px-4 text-right font-mono text-danger font-medium text-xs">{(row.riskScore * 100).toFixed(1)}</td>
                  <td className="py-3 px-4 text-right font-mono text-gray-300 text-xs">{(row.churnProb * 100).toFixed(1)}%</td>
                  <td className="py-3 px-4 text-right font-mono text-gray-300 text-xs">{(row.integrityScore * 100).toFixed(1)}%</td>
                  <td className="py-3 px-4 text-right font-mono text-gray-300 text-xs">${row.monetary.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
};

export default CustomerLookup;
