import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './Dashboard.css';

interface WeightEntry {
  id: number;
  kg: number;
  logged_at: string;
}

interface FoodEntry {
  id: number;
  name: string;
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
  logged_at: string;
}

interface HREntry {
  id: number;
  avg_bpm: number;
  min_bpm: number;
  max_bpm: number;
  started_at: string;
}

interface DashboardData {
  recent_weight: WeightEntry[];
  recent_food: FoodEntry[];
  recent_hr: HREntry[];
  stats: {
    total_weight_entries: number;
    total_food_entries: number;
    total_hr_sessions: number;
  };
}

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
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
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getLatestWeight = () => {
    if (!dashboardData?.recent_weight || dashboardData.recent_weight.length === 0) {
      return null;
    }
    return dashboardData.recent_weight[0]; // Most recent weight
  };

  const getTodayCalories = () => {
    if (!dashboardData?.recent_food) return 0;
    const today = new Date().toDateString();
    return dashboardData.recent_food
      .filter(food => new Date(food.logged_at).toDateString() === today)
      .reduce((sum, food) => sum + food.calories, 0);
  };

  const getTodayProtein = () => {
    if (!dashboardData?.recent_food) return 0;
    const today = new Date().toDateString();
    return dashboardData.recent_food
      .filter(food => new Date(food.logged_at).toDateString() === today)
      .reduce((sum, food) => sum + food.protein, 0);
  };

  const getLatestHeartRate = () => {
    if (!dashboardData?.recent_hr || dashboardData.recent_hr.length === 0) {
      return null;
    }
    return dashboardData.recent_hr[0]; // Most recent HR session
  };

  const getWeightChartData = () => {
    if (!dashboardData?.recent_weight) return [];
    return dashboardData.recent_weight
      .slice(0, 7) // Last 7 entries
      .reverse() // Show oldest to newest
      .map(entry => ({
        date: new Date(entry.logged_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        weight: entry.kg
      }));
  };

  if (loading) {
    return <div className="dashboard-loading">Loading your health data...</div>;
  }

  const latestWeight = getLatestWeight();
  const todayCalories = getTodayCalories();
  const todayProtein = getTodayProtein();
  const latestHR = getLatestHeartRate();
  const weightChartData = getWeightChartData();

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
              <span className="stat-value">
                {latestWeight ? `${latestWeight.kg} kg` : '--'}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Calories</span>
              <span className="stat-value">{todayCalories} kcal</span>
            </div>
            <div className="stat">
              <span className="stat-label">Protein</span>
              <span className="stat-value">{todayProtein}g</span>
            </div>
            <div className="stat">
              <span className="stat-label">Heart Rate</span>
              <span className="stat-value">
                {latestHR ? `${latestHR.avg_bpm} bpm` : '--'}
              </span>
            </div>
          </div>
        </div>

        {/* Weekly Weight Trend */}
        <div className="dashboard-card">
          <h2>Weekly Weight Trend</h2>
          {weightChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={weightChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  interval="preserveStartEnd"
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  domain={['dataMin - 1', 'dataMax + 1']}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #ccc',
                    borderRadius: '8px'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="weight" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                  dot={{ fill: '#8884d8', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">
              <p>No weight data yet. Log your first weight to see your trend!</p>
            </div>
          )}
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