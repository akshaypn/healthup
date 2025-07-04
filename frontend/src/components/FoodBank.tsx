import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import './FoodBank.css';

interface NutritionalRequirement {
  nutrient: string;
  daily_target: number;
  unit: string;
  consumed: number;
  remaining: number;
  percentage: number;
  status: string; // under, adequate, over
}

interface NutritionalSummary {
  period: string;
  period_start: string;
  period_end: string;
  total_calories: number;
  total_protein: number;
  total_fat: number;
  total_carbs: number;
  requirements: NutritionalRequirement[];
  summary: {
    total_food_items: number;
    average_calories_per_day: number;
    completion_rate: number;
  };
}

interface FoodLog {
  id: number;
  description: string;
  calories: number | null;
  protein_g: number | null;
  fat_g: number | null;
  carbs_g: number | null;
  logged_at: string;
}

interface FoodBankData {
  summary: NutritionalSummary;
  food_logs: FoodLog[];
}

const FoodBank: React.FC = () => {
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [data, setData] = useState<FoodBankData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFoodBankData();
  }, [period]);

  const fetchFoodBankData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/food-bank/${period}`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const foodBankData = await response.json();
        setData(foodBankData);
      } else if (response.status === 404) {
        setError('Profile not found. Please create a profile first.');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to fetch food bank data');
      }
    } catch (error) {
      setError('Failed to fetch food bank data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'under': return '#ef4444';
      case 'adequate': return '#22c55e';
      case 'over': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'under': return '⚠️';
      case 'adequate': return '✅';
      case 'over': return '⚠️';
      default: return '❓';
    }
  };

  const formatNutrientName = (nutrient: string) => {
    return nutrient
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
      .replace('G', 'g')
      .replace('Mg', 'mg')
      .replace('Mcg', 'μg');
  };

  const chartData = data?.summary.requirements
    .filter(req => ['calories', 'protein_g', 'fat_g', 'carbs_g', 'fiber_g'].includes(req.nutrient))
    .map(req => ({
      name: formatNutrientName(req.nutrient),
      consumed: req.consumed,
      target: req.daily_target,
      percentage: req.percentage
    })) || [];

  const pieData = [
    { name: 'Protein', value: data?.summary.total_protein || 0, color: '#8884d8' },
    { name: 'Fat', value: data?.summary.total_fat || 0, color: '#82ca9d' },
    { name: 'Carbs', value: data?.summary.total_carbs || 0, color: '#ffc658' }
  ];

  if (loading) {
    return (
      <div className="food-bank">
        <div className="loading">Loading food bank data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="food-bank">
        <div className="error-message">
          <h2>❌ Error</h2>
          <p>{error}</p>
          {error.includes('Profile not found') && (
            <a href="/profile" className="profile-link">Create Profile</a>
          )}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="food-bank">
        <div className="no-data">No data available</div>
      </div>
    );
  }

  return (
    <div className="food-bank">
      <div className="food-bank-container">
        <div className="food-bank-header">
          <h1>🏦 Food Bank</h1>
          <p>Track your nutritional intake and requirements</p>
          
          <div className="period-selector">
            <button
              className={`period-btn ${period === 'daily' ? 'active' : ''}`}
              onClick={() => setPeriod('daily')}
            >
              Daily
            </button>
            <button
              className={`period-btn ${period === 'weekly' ? 'active' : ''}`}
              onClick={() => setPeriod('weekly')}
            >
              Weekly
            </button>
            <button
              className={`period-btn ${period === 'monthly' ? 'active' : ''}`}
              onClick={() => setPeriod('monthly')}
            >
              Monthly
            </button>
          </div>
        </div>

        <div className="summary-cards">
          <div className="summary-card">
            <h3>📊 Overview</h3>
            <div className="summary-stats">
              <div className="stat">
                <span className="stat-label">Total Calories</span>
                <span className="stat-value">{Math.round(data.summary.total_calories)}</span>
                <span className="stat-unit">kcal</span>
              </div>
              <div className="stat">
                <span className="stat-label">Food Items</span>
                <span className="stat-value">{data.summary.summary.total_food_items}</span>
                <span className="stat-unit">items</span>
              </div>
              <div className="stat">
                <span className="stat-label">Completion Rate</span>
                <span className="stat-value">{Math.round(data.summary.summary.completion_rate)}%</span>
                <span className="stat-unit">complete</span>
              </div>
            </div>
          </div>

          <div className="summary-card">
            <h3>🍽️ Macronutrients</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={60}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="charts-section">
          <div className="chart-card">
            <h3>📈 Nutrient Progress</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="consumed" fill="#667eea" name="Consumed" />
                <Bar dataKey="target" fill="#e5e7eb" name="Target" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="requirements-section">
          <h2>🎯 Nutritional Requirements</h2>
          <div className="requirements-grid">
            {data.summary.requirements.map((req) => (
              <div key={req.nutrient} className={`requirement-card ${req.status}`}>
                <div className="requirement-header">
                  <h4>{formatNutrientName(req.nutrient)}</h4>
                  <span className={`status-badge ${req.status}`}>
                    {getStatusIcon(req.status)} {req.status}
                  </span>
                </div>
                
                <div className="requirement-progress">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{ 
                        width: `${Math.min(req.percentage, 100)}%`,
                        backgroundColor: getStatusColor(req.status)
                      }}
                    />
                  </div>
                  <span className="progress-text">{Math.round(req.percentage)}%</span>
                </div>
                
                <div className="requirement-details">
                  <div className="detail-row">
                    <span>Consumed:</span>
                    <span>{Math.round(req.consumed)} {req.unit}</span>
                  </div>
                  <div className="detail-row">
                    <span>Target:</span>
                    <span>{Math.round(req.daily_target)} {req.unit}</span>
                  </div>
                  <div className="detail-row">
                    <span>Remaining:</span>
                    <span className={req.remaining < 0 ? 'negative' : ''}>
                      {Math.round(req.remaining)} {req.unit}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="food-logs-section">
          <h2>📝 Recent Food Logs</h2>
          <div className="food-logs-list">
            {data.food_logs.length === 0 ? (
              <div className="no-logs">No food logs for this period</div>
            ) : (
              data.food_logs.map((log) => (
                <div key={log.id} className="food-log-item">
                  <div className="food-log-header">
                    <h4>{log.description}</h4>
                    <span className="food-log-date">
                      {new Date(log.logged_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="food-log-nutrition">
                    <span className="nutrition-item">
                      {log.calories || 0} kcal
                    </span>
                    <span className="nutrition-item">
                      {log.protein_g || 0}g protein
                    </span>
                    <span className="nutrition-item">
                      {log.carbs_g || 0}g carbs
                    </span>
                    <span className="nutrition-item">
                      {log.fat_g || 0}g fat
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FoodBank; 