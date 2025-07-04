import React, { useState } from 'react';
import './AmazfitConnectModal.css';

interface AmazfitConnectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const AmazfitConnectModal: React.FC<AmazfitConnectModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/amazfit/connect`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (response.ok) {
        setSuccess('Amazfit account connected successfully!');
        setTimeout(() => {
          onSuccess();
          onClose();
        }, 1500);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to connect. Please check your credentials.');
      }
    } catch (e) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="amazfit-modal-overlay">
      <div className="amazfit-modal">
        <div className="amazfit-modal-header">
          <h2>Connect Amazfit Account</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>
        
        <div className="amazfit-modal-body">
          <p className="modal-description">
            Connect your Amazfit/Zepp account to automatically sync your health data including heart rate, steps, and sleep.
          </p>
          
          <form onSubmit={handleSubmit} className="amazfit-form">
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="username"
                placeholder="Enter your Amazfit email"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder="Enter your Amazfit password"
              />
            </div>
            
            {error && <div className="error-message">{error}</div>}
            {success && <div className="success-message">{success}</div>}
            
            <div className="modal-actions">
              <button type="button" className="cancel-btn" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="connect-btn" disabled={loading}>
                {loading ? 'Connecting...' : 'Connect Account'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AmazfitConnectModal; 