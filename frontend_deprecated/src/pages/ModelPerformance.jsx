import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useData } from '../hooks/useDataContext';
import { Database, GitBranch, BrainCircuit, MessageSquare, LayoutDashboard, Zap } from 'lucide-react';

const ModelPerformance = () => {
  const { data } = useData();
  const { churnPredictions } = data;

  const metrics = useMemo(() => {
    if (!churnPredictions) return null;

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

    return { accuracy, precision, recall, f1, baselineAccuracy };
  }, [churnPredictions]);

  const techStack = [
    { name: 'XGBoost', desc: 'Primary classification model for churn' },
    { name: 'TF-IDF + NLP', desc: 'Text vectorization for reviews' },
    { name: 'React 18', desc: 'Frontend UI library' },
    { name: 'Tailwind CSS', desc: 'Utility-first styling framework' },
    { name: 'Framer Motion', desc: 'Animation library' },
    { name: 'PapaParse', desc: 'Client-side CSV parsing' }
  ];

  const pipeline = [
    { title: 'Extraction', icon: Database, desc: 'Raw dataset' },
    { title: 'Feature Eng', icon: GitBranch, desc: 'RFM derived' },
    { title: 'NLP Pipeline', icon: MessageSquare, desc: 'Text vectorization' },
    { title: 'Training', icon: BrainCircuit, desc: 'Model fitting' },
    { title: 'Scoring', icon: Zap, desc: 'Risk evaluation' },
    { title: 'Dashboard', icon: LayoutDashboard, desc: 'UI Integration' }
  ];

  const renderImageCard = (src, title, delay) => (
    <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay }} className="glass-panel p-4 flex flex-col group">
      <h3 className="font-syne font-semibold mb-3 text-[13px] text-gray-400 uppercase tracking-widest">{title}</h3>
      <div className="relative w-full aspect-video rounded overflow-hidden border border-border bg-[#000] flex items-center justify-center transition-colors group-hover:border-gray-700">
        <img src={src} alt={title} className="w-full h-full object-contain p-2" />
      </div>
    </motion.div>
  );

  if (!metrics) return null;

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto w-full pb-12">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="pt-2 pb-4 border-b border-border">
        <h1 className="font-syne font-semibold text-3xl text-white mb-2 tracking-tight">Model Performance</h1>
        <p className="text-gray-400 text-sm max-w-2xl leading-relaxed">Holistic view of machine learning pipeline and evaluation metrics.</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {renderImageCard('/models/confusion_matrix.png', 'Churn Confusion Matrix', 0.05)}
        {renderImageCard('/models/risk_distribution.png', 'Overall Risk Distribution', 0.1)}
        {renderImageCard('/models/feature_importance.png', 'Global Feature Importance', 0.15)}
        {renderImageCard('/models/nlp_confusion_matrix.png', 'NLP Review Mismatch Matrix', 0.2)}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-2">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="glass-panel overflow-hidden flex flex-col">
          <div className="p-5 border-b border-border bg-[#0a0a0a]">
            <h3 className="font-syne font-semibold text-[15px] text-gray-200">Evaluation Summary</h3>
          </div>
          <table className="w-full text-left border-collapse text-sm">
            <thead className="bg-[#111] border-b border-border">
              <tr className="text-gray-400">
                <th className="py-3 px-5 font-semibold uppercase tracking-widest text-[11px]">Metric</th>
                <th className="py-3 px-5 font-semibold uppercase tracking-widest text-[11px]">Baseline</th>
                <th className="py-3 px-5 font-semibold uppercase tracking-widest text-[11px] text-white">Model</th>
                <th className="py-3 px-5 font-semibold uppercase tracking-widest text-[11px] text-right">Uplift</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              <tr className="hover:bg-white/[0.02] transition-colors">
                <td className="py-3 px-5 font-medium text-gray-300">Accuracy</td>
                <td className="py-3 px-5 text-gray-500">{(metrics.baselineAccuracy * 100).toFixed(1)}%</td>
                <td className="py-3 px-5 text-white font-medium">{(metrics.accuracy * 100).toFixed(1)}%</td>
                <td className="py-3 px-5 text-right text-success text-xs font-mono">+ {((metrics.accuracy - metrics.baselineAccuracy) * 100).toFixed(1)}%</td>
              </tr>
              <tr className="hover:bg-white/[0.02] transition-colors">
                <td className="py-3 px-5 font-medium text-gray-300">Precision</td>
                <td className="py-3 px-5 text-gray-500">-</td>
                <td className="py-3 px-5 text-white font-medium">{(metrics.precision * 100).toFixed(1)}%</td>
                <td className="py-3 px-5 text-right text-gray-600 text-xs">-</td>
              </tr>
              <tr className="hover:bg-white/[0.02] transition-colors">
                <td className="py-3 px-5 font-medium text-gray-300">Recall</td>
                <td className="py-3 px-5 text-gray-500">-</td>
                <td className="py-3 px-5 text-white font-medium">{(metrics.recall * 100).toFixed(1)}%</td>
                <td className="py-3 px-5 text-right text-gray-600 text-xs">-</td>
              </tr>
              <tr className="hover:bg-white/[0.02] transition-colors">
                <td className="py-3 px-5 font-medium text-gray-300">F1 Score</td>
                <td className="py-3 px-5 text-gray-500">0.0%</td>
                <td className="py-3 px-5 text-white font-medium">{(metrics.f1 * 100).toFixed(1)}%</td>
                <td className="py-3 px-5 text-right text-success text-xs font-mono">+ {(metrics.f1 * 100).toFixed(1)}%</td>
              </tr>
            </tbody>
          </table>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-panel p-5 flex flex-col">
          <h3 className="font-syne font-semibold text-[15px] mb-5 text-gray-200">Technology Stack</h3>
          <div className="grid grid-cols-2 gap-3 flex-1">
            {techStack.map((tech) => (
              <div key={tech.name} className="p-3 rounded-lg border border-border bg-[#000] flex flex-col justify-center transition-colors hover:border-gray-700">
                <h4 className="font-semibold text-sm text-gray-200">{tech.name}</h4>
                <p className="text-[11px] text-gray-500 mt-0.5">{tech.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }} className="glass-panel p-6 mt-2 relative overflow-hidden">
        <h3 className="font-syne font-semibold text-[15px] text-gray-200 mb-8">Pipeline Architecture</h3>
        
        <div className="relative">
          <div className="absolute top-4 left-0 w-full h-[1px] bg-border z-0 hidden md:block">
            <motion.div initial={{ width: 0 }} animate={{ width: '100%' }} transition={{ duration: 1.5, delay: 0.5 }} className="h-full bg-gray-600"></motion.div>
          </div>

          <div className="grid grid-cols-2 gap-y-8 md:grid-cols-6 md:gap-y-0 relative z-10">
            {pipeline.map((step, i) => (
              <motion.div key={step.title} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 + (i * 0.1) }} className="flex flex-col items-center text-center">
                <div className="w-8 h-8 rounded-full bg-[#0a0a0a] border border-[#333] flex items-center justify-center mb-3">
                  <step.icon className="w-3.5 h-3.5 text-gray-400" />
                </div>
                <h4 className="font-semibold text-[12px] text-gray-300">{step.title}</h4>
                <p className="text-[10px] text-gray-500 mt-0.5 uppercase tracking-wider">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default ModelPerformance;
