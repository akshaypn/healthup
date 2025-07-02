import React, { useState, useEffect } from 'react';
import { GoogleGenAI } from '@google/genai';
import './Coach.css';

interface CoachAdvice {
  tips: string[];
  message: string;
}

const Coach: React.FC = () => {
  const [advice, setAdvice] = useState<CoachAdvice | null>(null);
  const [loading, setLoading] = useState(false);
  const [userQuestion, setUserQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState<Array<{ question: string; answer: string }>>([]);

  useEffect(() => {
    fetchTodayAdvice();
  }, []);

  const fetchTodayAdvice = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/coach/today`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAdvice(data);
      }
    } catch (error) {
      console.error('Failed to fetch coach advice:', error);
    }
  };

  const askCoach = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userQuestion.trim()) return;

    setLoading(true);
    const question = userQuestion;
    setUserQuestion('');

    try {
      // Use Google Gemini API for real-time coaching
      const ai = new GoogleGenAI({ apiKey: import.meta.env.VITE_GEMINI_API_KEY });
      
      const prompt = `You are a personal health coach. The user is asking: "${question}". 
      Provide a helpful, encouraging, and actionable response in 2-3 sentences. 
      Focus on practical advice and motivation.`;

      const response = await ai.models.generateContent({
        model: "gemini-2.0-flash-exp",
        contents: prompt,
        config: {
          temperature: 0.7,
        },
      });

      const answer = response.text || "I'm sorry, I couldn't generate a response right now.";
      
      setChatHistory(prev => [...prev, { question, answer }]);
    } catch (error) {
      console.error('Failed to get coach response:', error);
      setChatHistory(prev => [...prev, { 
        question, 
        answer: "I'm having trouble connecting right now. Please try again later or check your internet connection." 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="coach">
      <h1>Your AI Health Coach</h1>
      
      <div className="coach-container">
        {/* Today's Advice */}
        <div className="today-advice-card">
          <h2>Today's Quick Tips</h2>
          {advice ? (
            <div className="advice-content">
              <p className="advice-message">{advice.message}</p>
              <ul className="advice-tips">
                {advice.tips.map((tip, index) => (
                  <li key={index} className="tip-item">
                    <span className="tip-icon">💡</span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="loading-advice">
              <p>Loading your personalized advice...</p>
            </div>
          )}
        </div>

        {/* Chat with Coach */}
        <div className="coach-chat-card">
          <h2>Ask Your Coach</h2>
          <div className="chat-container">
            <div className="chat-messages">
              {chatHistory.length === 0 ? (
                <div className="welcome-message">
                  <p>👋 Hi! I'm your AI health coach. Ask me anything about:</p>
                  <ul>
                    <li>Nutrition and meal planning</li>
                    <li>Exercise recommendations</li>
                    <li>Weight management</li>
                    <li>Heart rate and fitness</li>
                    <li>General health tips</li>
                  </ul>
                </div>
              ) : (
                chatHistory.map((chat, index) => (
                  <div key={index} className="chat-message">
                    <div className="user-question">
                      <strong>You:</strong> {chat.question}
                    </div>
                    <div className="coach-answer">
                      <strong>Coach:</strong> {chat.answer}
                    </div>
                  </div>
                ))
              )}
              {loading && (
                <div className="loading-message">
                  <p>Coach is thinking...</p>
                </div>
              )}
            </div>
            
            <form onSubmit={askCoach} className="chat-input-form">
              <input
                type="text"
                value={userQuestion}
                onChange={(e) => setUserQuestion(e.target.value)}
                placeholder="Ask your coach anything..."
                disabled={loading}
                className="chat-input"
              />
              <button type="submit" disabled={loading || !userQuestion.trim()} className="send-btn">
                {loading ? 'Sending...' : 'Send'}
              </button>
            </form>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="quick-actions-card">
          <h2>Quick Actions</h2>
          <div className="quick-actions">
            <button 
              className="quick-action-btn"
              onClick={() => setUserQuestion("What should I eat today?")}
            >
              🍽️ Meal Suggestions
            </button>
            <button 
              className="quick-action-btn"
              onClick={() => setUserQuestion("How can I improve my workout?")}
            >
              💪 Workout Tips
            </button>
            <button 
              className="quick-action-btn"
              onClick={() => setUserQuestion("How can I stay motivated?")}
            >
              🎯 Motivation
            </button>
            <button 
              className="quick-action-btn"
              onClick={() => setUserQuestion("What's a good heart rate range for exercise?")}
            >
              ❤️ Heart Rate Guide
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Coach; 