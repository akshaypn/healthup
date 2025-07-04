import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Dashboard from './components/Dashboard'
import Login from './components/Login'
import Register from './components/Register'
import WeightLog from './components/WeightLog'
import FoodLog from './components/FoodLog'
import FoodBank from './components/FoodBank'
import Profile from './components/Profile'
import HRLog from './components/HRLog'
import Insights from './components/Insights'
import Coach from './components/Coach'
import Navigation from './components/Navigation'
import './App.css'

// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('SW registered: ', registration);
      })
      .catch((registrationError) => {
        console.log('SW registration failed: ', registrationError);
      });
  });
}

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return <div className="loading">Loading...</div>;
  }
  
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={
              <PrivateRoute>
                <div className="app-container">
                  <Navigation />
                  <main className="main-content">
                    <Dashboard />
                  </main>
                </div>
              </PrivateRoute>
            } />
            <Route path="/weight" element={
              <PrivateRoute>
                <div className="app-container">
                  <Navigation />
                  <main className="main-content">
                    <WeightLog />
                  </main>
                </div>
              </PrivateRoute>
            } />
            <Route path="/food" element={
              <PrivateRoute>
                <div className="app-container">
                  <Navigation />
                  <main className="main-content">
                    <FoodLog />
                  </main>
                </div>
              </PrivateRoute>
            } />
            <Route path="/food-bank" element={
              <PrivateRoute>
                <div className="app-container">
                  <Navigation />
                  <main className="main-content">
                    <FoodBank />
                  </main>
                </div>
              </PrivateRoute>
            } />
            <Route path="/profile" element={
              <PrivateRoute>
                <div className="app-container">
                  <Navigation />
                  <main className="main-content">
                    <Profile />
                  </main>
                </div>
              </PrivateRoute>
            } />
            <Route path="/hr" element={
              <PrivateRoute>
                <div className="app-container">
                  <Navigation />
                  <main className="main-content">
                    <HRLog />
                  </main>
                </div>
              </PrivateRoute>
            } />
            <Route path="/insights" element={
              <PrivateRoute>
                <div className="app-container">
                  <Navigation />
                  <main className="main-content">
                    <Insights />
                  </main>
                </div>
              </PrivateRoute>
            } />
            <Route path="/coach" element={
              <PrivateRoute>
                <div className="app-container">
                  <Navigation />
                  <main className="main-content">
                    <Coach />
                  </main>
                </div>
              </PrivateRoute>
            } />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;
