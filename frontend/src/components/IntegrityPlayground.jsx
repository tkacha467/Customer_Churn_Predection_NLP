import { useState, useEffect } from 'react';

import { apiFetch } from '../lib/api';
const DINING_PRESETS = [
  {
    label: '☕ Genuine 5-Star Cafe Visit',
    rating: 5,
    text: 'The specialty coffee was pulled to perfection and the staff made us feel right at home! Truly an outstanding neighborhood roastery.'
  },
  {
    label: '🥐 Sarcastic 5-Star Dining Complaint',
    rating: 5,
    text: 'Waited 50 minutes for cold coffee and stale croissants. Truly teaching me patience, wasting my money, five stars!'
  },
  {
    label: '🍽️ Balanced 3-Star Restaurant Visit',
    rating: 3,
    text: 'The food was acceptable and the atmosphere was standard. A decent visit, though nothing particularly memorable.'
  },
  {
    label: '❌ Severe 1-Star Operational Letdown',
    rating: 1,
    text: 'Extremely rude floor staff, dirty cutlery, and cold food. Completely unacceptable standards.'
  }
];

export default function IntegrityPlayground() {
  const [reviewText, setReviewText] = useState('');
  const [rating, setRating] = useState(5);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    apiFetch('/api/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error("Failed to load stats:", err));
  }, []);

  const handleApplyPreset = (preset) => {
    setRating(preset.rating);
    setReviewText(preset.text);
  };

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    if (!reviewText.trim()) return;

    setLoading(true);
    try {
      const response = await apiFetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review: reviewText, rating })
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Analysis failed:", error);
      alert("Failed to connect to the AI API. Ensure the Python server is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="grid-2">
        {/* Interactive Playground */}
        <div className="glass-panel">
          <div className="section-badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa' }}>
            NLP Sequence Classification & Fusion
          </div>
          <h2 style={{ marginBottom: '0.5rem', color: 'var(--primary)', fontSize: '1.6rem' }}>
            Review Integrity & Sarcasm Lab
          </h2>
          <p style={{ marginBottom: '1.25rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Evaluates reviews with our fine-tuned DistilBERT / RoBERTa sentiment classifier fused with an irony/sarcasm detection pipeline.
          </p>

          {/* Quick Presets */}
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.5rem' }}>
              ⚡ 1-Click Hospitality Test Scenarios:
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {DINING_PRESETS.map((p, idx) => (
                <button
                  type="button"
                  key={idx}
                  className="btn-secondary"
                  onClick={() => handleApplyPreset(p)}
                  style={{ fontSize: '0.75rem', padding: '0.4rem 0.75rem' }}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
          
          <form onSubmit={handleAnalyze}>
            <div className="input-group">
              <label>Star Rating Given</label>
              <div className="star-rating">
                {[1, 2, 3, 4, 5].map(star => (
                  <button
                    type="button"
                    key={star}
                    className={`star-btn ${rating >= star ? 'active' : ''}`}
                    onClick={() => setRating(star)}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>

            <div className="input-group">
              <label>Review Text to Evaluate</label>
              <textarea 
                rows="4"
                placeholder="Paste any dining review or complaint..."
                value={reviewText}
                onChange={(e) => setReviewText(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="btn-primary" disabled={loading || !reviewText.trim()}>
              {loading ? 'Evaluating with Fusion Engine...' : '🔍 Analyze Review Integrity'}
            </button>
          </form>
        </div>

        {/* Results Panel */}
        <div className="glass-panel">
          {!result ? (
            <div className="result-card" style={{ opacity: 0.5 }}>
              <div className="status-icon">🤖</div>
              <h3>Model Pipeline Ready</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                Select a test scenario or enter review text to inspect sentiment scores, sarcasm probabilities, and rating alignment.
              </p>
            </div>
          ) : (
            <div className="result-card">
              <div className={`status-icon ${result.integrity === 'Suspicious' ? 'status-fake' : 'status-real'}`}>
                {result.integrity === 'Suspicious' ? '⚠️' : '✅'}
              </div>
              <h2 style={{ color: result.integrity === 'Suspicious' ? 'var(--danger)' : 'var(--success)', fontSize: '1.4rem' }}>
                {result.integrity === 'Suspicious' ? 'Integrity Mismatch Detected!' : 'Review Validated As Genuine'}
              </h2>
              
              {result.sarcasm && (
                <div style={{ backgroundColor: '#f59e0b', color: '#000', padding: '0.25rem 0.85rem', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 'bold', marginTop: '-0.5rem' }}>
                  ⚡ SARCASM / IRONY DETECTED
                </div>
              )}
              
              <ul style={{ color: 'var(--text-muted)', textAlign: 'left', marginTop: '1rem', width: '100%', fontSize: '0.9rem' }}>
                {result.reason.map((res, i) => (
                  <li key={i}>{res}</li>
                ))}
              </ul>
              
              <div className="grid-2" style={{ width: '100%', marginTop: '1.5rem', gap: '1rem' }}>
                <div className="glass-panel" style={{ padding: '1rem', border: '1px solid var(--primary)', textAlign: 'center' }}>
                  <div className="metric-label">Predicted Sentiment</div>
                  <div className="metric" style={{ color: result.sentiment === 'Positive' ? 'var(--success)' : result.sentiment === 'Negative' ? 'var(--danger)' : 'var(--text-muted)' }}>
                    {result.sentiment}
                  </div>
                </div>
                <div className="glass-panel" style={{ padding: '1rem', textAlign: 'center' }}>
                  <div className="metric-label">AI Confidence</div>
                  <div className="metric">
                    {(result.confidence * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Dataset Overview */}
      <div className="glass-panel" style={{ marginTop: '2rem' }}>
        <h3 style={{ marginBottom: '1rem', textAlign: 'center' }}>Underlying Model Architecture & Training Foundations</h3>
        <div className="grid-2">
          <div style={{ textAlign: 'center' }}>
            <h4 style={{ color: 'var(--primary)', marginBottom: '0.75rem' }}>Amazon Benchmark Training Corpus</h4>
            <div className="data-stats">
              <div className="stat-box">
                <div className="metric">{stats ? stats.amazon.total_reviews : '3.6M'}</div>
                <div className="metric-label">Training Rows</div>
              </div>
              <div className="stat-box">
                <div className="metric">{stats ? stats.amazon.test_reviews : '400k'}</div>
                <div className="metric-label">Testing Rows</div>
              </div>
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <h4 style={{ color: 'var(--secondary)', marginBottom: '0.75rem' }}>Validation Inference Scans</h4>
            <div className="data-stats">
              <div className="stat-box">
                <div className="metric">{stats ? stats.flipkart.total_reviews : '363,261'}</div>
                <div className="metric-label">Reviews Scanned</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
