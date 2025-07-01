import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './FoodLog.css';

interface FoodEntry {
  id: number;
  description: string;
  calories: number;
  protein_g: number;
  fat_g: number;
  carbs_g: number;
  logged_at: string;
}

const FoodLog: React.FC = () => {
  const [formData, setFormData] = useState({
    description: '',
    calories: '',
    protein_g: '',
    fat_g: '',
    carbs_g: ''
  });
  const [foodHistory, setFoodHistory] = useState<FoodEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchFoodHistory();
  }, []);

  const fetchFoodHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/food/history`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        // Ensure we have an array, even if the API returns unexpected data
        const logs = Array.isArray(data.logs) ? data.logs : [];
        setFoodHistory(logs);
      }
    } catch (error) {
      console.error('Failed to fetch food history:', error);
      setFoodHistory([]); // Set empty array on error
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/food`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          description: formData.description,
          calories: parseInt(formData.calories) || 0,
          protein_g: parseInt(formData.protein_g) || 0,
          fat_g: parseInt(formData.fat_g) || 0,
          carbs_g: parseInt(formData.carbs_g) || 0
        })
      });

      if (response.ok) {
        setMessage('Food logged successfully!');
        setFormData({
          description: '',
          calories: '',
          protein_g: '',
          fat_g: '',
          carbs_g: ''
        });
        fetchFoodHistory();
      } else {
        setMessage('Failed to log food. Please try again.');
      }
    } catch (error) {
      setMessage('Failed to log food. Please try again.');
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

  const todayEntries = (foodHistory || []).filter(entry => 
    new Date(entry.logged_at).toDateString() === new Date().toDateString()
  );

  const todayTotals = todayEntries.reduce((acc, entry) => ({
    calories: acc.calories + entry.calories,
    protein: acc.protein + entry.protein_g,
    fat: acc.fat + entry.fat_g,
    carbs: acc.carbs + entry.carbs_g
  }), { calories: 0, protein: 0, fat: 0, carbs: 0 });

  const chartData = [
    { name: 'Protein', value: todayTotals.protein, color: '#8884d8' },
    { name: 'Fat', value: todayTotals.fat, color: '#82ca9d' },
    { name: 'Carbs', value: todayTotals.carbs, color: '#ffc658' }
  ];

  return (
    <div className="food-log">
      <h1>Food Tracking</h1>
      
      <div className="food-container">
        {/* Log Food Form */}
        <div className="food-form-card">
          <h2>Log a Meal</h2>
          <form onSubmit={handleSubmit} className="food-form">
            <div className="form-group">
              <label htmlFor="description">Food Description</label>
              <input
                type="text"
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                placeholder="e.g., Grilled chicken with rice"
                required
              />
            </div>
            
            <div className="macros-grid">
              <div className="form-group">
                <label htmlFor="calories">Calories</label>
                <input
                  type="number"
                  id="calories"
                  name="calories"
                  value={formData.calories}
                  onChange={handleInputChange}
                  placeholder="0"
                  min="0"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="protein_g">Protein (g)</label>
                <input
                  type="number"
                  id="protein_g"
                  name="protein_g"
                  value={formData.protein_g}
                  onChange={handleInputChange}
                  placeholder="0"
                  min="0"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="fat_g">Fat (g)</label>
                <input
                  type="number"
                  id="fat_g"
                  name="fat_g"
                  value={formData.fat_g}
                  onChange={handleInputChange}
                  placeholder="0"
                  min="0"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="carbs_g">Carbs (g)</label>
                <input
                  type="number"
                  id="carbs_g"
                  name="carbs_g"
                  value={formData.carbs_g}
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
            
            <button type="submit" disabled={loading} className="submit-btn">
              {loading ? 'Logging...' : 'Log Food'}
            </button>
          </form>
        </div>

        {/* Today's Summary */}
        <div className="food-summary-card">
          <h2>Today's Nutrition</h2>
          <div className="nutrition-summary">
            <div className="nutrition-item">
              <span className="nutrition-label">Calories</span>
              <span className="nutrition-value">{todayTotals.calories} kcal</span>
            </div>
            <div className="nutrition-item">
              <span className="nutrition-label">Protein</span>
              <span className="nutrition-value">{todayTotals.protein}g</span>
            </div>
            <div className="nutrition-item">
              <span className="nutrition-label">Fat</span>
              <span className="nutrition-value">{todayTotals.fat}g</span>
            </div>
            <div className="nutrition-item">
              <span className="nutrition-label">Carbs</span>
              <span className="nutrition-value">{todayTotals.carbs}g</span>
            </div>
          </div>
          
          <div className="macros-chart">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Entries */}
        <div className="food-history-card">
          <h2>Today's Meals</h2>
          <div className="food-history">
            {(todayEntries || []).length > 0 ? (
              todayEntries.map((entry) => (
                <div key={entry.id} className="food-entry">
                  <div className="food-info">
                    <span className="food-description">{entry.description}</span>
                    <span className="food-time">
                      {new Date(entry.logged_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="food-macros">
                    <span>{entry.calories} kcal</span>
                    <span>P: {entry.protein_g}g</span>
                    <span>F: {entry.fat_g}g</span>
                    <span>C: {entry.carbs_g}g</span>
                  </div>
                </div>
              ))
            ) : (
              <p>No meals logged today.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FoodLog; 