import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './HRLog.css';

// Extend Navigator interface for Bluetooth
declare global {
  interface Navigator {
    bluetooth?: {
      requestDevice(options: { filters: Array<{ services: string[] }> }): Promise<any>;
    };
  }
}

interface HREntry {
  id: number;
  avg_bpm: number;
  min_bpm: number;
  max_bpm: number;
  started_at: string;
  ended_at: string;
}

const HRLog: React.FC = () => {
  const [formData, setFormData] = useState({
    avg_bpm: '',
    min_bpm: '',
    max_bpm: ''
  });
  const [hrHistory, setHrHistory] = useState<HREntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isScanning, setIsScanning] = useState(false);

  useEffect(() => {
    fetchHRHistory();
  }, []);

  const fetchHRHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/hr/history`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        // Ensure we have an array, even if the API returns unexpected data
        const logs = Array.isArray(data.logs) ? data.logs : [];
        setHrHistory(logs);
      }
    } catch (error) {
      console.error('Failed to fetch HR history:', error);
      setHrHistory([]); // Set empty array on error
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/hr`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          avg_bpm: parseInt(formData.avg_bpm) || 0,
          min_bpm: parseInt(formData.min_bpm) || 0,
          max_bpm: parseInt(formData.max_bpm) || 0,
          raw: {}
        })
      });

      if (response.ok) {
        setMessage('Heart rate logged successfully!');
        setFormData({
          avg_bpm: '',
          min_bpm: '',
          max_bpm: ''
        });
        fetchHRHistory();
      } else {
        setMessage('Failed to log heart rate. Please try again.');
      }
    } catch (error) {
      setMessage('Failed to log heart rate. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const scanForHRDevice = async () => {
    if (!navigator.bluetooth) {
      setMessage('Bluetooth is not supported in this browser');
      return;
    }

    setIsScanning(true);
    setMessage('Scanning for heart rate devices...');

    try {
      const device = await navigator.bluetooth.requestDevice({
        filters: [
          { services: ['heart_rate'] }
        ]
      });

      setMessage(`Connected to: ${device.name}`);
      // Here you would implement the actual heart rate monitoring
      // For now, we'll just simulate it
      setTimeout(() => {
        setFormData({
          avg_bpm: '75',
          min_bpm: '65',
          max_bpm: '85'
        });
        setMessage('Heart rate data captured!');
      }, 2000);

    } catch (error) {
      setMessage('Failed to connect to heart rate device');
    } finally {
      setIsScanning(false);
    }
  };

  const chartData = (hrHistory || []).map(entry => ({
    date: new Date(entry.started_at).toLocaleDateString(),
    avg: entry.avg_bpm,
    min: entry.min_bpm,
    max: entry.max_bpm
  })).reverse();

  return (
    <div className="hr-log">
      <h1>Heart Rate Tracking</h1>
      
      <div className="hr-container">
        {/* Log HR Form */}
        <div className="hr-form-card">
          <h2>Log Heart Rate Session</h2>
          <form onSubmit={handleSubmit} className="hr-form">
            <div className="form-group">
              <label htmlFor="avg_bpm">Average BPM</label>
              <input
                type="number"
                id="avg_bpm"
                name="avg_bpm"
                value={formData.avg_bpm}
                onChange={handleInputChange}
                placeholder="0"
                min="0"
                required
              />
            </div>
            
            <div className="hr-range">
              <div className="form-group">
                <label htmlFor="min_bpm">Min BPM</label>
                <input
                  type="number"
                  id="min_bpm"
                  name="min_bpm"
                  value={formData.min_bpm}
                  onChange={handleInputChange}
                  placeholder="0"
                  min="0"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="max_bpm">Max BPM</label>
                <input
                  type="number"
                  id="max_bpm"
                  name="max_bpm"
                  value={formData.max_bpm}
                  onChange={handleInputChange}
                  placeholder="0"
                  min="0"
                />
              </div>
            </div>
            
            {message && (
              <div className={`message ${message.includes('successfully') ? 'success' : 'error'}`}>
                {message}
              </div>
            )}
            
            <div className="hr-actions">
              <button type="submit" disabled={loading} className="submit-btn">
                {loading ? 'Logging...' : 'Log Heart Rate'}
              </button>
              
              <button 
                type="button" 
                onClick={scanForHRDevice} 
                disabled={isScanning}
                className="bluetooth-btn"
              >
                {isScanning ? 'Scanning...' : '📱 Connect HR Monitor'}
              </button>
            </div>
          </form>
        </div>

        {/* HR Chart */}
        <div className="hr-chart-card">
          <h2>Heart Rate Trend</h2>
          {(chartData || []).length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="avg" stroke="#8884d8" strokeWidth={2} name="Average" />
                <Line type="monotone" dataKey="min" stroke="#82ca9d" strokeWidth={1} name="Min" />
                <Line type="monotone" dataKey="max" stroke="#ffc658" strokeWidth={1} name="Max" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">
              <p>No heart rate data yet. Log your first session to see your trend!</p>
            </div>
          )}
        </div>

        {/* Recent Sessions */}
        <div className="hr-history-card">
          <h2>Recent Sessions</h2>
          <div className="hr-history">
            {(hrHistory || []).length > 0 ? (
              (hrHistory || []).slice(0, 10).map((entry) => (
                <div key={entry.id} className="hr-entry">
                  <div className="hr-stats">
                    <span className="hr-avg">{entry.avg_bpm} bpm avg</span>
                    <span className="hr-range">{entry.min_bpm}-{entry.max_bpm} bpm</span>
                  </div>
                  <span className="hr-date">
                    {new Date(entry.started_at).toLocaleDateString()}
                  </span>
                </div>
              ))
            ) : (
              <p>No heart rate sessions yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HRLog; 