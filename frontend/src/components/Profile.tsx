import React, { useState, useEffect } from 'react';
import './Profile.css';
import { apiClient } from '../utils/api';

interface UserProfile {
  id: number;
  user_id: string;
  gender: string;
  height_cm: number;
  weight_kg: number;
  age: number;
  activity_level: string;
  goal: string;
  created_at: string;
  updated_at: string;
}

interface ProfileFormData {
  gender: string;
  height_cm: number;
  weight_kg: number;
  age: number;
  activity_level: string;
  goal: string;
}

const Profile: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [formData, setFormData] = useState<ProfileFormData>({
    gender: '',
    height_cm: 0,
    weight_kg: 0,
    age: 0,
    activity_level: '',
    goal: ''
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await apiClient.get<UserProfile>('/profile');
      
      if (response.data) {
        setProfile(response.data);
        setFormData({
          gender: response.data.gender,
          height_cm: response.data.height_cm,
          weight_kg: response.data.weight_kg,
          age: response.data.age,
          activity_level: response.data.activity_level,
          goal: response.data.goal
        });
      } else if (response.error && response.error.includes('404')) {
        // Profile doesn't exist yet, that's okay
        setProfile(null);
      } else {
        console.error('Failed to fetch profile:', response.error);
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = profile 
        ? await apiClient.put<UserProfile>('/profile', formData)
        : await apiClient.post<UserProfile>('/profile', formData);

      if (response.data) {
        setProfile(response.data);
        setMessage('✅ Profile saved successfully!');
      } else {
        setMessage(`❌ Failed to save profile: ${response.error || 'Unknown error'}`);
      }
    } catch (error) {
      setMessage('❌ Failed to save profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name.includes('height') || name.includes('weight') || name.includes('age') 
        ? parseFloat(value) || 0 
        : value
    }));
  };

  return (
    <div className="profile">
      <div className="profile-container">
        <div className="profile-header">
          <h1>👤 User Profile</h1>
          <p>Set your personal information to get accurate nutritional recommendations</p>
        </div>

        {message && (
          <div className={`message ${message.includes('✅') ? 'success' : 'error'}`}>
            {message}
          </div>
        )}

        <div className="profile-form-card">
          <form onSubmit={handleSubmit} className="profile-form">
            <div className="form-section">
              <h3>Basic Information</h3>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="gender">Gender</label>
                  <select
                    id="gender"
                    name="gender"
                    value={formData.gender}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="">Select gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="age">Age (years)</label>
                  <input
                    type="number"
                    id="age"
                    name="age"
                    value={formData.age || ''}
                    onChange={handleInputChange}
                    min="1"
                    max="120"
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="height_cm">Height (cm)</label>
                  <input
                    type="number"
                    id="height_cm"
                    name="height_cm"
                    value={formData.height_cm || ''}
                    onChange={handleInputChange}
                    min="100"
                    max="250"
                    step="0.1"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="weight_kg">Weight (kg)</label>
                  <input
                    type="number"
                    id="weight_kg"
                    name="weight_kg"
                    value={formData.weight_kg || ''}
                    onChange={handleInputChange}
                    min="30"
                    max="300"
                    step="0.1"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="form-section">
              <h3>Activity & Goals</h3>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="activity_level">Activity Level</label>
                  <select
                    id="activity_level"
                    name="activity_level"
                    value={formData.activity_level}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="">Select activity level</option>
                    <option value="sedentary">Sedentary (little or no exercise)</option>
                    <option value="lightly_active">Lightly Active (light exercise 1-3 days/week)</option>
                    <option value="moderately_active">Moderately Active (moderate exercise 3-5 days/week)</option>
                    <option value="very_active">Very Active (hard exercise 6-7 days/week)</option>
                    <option value="extremely_active">Extremely Active (very hard exercise, physical job)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="goal">Fitness Goal</label>
                  <select
                    id="goal"
                    name="goal"
                    value={formData.goal}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="">Select goal</option>
                    <option value="lose_weight">Lose Weight</option>
                    <option value="maintain_weight">Maintain Weight</option>
                    <option value="gain_weight">Gain Weight</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="form-actions">
              <button
                type="submit"
                disabled={loading}
                className="save-btn"
              >
                {loading ? 'Saving...' : (profile ? 'Update Profile' : 'Create Profile')}
              </button>
            </div>
          </form>
        </div>

        {profile && (
          <div className="profile-info-card">
            <h3>📊 Current Profile</h3>
            <div className="profile-info">
              <div className="info-row">
                <span className="label">Gender:</span>
                <span className="value">{profile.gender}</span>
              </div>
              <div className="info-row">
                <span className="label">Age:</span>
                <span className="value">{profile.age} years</span>
              </div>
              <div className="info-row">
                <span className="label">Height:</span>
                <span className="value">{profile.height_cm} cm</span>
              </div>
              <div className="info-row">
                <span className="label">Weight:</span>
                <span className="value">{profile.weight_kg} kg</span>
              </div>
              <div className="info-row">
                <span className="label">Activity Level:</span>
                <span className="value">{profile.activity_level.replace('_', ' ')}</span>
              </div>
              <div className="info-row">
                <span className="label">Goal:</span>
                <span className="value">{profile.goal.replace('_', ' ')}</span>
              </div>
              <div className="info-row">
                <span className="label">Last Updated:</span>
                <span className="value">{new Date(profile.updated_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Profile; 