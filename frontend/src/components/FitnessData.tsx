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

  // Steps progression through the day (only show if we have real data)
  const hasRealStepData = dayData?.steps && dayData.steps > 0;
  const stepsProgression = hasRealStepData ? (() => {
    const totalSteps = dayData.steps;
    const stepsPerHour = totalSteps / 24;
    
    const progression = [];
    for (let hour = 0; hour < 24; hour++) {
      progression.push({
        hour: `${hour}:00`,
        steps: Math.round(stepsPerHour * (hour + 1)) // Cumulative steps
      });
    }
    return progression;
  })() : [];

  // Sleep data processing
  const sleepDurationHours = (dayData?.sleep_duration || 0) / 3600;
  const sleepData = [
    { name: 'Sleep', value: sleepDurationHours, color: '#6366f1' },
    { name: 'Awake', value: 24 - sleepDurationHours, color: '#f3f4f6' }
  ];

  // Calculate sleep statistics
  const sleepStats = {
    duration: sleepDurationHours,
    hours: Math.floor(sleepDurationHours),
    minutes: Math.round((sleepDurationHours % 1) * 60)
  };

  return (
    <div className="hr-log">
      <h1>Heart Rate & Activity (Amazfit)</h1>
      <div className="hr-container">
        {/* Connection Status */}
        {isConnected && (
          <div className="hr-status-card">
            <div className="status">✅ Connected to Amazfit Cloud</div>
            <div className="last-sync">Last sync: {syncTime}</div>
            <button className="sync-btn" onClick={() => fetchDayData(selectedDate)} disabled={loading}>
              {loading ? 'Syncing...' : 'Sync Now'}
            </button>
            <button 
              className="reconnect-btn" 
              onClick={() => setShowConnectModal(true)}
              style={{ marginTop: '8px', background: '#6b7280' }}
            >
              Reconnect Account
            </button>
          </div>
        )}

        {/* Date Picker Button */}
        <div className="date-picker-card">
          <h2>Selected Date</h2>
          <button 
            className="date-picker-btn" 
            onClick={() => setShowDatePicker(true)}
          >
            {selectedDate.toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
            <span className="date-picker-icon">📅</span>
          </button>
        </div>

        {/* Data Display */}
        <div className="data-cards">
          {/* HR Chart */}
          <div className="hr-chart-card">
            <h2>Heart Rate Trend (24h)</h2>
            {loading ? <div className="loading">Loading...</div> : hrChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={hrChartData} margin={{ top: 10, right: 30, left: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    dataKey="time" 
                    tick={{ fontSize: 10, fill: '#6b7280' }}
                    interval={Math.floor(hrChartData.length / 6)} // Show ~6 time labels
                    axisLine={{ stroke: '#d1d5db' }}
                  />
                  <YAxis 
                    domain={[30, 240]} // Amazfit HR range
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
            ) : <div className="no-data">No HR data for this day.</div>}
          </div>

          {/* Steps & Calories Numbers */}
          <div className="steps-bar-card">
            <h2>Daily Activity</h2>
            {loading ? <div className="loading">Loading...</div> : (
              <div className="activity-stats">
                <div className="stat-item">
                  <div className="stat-value">{dayData?.steps?.toLocaleString() || 0}</div>
                  <div className="stat-label">Steps</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">{dayData?.calories?.toLocaleString() || 0}</div>
                  <div className="stat-label">Calories</div>
                </div>
              </div>
            )}
          </div>

          {/* Steps Progression Chart - Only show if we have real data */}
          {hasRealStepData && (
            <div className="steps-progression-card">
              <h2>Steps Progress</h2>
              {loading ? <div className="loading">Loading...</div> : (
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={stepsProgression} margin={{ top: 10, right: 30, left: 20, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="hour" 
                      tick={{ fontSize: 10, fill: '#6b7280' }}
                      interval={3} // Show every 4th hour
                      axisLine={{ stroke: '#d1d5db' }}
                    />
                    <YAxis 
                      tick={{ fontSize: 10, fill: '#6b7280' }}
                      axisLine={{ stroke: '#d1d5db' }}
                    />
                    <Tooltip 
                      formatter={(value: any) => [`${value.toLocaleString()} steps`, 'Cumulative Steps']}
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
                      dataKey="steps" 
                      stroke="#3b82f6" 
                      strokeWidth={3}
                      dot={false}
                      activeDot={{ r: 4, fill: '#3b82f6' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          )}

          {/* Sleep Data */}
          <div className="sleep-pie-card">
            <h2>Sleep Summary</h2>
            {loading ? <div className="loading">Loading...</div> : sleepStats.duration > 0 ? (
              <div className="sleep-content">
                <div className="sleep-stats">
                  <div className="sleep-duration">
                    <span className="sleep-hours">{sleepStats.hours}</span>
                    <span className="sleep-label">h</span>
                    <span className="sleep-minutes">{sleepStats.minutes}</span>
                    <span className="sleep-label">m</span>
                  </div>
                  <div className="sleep-text">Total Sleep</div>
                </div>
                <div className="sleep-chart">
                  <ResponsiveContainer width="100%" height={120}>
                    <PieChart>
                      <Pie 
                        data={sleepData} 
                        dataKey="value" 
                        nameKey="name" 
                        cx="50%" 
                        cy="50%" 
                        outerRadius={50} 
                        innerRadius={30}
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
                </div>
              </div>
            ) : <div className="no-data">No sleep data for this day.</div>}
          </div>
        </div>

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