import React, { useState, useEffect } from 'react';
import './Insights.css';

interface Insight {
  period: string;
  period_start: string;
  insight_md: string;
  created_at: string;
}

const Insights: React.FC = () => {
  const [insights, setInsights] = useState<{ [key: string]: Insight }>({});
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('daily');

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    try {
      const token = localStorage.getItem('token');
      const periods = ['daily', 'weekly', 'monthly'];
      
      const insightsData: { [key: string]: Insight } = {};
      
      for (const period of periods) {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/insight/${period}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          insightsData[period] = data;
        }
      }
      
      setInsights(insightsData);
    } catch (error) {
      console.error('Failed to fetch insights:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const renderMarkdown = (markdown: string) => {
    if (!markdown) return <p>No insights available yet. Keep logging your data to get personalized insights!</p>;
    
    // Simple markdown rendering
    return markdown.split('\n').map((line, index) => {
      if (line.startsWith('## ')) {
        return <h3 key={index}>{line.replace('## ', '')}</h3>;
      } else if (line.startsWith('# ')) {
        return <h2 key={index}>{line.replace('# ', '')}</h2>;
      } else if (line.startsWith('- ')) {
        return <li key={index}>{line.replace('- ', '')}</li>;
      } else if (line.trim() === '') {
        return <br key={index} />;
      } else {
        return <p key={index}>{line}</p>;
      }
    });
  };

  if (loading) {
    return <div className="insights-loading">Loading your insights...</div>;
  }

  return (
    <div className="insights">
      <h1>AI Health Insights</h1>
      
      <div className="insights-container">
        {/* Period Selector */}
        <div className="period-selector">
          <button 
            className={`period-btn ${selectedPeriod === 'daily' ? 'active' : ''}`}
            onClick={() => setSelectedPeriod('daily')}
          >
            Daily
          </button>
          <button 
            className={`period-btn ${selectedPeriod === 'weekly' ? 'active' : ''}`}
            onClick={() => setSelectedPeriod('weekly')}
          >
            Weekly
          </button>
          <button 
            className={`period-btn ${selectedPeriod === 'monthly' ? 'active' : ''}`}
            onClick={() => setSelectedPeriod('monthly')}
          >
            Monthly
          </button>
        </div>

        {/* Insight Content */}
        <div className="insight-content">
          {insights[selectedPeriod] ? (
            <div className="insight-card">
              <div className="insight-header">
                <h2>{selectedPeriod.charAt(0).toUpperCase() + selectedPeriod.slice(1)} Insights</h2>
                <div className="insight-meta">
                  <span>Period: {formatDate(insights[selectedPeriod].period_start)}</span>
                  <span>Generated: {formatDate(insights[selectedPeriod].created_at)}</span>
                </div>
              </div>
              
              <div className="insight-body">
                {renderMarkdown(insights[selectedPeriod].insight_md)}
              </div>
            </div>
          ) : (
            <div className="no-insight">
              <h2>No {selectedPeriod} insights yet</h2>
              <p>
                Your AI coach is analyzing your {selectedPeriod} data. 
                Keep logging your health metrics to receive personalized insights!
              </p>
              <div className="insight-tips">
                <h3>What to expect:</h3>
                <ul>
                  <li>Personalized health recommendations</li>
                  <li>Trend analysis and patterns</li>
                  <li>Actionable next steps</li>
                  <li>Motivational guidance</li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Insight Status */}
        <div className="insight-status">
          <h3>Insight Generation Status</h3>
          <div className="status-grid">
            <div className="status-item">
              <span className="status-label">Daily Insights</span>
              <span className={`status-indicator ${insights.daily ? 'available' : 'pending'}`}>
                {insights.daily ? '✓ Available' : '⏳ Pending'}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Weekly Insights</span>
              <span className={`status-indicator ${insights.weekly ? 'available' : 'pending'}`}>
                {insights.weekly ? '✓ Available' : '⏳ Pending'}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Monthly Insights</span>
              <span className={`status-indicator ${insights.monthly ? 'available' : 'pending'}`}>
                {insights.monthly ? '✓ Available' : '⏳ Pending'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Insights; 