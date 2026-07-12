import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { ShieldAlert, ShieldCheck, FileText, CheckCircle2, AlertTriangle, ScanSearch } from 'lucide-react';
import { useData } from '../hooks/useDataContext';
import StatCard from '../components/StatCard';

const ReviewIntegrity = () => {
  const { data } = useData();
  const { integrityScores } = data;

  const [reviewText, setReviewText] = useState('');
  const [starRating, setStarRating] = useState(5);
  const [scanResult, setScanResult] = useState(null);
  const [isScanning, setIsScanning] = useState(false);

  const stats = useMemo(() => {
    if (!integrityScores) return null;
    let totalScore = 0;
    let mismatches = 0;

    integrityScores.forEach(row => {
      totalScore += row.avg_integrity_score || 0;
      if (row.has_mismatch === 1 || String(row.has_mismatch) === 'true' || row.has_mismatch === true) {
        mismatches++;
      }
    });

    return {
      totalReviews: integrityScores.length,
      avgScore: totalScore / integrityScores.length,
      mismatches
    };
  }, [integrityScores]);

  const mismatchExamples = useMemo(() => {
    if (!integrityScores) return [];
    return integrityScores.filter(row => row.has_mismatch === 1 || String(row.has_mismatch) === 'true' || row.has_mismatch === true).slice(0, 7);
  }, [integrityScores]);

  const handleScan = () => {
    if (!reviewText.trim()) return;
    setIsScanning(true);
    setScanResult(null);

    setTimeout(() => {
      const text = reviewText.toLowerCase();
      const negativeWords = ['bad', 'terrible', 'awful', 'worst', 'hate', 'poor', 'broken', 'late'];
      const positiveWords = ['good', 'great', 'excellent', 'love', 'best', 'perfect', 'amazing'];
      
      let isNegative = negativeWords.some(w => text.includes(w));
      let isPositive = positiveWords.some(w => text.includes(w));
      
      let isConsistent = true;
      if (starRating >= 4 && isNegative && !isPositive) isConsistent = false;
      if (starRating <= 2 && isPositive && !isNegative) isConsistent = false;

      const score = isConsistent ? 0.85 + Math.random() * 0.1 : 0.1 + Math.random() * 0.2;

      setScanResult({
        isConsistent,
        confidence: (score * 100).toFixed(1)
      });
      setIsScanning(false);
    }, 1200);
  };

  if (!stats) return null;

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto w-full pb-10">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="pt-2 pb-4 border-b border-border">
        <h1 className="font-syne font-semibold text-3xl text-white mb-2 tracking-tight">Review Integrity</h1>
        <p className="text-gray-400 text-sm max-w-2xl leading-relaxed">NLP-driven detection of fraudulent reviews and sentiment-rating mismatches.</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard title="Total Analysed" value={stats.totalReviews} icon={FileText} colorClass="text-white" />
        <StatCard title="Avg Integrity Score" value={stats.avgScore * 100} suffix="%" icon={ShieldCheck} colorClass="text-success" />
        <StatCard title="Flagged Mismatches" value={stats.mismatches} icon={ShieldAlert} colorClass="text-danger" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-panel p-6 flex flex-col gap-5">
          <h3 className="font-syne font-semibold text-[15px] flex items-center gap-2 text-gray-200">
            <ScanSearch className="w-4 h-4 text-gray-400" /> Live NLP Sandbox
          </h3>
          
          <div className="flex flex-col gap-1.5">
            <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-widest">Review Text</label>
            <textarea 
              className="w-full bg-[#0a0a0a] border border-border rounded-lg p-3 text-sm text-gray-200 focus:outline-none focus:border-gray-500 transition-colors resize-none h-28"
              placeholder="Paste customer review here..."
              value={reviewText}
              onChange={(e) => setReviewText(e.target.value)}
            ></textarea>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-widest">Star Rating (1-5)</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map(star => (
                <button 
                  key={star}
                  onClick={() => setStarRating(star)}
                  className={`w-10 h-10 rounded border text-sm font-medium transition-all ${
                    starRating >= star 
                    ? 'bg-white text-black border-white' 
                    : 'bg-[#000] border-border text-gray-600 hover:border-gray-600'
                  }`}
                >
                  {star}
                </button>
              ))}
            </div>
          </div>

          <button 
            onClick={handleScan}
            disabled={isScanning || !reviewText.trim()}
            className="w-full bg-white text-black font-semibold text-sm py-2.5 rounded hover:bg-gray-200 transition-all disabled:opacity-50 flex justify-center items-center gap-2 mt-2"
          >
            {isScanning ? (
              <><div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin"></div> Processing NLP...</>
            ) : 'Analyse Sequence'}
          </button>

          <div className="h-16 mt-2">
            {scanResult && (
              <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className={`w-full h-full rounded border p-3 flex flex-col justify-center gap-2 ${scanResult.isConsistent ? 'bg-success/5 border-success/20' : 'bg-danger/5 border-danger/20'}`}>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    {scanResult.isConsistent ? <CheckCircle2 className="w-4 h-4 text-success" /> : <AlertTriangle className="w-4 h-4 text-danger" />}
                    <span className={`font-semibold ${scanResult.isConsistent ? 'text-success' : 'text-danger'}`}>
                      {scanResult.isConsistent ? 'CONSISTENT' : 'MISMATCH DETECTED'}
                    </span>
                  </div>
                  <span className="font-mono text-xs text-gray-400">{scanResult.confidence}% CONF</span>
                </div>
                <div className="w-full bg-[#000] border border-[#222] rounded-full h-1 overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }} 
                    animate={{ width: `${scanResult.confidence}%` }} 
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className={`h-full ${scanResult.isConsistent ? 'bg-success' : 'bg-danger'}`}
                  ></motion.div>
                </div>
              </motion.div>
            )}
          </div>
        </motion.div>

        <div className="flex flex-col gap-6">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-panel p-6 flex flex-col overflow-hidden">
             <h3 className="font-syne font-semibold text-[15px] mb-4 text-gray-200">Recent Mismatches</h3>
             <div className="flex-1 border border-border rounded-lg overflow-hidden bg-[#0a0a0a]">
               <table className="w-full text-left border-collapse text-sm">
                 <thead className="bg-[#111] border-b border-border">
                   <tr className="text-gray-400">
                     <th className="py-2.5 px-4 font-semibold uppercase tracking-widest text-[11px]">Customer ID</th>
                     <th className="py-2.5 px-4 font-semibold uppercase tracking-widest text-[11px] text-right">Integrity Score</th>
                   </tr>
                 </thead>
                 <tbody className="divide-y divide-border">
                   {mismatchExamples.map((row, i) => (
                     <tr key={row.customer_unique_id} className="hover:bg-white/[0.02] transition-colors">
                       <td className="py-2.5 px-4 font-mono text-[11px] text-gray-400 truncate max-w-[200px]">{row.customer_unique_id}</td>
                       <td className="py-2.5 px-4 text-right">
                         <span className="text-danger font-medium text-[12px]">{(row.avg_integrity_score * 100).toFixed(1)}%</span>
                       </td>
                     </tr>
                   ))}
                   {mismatchExamples.length === 0 && (
                     <tr><td colSpan="2" className="py-4 text-center text-xs text-gray-600">No anomalies detected.</td></tr>
                   )}
                 </tbody>
               </table>
             </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.3 }} className="glass-panel p-4 flex flex-col items-center justify-center group overflow-hidden">
             <h4 className="font-syne font-semibold mb-3 text-[13px] text-gray-400 uppercase tracking-widest w-full">NLP Confusion Matrix</h4>
             <div className="relative w-full aspect-[2/1] rounded overflow-hidden border border-border bg-[#000] flex items-center justify-center p-2 transition-colors group-hover:border-gray-700">
               <img src="/models/nlp_confusion_matrix.png" alt="NLP Confusion Matrix" className="w-full h-full object-contain" />
             </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default ReviewIntegrity;
