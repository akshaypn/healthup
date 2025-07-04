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
  const [generating, setGenerating] = useState<{ [key: string]: boolean }>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    try {
      setError(null);
      const periods = ['daily', 'weekly', 'monthly'];
      
      const insightsData: { [key: string]: Insight } = {};
      
      for (const period of periods) {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/insight/${period}`, {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
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
      setError('Failed to load insights. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const generateInsight = async (period: string) => {
    try {
      setGenerating(prev => ({ ...prev, [period]: true }));
      setError(null);
      
      const response = await fetch(`${import.meta.env.VITE_API_URL}/insight/${period}/generate`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.regenerated) {
          // Refresh insights after generation
          await fetchInsights();
        } else {
          // Insight already exists, just update the state
          setInsights(prev => ({
            ...prev,
            [period]: result.insight
          }));
        }
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate insight');
      }
    } catch (error) {
      console.error('Failed to generate insight:', error);
      setError(`Failed to generate ${period} insight: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setGenerating(prev => ({ ...prev, [period]: false }));
    }
  };

  const regenerateInsight = async (period: string) => {
    try {
      setGenerating(prev => ({ ...prev, [period]: true }));
      setError(null);
      
      const response = await fetch(`${import.meta.env.VITE_API_URL}/insight/${period}/regenerate`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        await response.json(); // Consume the response
        // Refresh insights after regeneration
        await fetchInsights();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to regenerate insight');
      }
    } catch (error) {
      console.error('Failed to regenerate insight:', error);
      setError(`Failed to regenerate ${period} insight: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setGenerating(prev => ({ ...prev, [period]: false }));
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
      
      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={() => setError(null)} className="dismiss-error">✕</button>
        </div>
      )}
      
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
                <div className="insight-actions">
                  <button 
                    className="regenerate-btn"
                    onClick={() => regenerateInsight(selectedPeriod)}
                    disabled={generating[selectedPeriod]}
                  >
                    {generating[selectedPeriod] ? '🔄 Regenerating...' : '🔄 Regenerate'}
                  </button>
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
                Your AI coach is ready to analyze your {selectedPeriod} data. 
                Click the button below to generate personalized insights!
              </p>
              <button 
                className="generate-insight-btn"
                onClick={() => generateInsight(selectedPeriod)}
                disabled={generating[selectedPeriod]}
              >
                {generating[selectedPeriod] ? '🤖 Generating...' : '🤖 Generate Insight'}
              </button>
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
            {['daily', 'weekly', 'monthly'].map(period => (
              <div key={period} className="status-item">
                <span className="status-label">{period.charAt(0).toUpperCase() + period.slice(1)} Insights</span>
                <div className="status-actions">
                  <span className={`status-indicator ${insights[period] ? 'available' : 'pending'}`}>
                    {insights[period] ? '✓ Available' : '⏳ Pending'}
                  </span>
                  {!insights[period] && (
                    <button 
                      className="generate-btn-small"
                      onClick={() => generateInsight(period)}
                      disabled={generating[period]}
                    >
                      {generating[period] ? '🔄' : '🤖'}
                    </button>
                  )}
                  {insights[period] && (
                    <button 
                      className="regenerate-btn-small"
                      onClick={() => regenerateInsight(period)}
                      disabled={generating[period]}
                    >
                      {generating[period] ? '🔄' : '🔄'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Insights; 