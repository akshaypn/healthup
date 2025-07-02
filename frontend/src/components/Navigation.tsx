import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Navigation.css';

const Navigation: React.FC = () => {
  const { logout } = useAuth();
  const location = useLocation();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/weight', label: 'Weight', icon: '⚖️' },
    { path: '/food', label: 'Food', icon: '🍽️' },
    { path: '/hr', label: 'Heart Rate', icon: '❤️' },
    { path: '/insights', label: 'Insights', icon: '🧠' },
    { path: '/coach', label: 'Coach', icon: '💪' },
  ];

  return (
    <nav className="navigation">
      <div className="nav-header">
        <h1>HealthUp</h1>
        <button onClick={handleLogout} className="logout-btn">
          Logout
        </button>
      </div>
      <div className="nav-items">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
};

export default Navigation; 