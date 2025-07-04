import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import AmazfitConnectModal from './AmazfitConnectModal';
import './HRLog.css';

interface AmazfitDayData {
  date: string;
  heart_rate: number[];
  steps: number;
  calories: number;
  sleep_duration: number;
  activity: {
    steps?: number;
    calories?: number;
    distance?: number;
    active_minutes?: number;
  };
  sleep: {
    sleep_time_hours?: number;
    deep_sleep_hours?: number;
    light_sleep_hours?: number;
    rem_sleep_hours?: number;
    awake_hours?: number;
    sleep_time_seconds?: number;
    sleep_start?: number;
    sleep_end?: number;
  };
  summary: any;
  cached?: boolean;
  workouts?: any[];
  events?: any[];
  hrv?: number;
  hr_stats?: {
    avg_hr?: number;
    max_hr?: number;
    min_hr?: number;
    valid_readings?: number;
    total_readings?: number;
  };
}

const HRLog: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [dayData, setDayData] = useState<AmazfitDayData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [syncTime, setSyncTime] = useState<string>('');

  // Check connection status on mount
  useEffect(() => {
    checkConnectionStatus();
  }, []);

  // Fetch data for selected day when connected
  useEffect(() => {
    if (isConnected) {
      fetchDayData(selectedDate);
    }
  }, [isConnected, selectedDate]);

  const checkConnectionStatus = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/amazfit/credentials`, {
        credentials: 'include',
      });
      
      if (response.ok) {
        setIsConnected(true);
        // Fetch today's data if connected
        fetchDayData(new Date());
      } else {
        setIsConnected(false);
        setShowConnectModal(true);
      }
    } catch (e) {
      setIsConnected(false);
      setShowConnectModal(true);
    }
  };

  // Fetch data for selected day
  const fetchDayData = async (date: Date) => {
    setLoading(true);
    setError('');
    setDayData(null);
    try {
      const dayStr = date.toISOString().slice(0, 10);
      const response = await fetch(`${import.meta.env.VITE_API_URL}/amazfit/day?date_str=${dayStr}`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setDayData(data);
        setSyncTime(new Date().toLocaleString());
        
        // Check if we have any meaningful data
        const hasData = data.heart_rate?.length > 0 || data.steps > 0 || data.calories > 0;
        if (!hasData) {
          setError('No activity data available for this date. Try selecting a different date.');
        }
      } else if (response.status === 404) {
        setError('No data available for this date.');
      } else {
        setError('Failed to fetch data for selected day.');
      }
    } catch (e) {
      setError('Network error.');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectSuccess = () => {
    setIsConnected(true);
    setShowConnectModal(false);
    fetchDayData(selectedDate);
  };

  // Calendar date change
  const handleDateChange = (value: any) => {
    if (value instanceof Date) {
      setSelectedDate(value);
    }
  };

  // Chart data transforms
  // Process heart rate data - remove spikes and invalid values, better time formatting
  const hrChartData = (() => {
    const hrData = dayData?.heart_rate || [];
    
    if (!Array.isArray(hrData) || hrData.length === 0) {
      return [];
    }
    
    return hrData
      .map((bpm, i) => {
        const hour = Math.floor(i / 60);
        const minute = i % 60;
        return {
          time: `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`,
          bpm: bpm > 30 && bpm < 240 ? bpm : null // Filter out invalid values (30-240 BPM range)
        };
      })
      .filter(d => d.bpm !== null)
      .slice(0, 1440); // Limit to 24 hours (1440 minutes)
  })();



  // Sleep data processing
  const sleepDurationHours = (dayData?.sleep_duration || 0) / 3600;
  const sleepData = [
    { name: 'Deep Sleep', value: dayData?.sleep?.deep_sleep_hours || 0, color: '#1e40af' },
    { name: 'Light Sleep', value: dayData?.sleep?.light_sleep_hours || 0, color: '#3b82f6' },
    { name: 'REM Sleep', value: dayData?.sleep?.rem_sleep_hours || 0, color: '#6366f1' },
    { name: 'Awake', value: dayData?.sleep?.awake_hours || 0, color: '#f3f4f6' }
  ].filter(item => item.value > 0);

  // Calculate sleep statistics
  const sleepStats = {
    duration: sleepDurationHours,
    hours: Math.floor(sleepDurationHours),
    minutes: Math.round((sleepDurationHours % 1) * 60)
  };

  // Heart rate statistics
  const hrStats = dayData?.hr_stats || {};
  const validHrReadings = hrStats.valid_readings || 0;
  const totalHrReadings = hrStats.total_readings || 1440; // 24 hours * 60 minutes

  // Activity statistics
  const distanceKm = dayData?.activity?.distance || 0;
  const activeMinutes = dayData?.activity?.active_minutes || 0;

  // Utility function to format timestamps in IST
  const formatTimestampIST = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  // Activity score calculation
  const activityScore = (() => {
    const steps = dayData?.steps || 0;
    const calories = dayData?.calories || 0;
    const sleepHours = sleepDurationHours;
    
    let score = 0;
    if (steps >= 10000) score += 40;
    else if (steps >= 7500) score += 30;
    else if (steps >= 5000) score += 20;
    else if (steps >= 2500) score += 10;
    
    if (calories >= 500) score += 30;
    else if (calories >= 300) score += 20;
    else if (calories >= 150) score += 10;
    
    if (sleepHours >= 7 && sleepHours <= 9) score += 30;
    else if (sleepHours >= 6 && sleepHours <= 10) score += 20;
    else if (sleepHours >= 5) score += 10;
    
    return Math.min(score, 100);
  })();

  return (
    <div className="hr-log">
      {/* Header Section */}
      <div className="header-section">
        <h1>🏃‍♂️ Amazfit Health Dashboard</h1>
        <p className="subtitle">Your daily health and fitness insights</p>
      </div>

      <div className="hr-container">
        {/* Connection Status */}
        {isConnected && (
          <div className="status-banner">
            <div className="status-content">
              <div className="status-indicator">
                <span className="status-dot connected"></span>
                <span className="status-text">Connected to Amazfit Cloud</span>
              </div>
              <div className="status-actions">
                <span className="last-sync">Last sync: {syncTime}</span>
                <button className="sync-btn" onClick={() => fetchDayData(selectedDate)} disabled={loading}>
                  {loading ? '🔄 Syncing...' : '🔄 Sync Now'}
                </button>
                <button 
                  className="reconnect-btn" 
                  onClick={() => setShowConnectModal(true)}
                >
                  ⚙️ Settings
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Date Picker */}
        <div className="date-section">
          <button 
            className="date-picker-btn" 
            onClick={() => setShowDatePicker(true)}
          >
            <span className="date-icon">📅</span>
            <span className="date-text">
              {selectedDate.toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </span>
            <span className="date-arrow">▼</span>
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
            <p>Fetching your health data...</p>
          </div>
        )}

        {/* Main Content */}
        {!loading && dayData && (
          <div className="dashboard-grid">
            {/* Activity Score Card */}
            <div className="score-card">
              <div className="score-header">
                <h2>📊 Daily Score</h2>
                <div className="score-circle">
                  <span className="score-value">{activityScore}</span>
                  <span className="score-label">/100</span>
                </div>
              </div>
              <div className="score-breakdown">
                <div className="score-item">
                  <span className="score-icon">👟</span>
                  <span className="score-text">Steps</span>
                  <span className="score-value-small">{dayData.steps?.toLocaleString() || 0}</span>
                </div>
                <div className="score-item">
                  <span className="score-icon">🔥</span>
                  <span className="score-text">Calories</span>
                  <span className="score-value-small">{dayData.calories?.toLocaleString() || 0}</span>
                </div>
                <div className="score-item">
                  <span className="score-icon">😴</span>
                  <span className="score-text">Sleep</span>
                  <span className="score-value-small">{sleepStats.hours}h {sleepStats.minutes}m</span>
                </div>
              </div>
            </div>

            {/* Activity Metrics */}
            <div className="metrics-grid">
              <div className="metric-card steps">
                <div className="metric-icon">👟</div>
                <div className="metric-content">
                  <h3>Steps</h3>
                  <div className="metric-value">{dayData.steps?.toLocaleString() || 0}</div>
                  <div className="metric-details">
                    <span>{distanceKm.toFixed(1)} km</span>
                    <span>•</span>
                    <span>{activeMinutes} min active</span>
                  </div>
                </div>
              </div>

              <div className="metric-card calories">
                <div className="metric-icon">🔥</div>
                <div className="metric-content">
                  <h3>Calories</h3>
                  <div className="metric-value">{dayData.calories?.toLocaleString() || 0}</div>
                  <div className="metric-details">
                    <span>kcal burned</span>
                  </div>
                </div>
              </div>

              <div className="metric-card heart-rate">
                <div className="metric-icon">❤️</div>
                <div className="metric-content">
                  <h3>Heart Rate</h3>
                  <div className="metric-value">{hrStats.avg_hr || 0}</div>
                  <div className="metric-details">
                    <span>{hrStats.min_hr || 0} - {hrStats.max_hr || 0} bpm</span>
                  </div>
                </div>
              </div>

              <div className="metric-card sleep">
                <div className="metric-icon">😴</div>
                <div className="metric-content">
                  <h3>Sleep</h3>
                  <div className="metric-value">{sleepStats.hours}h {sleepStats.minutes}m</div>
                  <div className="metric-details">
                    <span>Total sleep time</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Heart Rate Chart */}
            <div className="chart-card hr-chart">
              <div className="chart-header">
                <h2>❤️ Heart Rate Trend</h2>
                <div className="chart-stats">
                  <span className="stat-item">
                    <span className="stat-label">Avg:</span>
                    <span className="stat-value">{hrStats.avg_hr || 0} bpm</span>
                  </span>
                  <span className="stat-item">
                    <span className="stat-label">Valid:</span>
                    <span className="stat-value">{validHrReadings}/{totalHrReadings}</span>
                  </span>
                </div>
              </div>
              {hrChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={hrChartData} margin={{ top: 10, right: 30, left: 20, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="time" 
                      tick={{ fontSize: 10, fill: '#6b7280' }}
                      interval={Math.floor(hrChartData.length / 6)}
                      axisLine={{ stroke: '#d1d5db' }}
                    />
                    <YAxis 
                      domain={[30, 240]}
                      tick={{ fontSize: 10, fill: '#6b7280' }}
                      axisLine={{ stroke: '#d1d5db' }}
                    />
                    <Tooltip 
                      formatter={(value: any) => [`${value} BPM`, 'Heart Rate']}
                      labelFormatter={(label: any) => `Time: ${label}`}
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        border: '1px solid #d1d5db',
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                      }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="bpm" 
                      stroke="#ef4444" 
                      strokeWidth={3}
                      dot={false}
                      connectNulls={false}
                      activeDot={{ r: 4, fill: '#ef4444' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="no-data">No heart rate data available</div>
              )}
            </div>

            {/* Sleep Analysis */}
            <div className="chart-card sleep-chart">
              <div className="chart-header">
                <h2>😴 Sleep Analysis</h2>
                <div className="sleep-summary">
                  <span className="sleep-total">{sleepStats.hours}h {sleepStats.minutes}m</span>
                  <span className="sleep-label">total sleep</span>
                  {dayData?.sleep?.sleep_start && dayData?.sleep?.sleep_end && (
                    <div className="sleep-timing">
                      <span className="timing-label">Sleep Time (IST):</span>
                      <span className="timing-value">
                        {formatTimestampIST(dayData.sleep.sleep_start)} - {formatTimestampIST(dayData.sleep.sleep_end)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
              {sleepData.length > 0 ? (
                <div className="sleep-content">
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie 
                        data={sleepData} 
                        dataKey="value" 
                        nameKey="name" 
                        cx="50%" 
                        cy="50%" 
                        outerRadius={80} 
                        innerRadius={40}
                      >
                        {sleepData.map((entry, idx) => (
                          <Cell key={`cell-${idx}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value: any) => [`${value.toFixed(1)} hours`, 'Duration']}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                                     <div className="sleep-breakdown">
                     {(dayData?.sleep?.deep_sleep_hours || 0) > 0 && (
                       <div className="sleep-stage">
                         <span className="stage-color" style={{backgroundColor: '#1e40af'}}></span>
                         <span className="stage-name">Deep Sleep</span>
                         <span className="stage-time">{Math.floor((dayData?.sleep?.deep_sleep_hours || 0) * 60)}m</span>
                       </div>
                     )}
                     {(dayData?.sleep?.light_sleep_hours || 0) > 0 && (
                       <div className="sleep-stage">
                         <span className="stage-color" style={{backgroundColor: '#3b82f6'}}></span>
                         <span className="stage-name">Light Sleep</span>
                         <span className="stage-time">{Math.floor((dayData?.sleep?.light_sleep_hours || 0) * 60)}m</span>
                       </div>
                     )}
                     {(dayData?.sleep?.rem_sleep_hours || 0) > 0 && (
                       <div className="sleep-stage">
                         <span className="stage-color" style={{backgroundColor: '#6366f1'}}></span>
                         <span className="stage-name">REM Sleep</span>
                         <span className="stage-time">{Math.floor((dayData?.sleep?.rem_sleep_hours || 0) * 60)}m</span>
                       </div>
                     )}
                     {(dayData?.sleep?.awake_hours || 0) > 0 && (
                       <div className="sleep-stage">
                         <span className="stage-color" style={{backgroundColor: '#f3f4f6'}}></span>
                         <span className="stage-name">Awake</span>
                         <span className="stage-time">{Math.floor((dayData?.sleep?.awake_hours || 0) * 60)}m</span>
                       </div>
                     )}
                   </div>
                </div>
              ) : (
                <div className="no-data">No sleep data available</div>
              )}
            </div>

            {/* Additional Data */}
            <div className="additional-data">
              <div className="data-card">
                <h3>🏃‍♀️ Workouts</h3>
                <div className="data-value">
                  {dayData?.workouts?.length || 0} workouts recorded
                </div>
              </div>
              
              <div className="data-card">
                <h3>📱 Events</h3>
                <div className="data-value">
                  {dayData?.events?.length || 0} events recorded
                </div>
              </div>
              
              <div className="data-card">
                <h3>💓 HRV</h3>
                <div className="data-value">
                  {dayData?.hrv || 0} ms (RMSSD)
                </div>
              </div>
              
              <div className="data-card">
                <h3>💾 Cache</h3>
                <div className="data-value">
                  {dayData?.cached ? '✅ Cached' : '🔄 Fresh'}
                </div>
              </div>
            </div>
          </div>
        )}

        {error && <div className="error-message">{error}</div>}
      </div>

      {/* Amazfit Connection Modal */}
      <AmazfitConnectModal
        isOpen={showConnectModal}
        onClose={() => setShowConnectModal(false)}
        onSuccess={handleConnectSuccess}
      />

      {/* Date Picker Modal */}
      {showDatePicker && (
        <div className="modal-overlay" onClick={() => setShowDatePicker(false)}>
          <div className="date-picker-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Select Date</h3>
              <button 
                className="close-btn" 
                onClick={() => setShowDatePicker(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-content">
              <Calendar 
                value={selectedDate} 
                onChange={handleDateChange} 
                maxDate={new Date()}
                className="calendar-popup"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HRLog; 