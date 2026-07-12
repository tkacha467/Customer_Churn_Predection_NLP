import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell } from 'recharts';
import { useData } from '../hooks/useDataContext';
import StatCard from '../components/StatCard';
import { Target, CheckCircle2, XCircle, Activity } from 'lucide-react';

const ChurnAnalysis = () => {
  const { data } = useData();
  const { churnPredictions, rfmFeatures } = data;

  const metrics = useMemo(() => {
    if (!churnPredictions || !rfmFeatures) return null;

    let tp = 0, tn = 0, fp = 0, fn = 0;
    let actualChurn = 0, actualRetained = 0;

    churnPredictions.forEach(row => {
      const actual = row.churn_actual;
      const pred = row.churn_predicted;
      if (actual === 1) actualChurn++; else actualRetained++;
      if (actual === 1 && pred === 1) tp++;
      if (actual === 0 && pred === 0) tn++;
      if (actual === 0 && pred === 1) fp++;
      if (actual === 1 && pred === 0) fn++;
    });

    const total = tp + tn + fp + fn;
    const accuracy = (tp + tn) / total;
    const precision = tp / (tp + fp) || 0;
    const recall = tp / (tp + fn) || 0;
    const f1 = 2 * (precision * recall) / (precision + recall) || 0;
    const baselineAccuracy = Math.max(actualChurn, actualRetained) / total;

    let sumRecencyC = 0, sumFreqC = 0, sumMonetaryC = 0;
    let sumRecencyR = 0, sumFreqR = 0, sumMonetaryR = 0;

    rfmFeatures.forEach(row => {
      if (row.churn === 1) {
        sumRecencyC += row.recency || 0;
        sumFreqC += row.frequency || 0;
        sumMonetaryC += row.monetary || 0;
      } else {
        sumRecencyR += row.recency || 0;
        sumFreqR += row.frequency || 0;
        sumMonetaryR += row.monetary || 0;
      }
    });

    const featureImp = [
      { name: 'Recency Diff', value: Math.abs((sumRecencyC / actualChurn) - (sumRecencyR / actualRetained)) },
      { name: 'Freq Diff', value: Math.abs((sumFreqC / actualChurn) - (sumFreqR / actualRetained)) * 100 },
      { name: 'Monetary Diff', value: Math.abs((sumMonetaryC / actualChurn) - (sumMonetaryR / actualRetained)) }
    ].sort((a, b) => b.value - a.value);

    return { accuracy, precision, recall, f1, baselineAccuracy, actualChurn, actualRetained, featureImp };
  }, [churnPredictions, rfmFeatures]);

  if (!metrics) return null;

  const churnVsRetainedData = [
    { name: 'Retained', count: metrics.actualRetained, color: '#32d74b' },
    { name: 'Churned', count: metrics.actualChurn, color: '#ff453a' }
  ];

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#000] border border-[#222] p-2 rounded shadow-xl">
          <p className="text-[13px] text-gray-300 font-medium">{payload[0].payload.name}</p>
          <p className="text-[14px] font-bold text-white mt-1">{payload[0].value.toLocaleString()}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto w-full pb-10">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="pt-2 pb-4 border-b border-border">
        <h1 className="font-syne font-semibold text-3xl text-white mb-2 tracking-tight">Churn Analysis</h1>
        <p className="text-gray-400 text-sm max-w-2xl leading-relaxed">Evaluation of prediction accuracy against historical customer behavior.</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Model Accuracy" value={metrics.accuracy * 100} suffix="%" icon={Target} colorClass="text-accent" />
        <StatCard title="Precision" value={metrics.precision * 100} suffix="%" icon={CheckCircle2} colorClass="text-white" />
        <StatCard title="Recall" value={metrics.recall * 100} suffix="%" icon={XCircle} colorClass="text-gray-400" />
        <StatCard title="F1 Score" value={metrics.f1 * 100} suffix="%" icon={Activity} colorClass="text-primary" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-panel p-6 min-h-[360px] flex flex-col">
          <h3 className="font-syne font-semibold text-[15px] mb-6 text-gray-200">Actual Churn vs Retained</h3>
          <div className="flex-1 w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={churnVsRetainedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                <XAxis dataKey="name" stroke="#666" tick={{fontSize: 12}} axisLine={false} tickLine={false} />
                <YAxis stroke="#666" tick={{fontSize: 12}} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: '#ffffff05' }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} barSize={40} animationDuration={1000}>
                  {churnVsRetainedData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="glass-panel p-6 min-h-[360px] flex flex-col">
          <h3 className="font-syne font-semibold text-[15px] mb-6 text-gray-200">Feature Importance (Live Proxy)</h3>
          <div className="flex-1 w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={metrics.featureImp} margin={{ top: 0, right: 20, left: 30, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#222" horizontal={false} />
                <XAxis type="number" stroke="#666" hide />
                <YAxis dataKey="name" type="category" stroke="#999" tick={{fontSize: 12}} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: '#ffffff05' }} />
                <Bar dataKey="value" fill="#47c4ff" radius={[0, 4, 4, 0]} barSize={20} animationDuration={1000} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-panel p-6 overflow-hidden flex flex-col">
          <h3 className="font-syne font-semibold text-[15px] mb-4 text-gray-200">Baseline vs Model Performance</h3>
          <div className="flex-1 border border-border rounded-lg overflow-hidden bg-[#0a0a0a]">
            <table className="w-full text-left border-collapse text-sm">
              <thead className="bg-[#111] border-b border-border">
                <tr className="text-gray-400">
                  <th className="py-3 px-4 font-semibold uppercase tracking-widest text-[11px]">Metric</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-widest text-[11px]">Baseline (Majority)</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-widest text-[11px] text-white">Model (XGBoost)</th>
                  <th className="py-3 px-4 font-semibold uppercase tracking-widest text-[11px] text-right">Uplift</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                <tr className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 px-4 font-medium text-gray-300">Accuracy</td>
                  <td className="py-3 px-4 text-gray-500">{(metrics.baselineAccuracy * 100).toFixed(1)}%</td>
                  <td className="py-3 px-4 text-white font-medium">{(metrics.accuracy * 100).toFixed(1)}%</td>
                  <td className="py-3 px-4 text-right text-success text-xs font-mono">+ {((metrics.accuracy - metrics.baselineAccuracy) * 100).toFixed(1)}%</td>
                </tr>
                <tr className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 px-4 font-medium text-gray-300">F1 Score</td>
                  <td className="py-3 px-4 text-gray-500">0.0%</td>
                  <td className="py-3 px-4 text-white font-medium">{(metrics.f1 * 100).toFixed(1)}%</td>
                  <td className="py-3 px-4 text-right text-success text-xs font-mono">+ {(metrics.f1 * 100).toFixed(1)}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </motion.div>

        <div className="grid grid-cols-2 gap-4">
          <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.25 }} className="glass-panel p-4 flex flex-col group">
             <h4 className="font-syne font-semibold mb-3 text-[13px] text-gray-400 uppercase tracking-widest">Confusion Matrix</h4>
             <div className="relative w-full flex-1 aspect-square rounded overflow-hidden border border-border bg-[#000] flex items-center justify-center p-2 transition-colors group-hover:border-gray-700">
               <img src="/models/confusion_matrix.png" alt="Confusion Matrix" className="w-full h-full object-contain" />
             </div>
          </motion.div>
          <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.3 }} className="glass-panel p-4 flex flex-col group">
             <h4 className="font-syne font-semibold mb-3 text-[13px] text-gray-400 uppercase tracking-widest">Feature Importance</h4>
             <div className="relative w-full flex-1 aspect-square rounded overflow-hidden border border-border bg-[#000] flex items-center justify-center p-2 transition-colors group-hover:border-gray-700">
               <img src="/models/feature_importance.png" alt="Feature Importance" className="w-full h-full object-contain" />
             </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default ChurnAnalysis;
