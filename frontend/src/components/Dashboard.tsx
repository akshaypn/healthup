import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './Dashboard.css';

interface HealthData {
  weight: number;
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
  heartRate: number;
}

const Dashboard: React.FC = () => {
  const [todayData, setTodayData] = useState<HealthData | null>(null);
  const [weeklyData, setWeeklyData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/dashboard`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTodayData(data.today);
        setWeeklyData(data.weekly);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="dashboard-loading">Loading your health data...</div>;
  }

  return (
    <div className="dashboard">
      <h1>Your Health Dashboard</h1>
      
      <div className="dashboard-grid">
        {/* Today's Summary */}
        <div className="dashboard-card">
          <h2>Today's Summary</h2>
          <div className="summary-stats">
            <div className="stat">
              <span className="stat-label">Weight</span>
              <span className="stat-value">{todayData?.weight || '--'} kg</span>
            </div>
            <div className="stat">
              <span className="stat-label">Calories</span>
              <span className="stat-value">{todayData?.calories || 0} kcal</span>
            </div>
            <div className="stat">
              <span className="stat-label">Protein</span>
              <span className="stat-value">{todayData?.protein || 0}g</span>
            </div>
            <div className="stat">
              <span className="stat-label">Heart Rate</span>
              <span className="stat-value">{todayData?.heartRate || '--'} bpm</span>
            </div>
          </div>
        </div>

        {/* Weekly Weight Trend */}
        <div className="dashboard-card">
          <h2>Weekly Weight Trend</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={weeklyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="weight" stroke="#8884d8" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Quick Actions */}
        <div className="dashboard-card">
          <h2>Quick Actions</h2>
          <div className="quick-actions">
            <button className="action-btn" onClick={() => navigate('/weight')}>
              Log Weight
            </button>
            <button className="action-btn" onClick={() => navigate('/food')}>
              Log Meal
            </button>
            <button className="action-btn" onClick={() => navigate('/hr')}>
              Log Heart Rate
            </button>
            <button className="action-btn" onClick={() => navigate('/coach')}>
              Get Advice
            </button>
          </div>
        </div>

        {/* Recent Insights */}
        <div className="dashboard-card">
          <h2>Recent Insights</h2>
          <div className="insights-preview">
            <p>Your AI coach is analyzing your data...</p>
            <button className="view-insights-btn" onClick={() => navigate('/insights')}>
              View Full Insights
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 