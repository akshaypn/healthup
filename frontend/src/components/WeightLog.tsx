import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './WeightLog.css';

interface WeightEntry {
  id: number;
  kg: number;
  logged_at: string;
}

const WeightLog: React.FC = () => {
  const [weight, setWeight] = useState('');
  const [weightHistory, setWeightHistory] = useState<WeightEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchWeightHistory();
  }, []);

  const fetchWeightHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/weight/history`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        // Ensure we have an array, even if the API returns unexpected data
        const logs = Array.isArray(data.logs) ? data.logs : [];
        setWeightHistory(logs);
      }
    } catch (error) {
      console.error('Failed to fetch weight history:', error);
      setWeightHistory([]); // Set empty array on error
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!weight || parseFloat(weight) <= 0) {
      setMessage('Please enter a valid weight');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/weight`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ kg: parseFloat(weight) })
      });

      if (response.ok) {
        setMessage('Weight logged successfully!');
        setWeight('');
        fetchWeightHistory();
      } else {
        setMessage('Failed to log weight. Please try again.');
      }
    } catch (error) {
      setMessage('Failed to log weight. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const chartData = (weightHistory || []).map(entry => ({
    date: new Date(entry.logged_at).toLocaleDateString(),
    weight: entry.kg
  })).reverse();

  return (
    <div className="weight-log">
      <h1>Weight Tracking</h1>
      
      <div className="weight-container">
        {/* Log Weight Form */}
        <div className="weight-form-card">
          <h2>Log Today's Weight</h2>
          <form onSubmit={handleSubmit} className="weight-form">
            <div className="form-group">
              <label htmlFor="weight">Weight (kg)</label>
              <input
                type="number"
                id="weight"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                step="0.1"
                min="0"
                placeholder="Enter your weight"
                required
              />
            </div>
            
            {message && (
              <div className={`message ${message.includes('successfully') ? 'success' : 'error'}`}>
                {message}
              </div>
            )}
            
            <button type="submit" disabled={loading} className="submit-btn">
              {loading ? 'Logging...' : 'Log Weight'}
            </button>
          </form>
        </div>

        {/* Weight Chart */}
        <div className="weight-chart-card">
          <h2>Weight Trend</h2>
          {(chartData || []).length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="weight" stroke="#8884d8" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">
              <p>No weight data yet. Log your first weight to see your trend!</p>
            </div>
          )}
        </div>

        {/* Recent Entries */}
        <div className="weight-history-card">
          <h2>Recent Entries</h2>
          <div className="weight-history">
            {(weightHistory || []).length > 0 ? (
              (weightHistory || []).slice(0, 10).map((entry) => (
                <div key={entry.id} className="weight-entry">
                  <span className="weight-value">{entry.kg} kg</span>
                  <span className="weight-date">
                    {new Date(entry.logged_at).toLocaleDateString()}
                  </span>
                </div>
              ))
            ) : (
              <p>No weight entries yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeightLog; 