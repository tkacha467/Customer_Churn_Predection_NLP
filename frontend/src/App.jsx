import { useState, useEffect } from 'react';
import './index.css';

function App() {
  const [reviewText, setReviewText] = useState('');
  const [rating, setRating] = useState(5);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    // Fetch stats on load
    fetch('http://127.0.0.1:8000/api/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error("Failed to load stats:", err));
  }, []);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!reviewText.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/predict', {
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
    <div className="app-container">
      <header>
        <h1>Review Integrity AI</h1>
        <p>A pure NLP sequence classification model trained on 3.6 Million Amazon reviews to detect fake, sarcastic, or mismatched e-commerce reviews in real-time.</p>
      </header>

      <div className="grid-2">
        {/* Interactive Playground */}
        <div className="glass-panel">
          <h2 style={{ marginBottom: '1.5rem', color: 'var(--primary)' }}>Live Inference Playground</h2>
          <p style={{ marginBottom: '1.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Paste a real review from Flipkart below. Set the Star Rating they gave, and click Analyze to see if the AI flags it as a fake/mismatched review.
          </p>
          
          <form onSubmit={handleAnalyze}>
            <div className="input-group">
              <label>Star Rating</label>
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
              <label>Review Text</label>
              <textarea 
                rows="5"
                placeholder="Paste the review text here..."
                value={reviewText}
                onChange={(e) => setReviewText(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="btn-primary" disabled={loading || !reviewText.trim()}>
              {loading ? 'Analyzing with Fusion Engine...' : 'Analyze Review Integrity'}
            </button>
          </form>
        </div>

        {/* Results Panel */}
        <div className="glass-panel">
          {!result ? (
            <div className="result-card" style={{ opacity: 0.5 }}>
              <div className="status-icon">🤖</div>
              <h3>Waiting for input...</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                The Fusion Engine is loaded and ready. Enter a review to analyze its integrity.
              </p>
            </div>
          ) : (
            <div className="result-card">
              <div className={`status-icon ${result.integrity === 'Suspicious' ? 'status-fake' : 'status-real'}`}>
                {result.integrity === 'Suspicious' ? '⚠️' : '✅'}
              </div>
              <h2 style={{ color: result.integrity === 'Suspicious' ? 'var(--danger)' : 'var(--success)' }}>
                {result.integrity === 'Suspicious' ? 'Integrity Mismatch Detected!' : 'Review Looks Genuine'}
              </h2>
              
              {result.sarcasm && (
                <div style={{ backgroundColor: '#f59e0b', color: '#000', padding: '0.2rem 0.8rem', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 'bold', marginTop: '-0.5rem' }}>
                  SARCASM DETECTED
                </div>
              )}
              
              <ul style={{ color: 'var(--text-muted)', textAlign: 'left', marginTop: '1rem' }}>
                {result.reason.map((res, i) => (
                  <li key={i}>{res}</li>
                ))}
              </ul>
              
              <div className="grid-2" style={{ width: '100%', marginTop: '1.5rem' }}>
                <div className="glass-panel" style={{ padding: '1rem', border: '1px solid var(--primary)' }}>
                  <div className="metric-label">Predicted Sentiment</div>
                  <div className="metric" style={{ color: result.sentiment === 'Positive' ? 'var(--success)' : result.sentiment === 'Negative' ? 'var(--danger)' : 'var(--text-muted)' }}>
                    {result.sentiment}
                  </div>
                </div>
                <div className="glass-panel" style={{ padding: '1rem' }}>
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
      <div className="glass-panel">
        <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Dataset Architecture</h2>
        <div className="grid-2">
          <div style={{ textAlign: 'center' }}>
            <h3 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>Amazon Training Data</h3>
            <div className="data-stats">
              <div className="stat-box">
                <div className="metric">{stats ? stats.amazon.total_reviews : '...'}</div>
                <div className="metric-label">Training Rows</div>
              </div>
              <div className="stat-box">
                <div className="metric">{stats ? stats.amazon.test_reviews : '...'}</div>
                <div className="metric-label">Testing Rows</div>
              </div>
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <h3 style={{ color: 'var(--secondary)', marginBottom: '1rem' }}>Flipkart Inference Data</h3>
            <div className="data-stats">
              <div className="stat-box">
                <div className="metric">{stats ? stats.flipkart.total_reviews : '...'}</div>
                <div className="metric-label">Rows Scanned</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
