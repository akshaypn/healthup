import React, { useState, useEffect } from 'react';
import { Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import './FoodLog.css';

interface FoodEntry {
  id: number;
  description: string;
  calories: number | null;
  protein_g: number | null;
  fat_g: number | null;
  carbs_g: number | null;
  fiber_g: number | null;
  sugar_g: number | null;
  serving_size: string | null;
  meal_type: string | null;
  confidence_score: number | null;
  source: string | null;
  logged_at: string;
  // Vitamins
  vitamin_a_mcg?: number | null;
  vitamin_c_mg?: number | null;
  vitamin_d_mcg?: number | null;
  vitamin_e_mg?: number | null;
  vitamin_k_mcg?: number | null;
  vitamin_b1_mg?: number | null;
  vitamin_b2_mg?: number | null;
  vitamin_b3_mg?: number | null;
  vitamin_b5_mg?: number | null;
  vitamin_b6_mg?: number | null;
  vitamin_b7_mcg?: number | null;
  vitamin_b9_mcg?: number | null;
  vitamin_b12_mcg?: number | null;
  // Minerals
  calcium_mg?: number | null;
  iron_mg?: number | null;
  magnesium_mg?: number | null;
  phosphorus_mg?: number | null;
  potassium_mg?: number | null;
  sodium_mg?: number | null;
  zinc_mg?: number | null;
  copper_mg?: number | null;
  manganese_mg?: number | null;
  selenium_mcg?: number | null;
  chromium_mcg?: number | null;
  molybdenum_mcg?: number | null;
  // Other nutrients
  cholesterol_mg?: number | null;
  saturated_fat_g?: number | null;
  trans_fat_g?: number | null;
  polyunsaturated_fat_g?: number | null;
  monounsaturated_fat_g?: number | null;
}

interface ParsedFoodItem {
  description: string;
  serving_size?: string;
  meal_type?: string;
  confidence_score: number;
  nutritional_data: any;
}

interface FoodParsingResponse {
  session_id: string;
  status: string;
  parsed_foods: ParsedFoodItem[];
  extracted_datetime?: string;
  confidence_score: number;
  error_message?: string;
  meal_analysis?: any;
}

interface AgentStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  details?: string;
  error?: string;
  model_used?: string;
  duration?: number;
  start_time?: number;
}

const FoodLog: React.FC = () => {
  const [formData, setFormData] = useState({
    description: '',
    calories: '',
    protein_g: '',
    fat_g: '',
    carbs_g: '',
    fiber_g: '',
    sugar_g: '',
    serving_size: '',
    meal_type: ''
  });
  
  const [aiInput, setAiInput] = useState('');
  const [foodHistory, setFoodHistory] = useState<FoodEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [parsedFoods, setParsedFoods] = useState<ParsedFoodItem[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [showAiResults, setShowAiResults] = useState(false);
  const [editingFood, setEditingFood] = useState<FoodEntry | null>(null);
  const [showDetailedView, setShowDetailedView] = useState<number | null>(null);
  const [mealAnalysis, setMealAnalysis] = useState<any>(null);
  
  // Agent progress tracking
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([
    {
      id: 'extract-dishes',
      name: 'Extracting Dishes',
      description: 'Identifying food items from your description',
      status: 'pending'
    },
    {
      id: 'search-nutrition',
      name: 'Searching Nutrition Data',
      description: 'Finding nutritional information for each dish',
      status: 'pending'
    },
    {
      id: 'analyze-meal',
      name: 'Analyzing Meal',
      description: 'Generating comprehensive meal analysis',
      status: 'pending'
    },
    {
      id: 'create-logs',
      name: 'Creating Food Logs',
      description: 'Saving parsed data to your food diary',
      status: 'pending'
    }
  ]);
  
  // Enhanced error state
  const [detailedError, setDetailedError] = useState<{
    title: string;
    message: string;
    suggestions: string[];
    technical_details?: string;
  } | null>(null);

  useEffect(() => {
    fetchFoodHistory();
  }, []);

  const resetAgentSteps = () => {
    setAgentSteps(agentSteps.map(step => ({ ...step, status: 'pending', details: undefined, error: undefined })));
  };

  const updateAgentStep = (stepId: string, updates: Partial<AgentStep>) => {
    setAgentSteps(prev => prev.map(step => {
      if (step.id === stepId) {
        const updatedStep = { ...step, ...updates };
        
        // Track timing
        if (updates.status === 'running' && !step.start_time) {
          updatedStep.start_time = Date.now();
        } else if ((updates.status === 'completed' || updates.status === 'failed') && step.start_time) {
          updatedStep.duration = Date.now() - step.start_time;
        }
        
        return updatedStep;
      }
      return step;
    }));
  };

  const fetchFoodHistory = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/food/history`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        const logs = Array.isArray(data.logs) ? data.logs : [];
        setFoodHistory(logs);
      }
    } catch (error) {
      console.error('Failed to fetch food history:', error);
      setFoodHistory([]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/food`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          description: formData.description,
          calories: parseInt(formData.calories) || null,
          protein_g: parseFloat(formData.protein_g) || null,
          fat_g: parseFloat(formData.fat_g) || null,
          carbs_g: parseFloat(formData.carbs_g) || null,
          fiber_g: parseFloat(formData.fiber_g) || null,
          sugar_g: parseFloat(formData.sugar_g) || null,
          serving_size: formData.serving_size || null,
          meal_type: formData.meal_type || null
        })
      });

      if (response.ok) {
        setMessage('Food logged successfully!');
        setFormData({
          description: '',
          calories: '',
          protein_g: '',
          fat_g: '',
          carbs_g: '',
          fiber_g: '',
          sugar_g: '',
          serving_size: '',
          meal_type: ''
        });
        fetchFoodHistory();
      } else {
        const errorData = await response.json();
        setMessage(`Failed to log food: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      setMessage('Failed to log food. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAiParse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiInput.trim()) return;

    setAiLoading(true);
    setMessage('');
    setDetailedError(null);
    resetAgentSteps();
    setShowAiResults(false);
    setParsedFoods([]);
    setMealAnalysis(null);

    try {
      // Step 1: Extract dishes
      updateAgentStep('extract-dishes', { 
        status: 'running', 
        details: 'Processing your input...' 
      });
      
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/food/parse`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_input: aiInput,
          extract_datetime: true
        })
      });

      if (response.ok) {
        const data: FoodParsingResponse = await response.json();
        
        if (data.status === 'completed') {
          // Update steps to show completion with timing
          updateAgentStep('extract-dishes', { 
            status: 'completed', 
            details: `Found ${data.parsed_foods.length} food items` 
          });
          updateAgentStep('search-nutrition', { 
            status: 'completed', 
            details: 'Nutritional data retrieved successfully' 
          });
          updateAgentStep('analyze-meal', { 
            status: 'completed', 
            details: 'Meal analysis generated' 
          });

          setParsedFoods(data.parsed_foods);
          setCurrentSessionId(data.session_id);
          setMealAnalysis(data.meal_analysis);
          setShowAiResults(true);
          setMessage(`✅ AI successfully parsed ${data.parsed_foods.length} food items with ${Math.round(data.confidence_score * 100)}% confidence`);
        } else {
          // Handle parsing failure with detailed error
          updateAgentStep('extract-dishes', { 
            status: 'failed', 
            error: data.error_message || 'Failed to extract dishes' 
          });
          
          setDetailedError({
            title: 'AI Parsing Failed',
            message: data.error_message || 'The AI was unable to process your food description.',
            suggestions: [
              'Try rephrasing your description with more specific details',
              'Include quantities (e.g., "100g chicken breast")',
              'Separate multiple foods with commas or "and"',
              'Check that your description contains actual food items'
            ],
            technical_details: data.error_message
          });
        }
      } else {
        const errorData = await response.json();
        updateAgentStep('extract-dishes', { 
          status: 'failed', 
          error: errorData.detail || 'Request failed' 
        });
        
        // Parse error response for better user experience
        const errorInfo = parseErrorResponse(errorData);
        setDetailedError(errorInfo);
      }
    } catch (error) {
      updateAgentStep('extract-dishes', { 
        status: 'failed', 
        error: 'Network error or server unavailable' 
      });
      
      setDetailedError({
        title: 'Connection Error',
        message: 'Unable to connect to the AI service.',
        suggestions: [
          'Check your internet connection',
          'Try again in a few moments',
          'Contact support if the problem persists'
        ],
        technical_details: error instanceof Error ? error.message : 'Unknown network error'
      });
    } finally {
      setAiLoading(false);
    }
  };

  const handleCreateLogsFromAi = async () => {
    if (!currentSessionId) return;

    setLoading(true);
    updateAgentStep('create-logs', { status: 'running', details: 'Saving to your food diary...' });

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/food/parse/${currentSessionId}/create-logs`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        updateAgentStep('create-logs', { 
          status: 'completed', 
          details: `Created ${data.food_logs.length} food logs` 
        });
        setMessage(`✅ Successfully created ${data.food_logs.length} food logs!`);
        setShowAiResults(false);
        setParsedFoods([]);
        setCurrentSessionId(null);
        setAiInput('');
        fetchFoodHistory();
        
        // Reset after a delay
        setTimeout(() => {
          resetAgentSteps();
        }, 3000);
      } else {
        const errorData = await response.json();
        updateAgentStep('create-logs', { 
          status: 'failed', 
          error: errorData.detail || 'Failed to create logs' 
        });
        setMessage(`❌ Failed to create food logs: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      updateAgentStep('create-logs', { 
        status: 'failed', 
        error: 'Network error or server unavailable' 
      });
      setMessage('❌ Failed to create food logs. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateFood = async (foodId: number, updates: Partial<FoodEntry>) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/food/${foodId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updates)
      });

      if (response.ok) {
        setMessage('✅ Food log updated successfully!');
        setEditingFood(null);
        fetchFoodHistory();
      } else {
        const errorData = await response.json();
        setMessage(`❌ Failed to update food log: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      setMessage('❌ Failed to update food log. Please try again.');
    }
  };

  const handleDeleteFood = async (foodId: number) => {
    if (!confirm('Are you sure you want to delete this food log?')) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/food/${foodId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setMessage('✅ Food log deleted successfully!');
        fetchFoodHistory();
      } else {
        const errorData = await response.json();
        setMessage(`❌ Failed to delete food log: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      setMessage('❌ Failed to delete food log. Please try again.');
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const todayEntries = (foodHistory || []).filter(entry => 
    new Date(entry.logged_at).toDateString() === new Date().toDateString()
  );

  const todayTotals = todayEntries.reduce((acc, entry) => ({
    calories: acc.calories + (entry.calories || 0),
    protein: acc.protein + (entry.protein_g || 0),
    fat: acc.fat + (entry.fat_g || 0),
    carbs: acc.carbs + (entry.carbs_g || 0),
    fiber: acc.fiber + (entry.fiber_g || 0),
    sugar: acc.sugar + (entry.sugar_g || 0)
  }), { calories: 0, protein: 0, fat: 0, carbs: 0, fiber: 0, sugar: 0 });

  const pieData = [
    { name: 'Protein', value: todayTotals.protein, color: '#8884d8' },
    { name: 'Fat', value: todayTotals.fat, color: '#82ca9d' },
    { name: 'Carbs', value: todayTotals.carbs, color: '#ffc658' }
  ];

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅';
      case 'running': return '🔄';
      case 'failed': return '❌';
      default: return '⏳';
    }
  };

  const getStepClass = (status: string) => {
    switch (status) {
      case 'completed': return 'step-completed';
      case 'running': return 'step-running';
      case 'failed': return 'step-failed';
      default: return 'step-pending';
    }
  };

  const parseErrorResponse = (errorData: any) => {
    // Parse different types of error responses
    if (errorData.detail) {
      const detail = errorData.detail;
      
      // Check for specific error types
      if (detail.includes('rate limit') || detail.includes('quota')) {
        return {
          title: 'Rate Limit Exceeded',
          message: 'The AI service is temporarily busy. Please try again in a moment.',
          suggestions: [
            'Wait 1-2 minutes before trying again',
            'Try with a shorter food description',
            'Use manual entry for now'
          ],
          technical_details: detail
        };
      } else if (detail.includes('model') || detail.includes('API')) {
        return {
          title: 'AI Service Error',
          message: 'The AI service encountered an error while processing your request.',
          suggestions: [
            'Try rephrasing your food description',
            'Check that your input contains valid food items',
            'Try again in a few moments'
          ],
          technical_details: detail
        };
      } else if (detail.includes('validation') || detail.includes('invalid')) {
        return {
          title: 'Invalid Input',
          message: 'The food description could not be processed.',
          suggestions: [
            'Use clear, specific food descriptions',
            'Include quantities when possible',
            'Avoid special characters or unusual formatting'
          ],
          technical_details: detail
        };
      } else {
        return {
          title: 'Processing Error',
          message: detail,
          suggestions: [
            'Try rephrasing your description',
            'Check your internet connection',
            'Try again in a few moments'
          ],
          technical_details: detail
        };
      }
    }
    
    // Default error response
    return {
      title: 'Unknown Error',
      message: 'An unexpected error occurred.',
      suggestions: [
        'Try again in a few moments',
        'Check your internet connection',
        'Contact support if the problem persists'
      ],
      technical_details: JSON.stringify(errorData)
    };
  };

  return (
    <div className="food-log">
      <h1>🤖 AI-Powered Food Tracking</h1>
      
      <div className="food-container">
        {/* AI Food Input */}
        <div className="food-ai-card">
          <h2>✨ Smart Food Parser</h2>
          <p className="ai-description">
            Describe what you ate in natural language. Our AI agent will extract nutritional data and create detailed food logs automatically.
          </p>
          
          <form onSubmit={handleAiParse} className="ai-form">
            <div className="form-group">
              <label htmlFor="aiInput">What did you eat?</label>
              <textarea
                id="aiInput"
                value={aiInput}
                onChange={(e) => setAiInput(e.target.value)}
                placeholder="e.g., I had 80g of protein oats with 250ml milk and a small banana at 1pm today"
                disabled={aiLoading}
                className="ai-input"
              />
            </div>
            <button type="submit" disabled={aiLoading || !aiInput.trim()} className="ai-submit-btn">
              {aiLoading ? '🤖 AI is analyzing...' : '🚀 Parse with AI'}
            </button>
          </form>

          {/* Enhanced Agent Progress */}
          {aiLoading && (
            <div className="agent-progress">
              <h3>🤖 AI Agent Progress</h3>
              <div className="progress-summary">
                <div className="progress-stats">
                  <span className="stat">
                    <span className="stat-label">Completed:</span>
                    <span className="stat-value">
                      {agentSteps.filter(s => s.status === 'completed').length}/{agentSteps.length}
                    </span>
                  </span>
                  <span className="stat">
                    <span className="stat-label">Current:</span>
                    <span className="stat-value">
                      {agentSteps.find(s => s.status === 'running')?.name || 'Waiting...'}
                    </span>
                  </span>
                </div>
              </div>
              <div className="steps-container">
                {agentSteps.map((step) => (
                  <div key={step.id} className={`step ${getStepClass(step.status)}`}>
                    <div className="step-header">
                      <span className="step-icon">{getStepIcon(step.status)}</span>
                      <div className="step-info">
                        <span className="step-name">{step.name}</span>
                        {step.duration && (
                          <span className="step-duration">
                            ({Math.round(step.duration / 1000)}s)
                          </span>
                        )}
                      </div>
                      {step.model_used && (
                        <span className="step-model">{step.model_used}</span>
                      )}
                    </div>
                    <div className="step-description">{step.description}</div>
                    {step.details && (
                      <div className="step-details">
                        <span className="details-icon">📋</span>
                        {step.details}
                      </div>
                    )}
                    {step.error && (
                      <div className="step-error">
                        <span className="error-icon">⚠️</span>
                        <span className="error-text">{step.error}</span>
                      </div>
                    )}
                    {step.status === 'running' && (
                      <div className="step-loading">
                        <div className="loading-dots">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Enhanced Error Display */}
          {detailedError && (
            <div className="error-message">
              <div className="error-header">
                <h3>⚠️ {detailedError.title}</h3>
                <button 
                  onClick={() => setDetailedError(null)}
                  className="error-close-btn"
                >
                  ✕
                </button>
              </div>
              <div className="error-content">
                <p className="error-description">{detailedError.message}</p>
                
                <div className="error-suggestions">
                  <h4>💡 Suggestions:</h4>
                  <ul>
                    {detailedError.suggestions.map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
                
                {detailedError.technical_details && (
                  <details className="technical-details">
                    <summary>🔧 Technical Details</summary>
                    <pre className="error-details">{detailedError.technical_details}</pre>
                  </details>
                )}
              </div>
            </div>
          )}

          {/* Success Message */}
          {message && message.includes('✅') && (
            <div className="success-message">
              <p>{message}</p>
            </div>
          )}

          {/* AI Results */}
          {showAiResults && parsedFoods.length > 0 && (
            <div className="ai-results">
              <h3>🎯 AI Analysis Results</h3>
              
              {/* Meal Analysis */}
              {mealAnalysis && (
                <div className="meal-analysis">
                  <h4>📊 Meal Overview</h4>
                  <div className="analysis-grid">
                    {mealAnalysis.overall_health_score && (
                      <div className="analysis-item">
                        <span className="label">Health Score:</span>
                        <span className="value">{mealAnalysis.overall_health_score}/10</span>
                      </div>
                    )}
                    {mealAnalysis.protein_adequacy && (
                      <div className="analysis-item">
                        <span className="label">Protein:</span>
                        <span className="value">{mealAnalysis.protein_adequacy}</span>
                      </div>
                    )}
                    {mealAnalysis.fiber_content && (
                      <div className="analysis-item">
                        <span className="label">Fiber:</span>
                        <span className="value">{mealAnalysis.fiber_content}</span>
                      </div>
                    )}
                    {mealAnalysis.recommendations && mealAnalysis.recommendations.length > 0 && (
                      <div className="analysis-item full-width">
                        <span className="label">Recommendations:</span>
                        <ul className="recommendations">
                          {mealAnalysis.recommendations.map((rec: string, index: number) => (
                            <li key={index}>{rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Parsed Foods */}
              <div className="parsed-foods">
                <h4>🍽️ Detected Foods</h4>
                <div className="foods-grid">
                  {parsedFoods.map((food, index) => (
                    <div key={index} className="parsed-food-item">
                      <div className="food-header">
                        <h5>{food.description}</h5>
                        <span className="confidence">
                          {Math.round(food.confidence_score * 100)}% confidence
                        </span>
                      </div>
                      {food.serving_size && (
                        <p className="serving-size">Serving: {food.serving_size}</p>
                      )}
                      {food.meal_type && (
                        <p className="meal-type">Meal: {food.meal_type}</p>
                      )}
                      <div className="nutrition-preview">
                        {food.nutritional_data.calories_kcal && (
                          <span className="nutrition-item">
                            {Math.round(food.nutritional_data.calories_kcal)} kcal
                          </span>
                        )}
                        {food.nutritional_data.protein_g && (
                          <span className="nutrition-item">
                            {food.nutritional_data.protein_g}g protein
                          </span>
                        )}
                        {food.nutritional_data.carbs_g && (
                          <span className="nutrition-item">
                            {food.nutritional_data.carbs_g}g carbs
                          </span>
                        )}
                        {food.nutritional_data.fat_g && (
                          <span className="nutrition-item">
                            {food.nutritional_data.fat_g}g fat
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <button 
                onClick={handleCreateLogsFromAi} 
                disabled={loading}
                className="create-logs-btn"
              >
                {loading ? '📝 Creating logs...' : '💾 Save to Food Diary'}
              </button>
            </div>
          )}
        </div>

        {/* Manual Food Input */}
        <div className="food-manual-card">
          <h2>✏️ Manual Entry</h2>
          <p>Or enter food details manually</p>
          <form onSubmit={handleSubmit} className="manual-form">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="description">Food Description</label>
                <input
                  type="text"
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="serving_size">Serving Size</label>
                <input
                  type="text"
                  id="serving_size"
                  name="serving_size"
                  value={formData.serving_size}
                  onChange={handleInputChange}
                  placeholder="e.g., 100g"
                />
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="calories">Calories</label>
                <input
                  type="number"
                  id="calories"
                  name="calories"
                  value={formData.calories}
                  onChange={handleInputChange}
                />
              </div>
              <div className="form-group">
                <label htmlFor="protein_g">Protein (g)</label>
                <input
                  type="number"
                  step="0.1"
                  id="protein_g"
                  name="protein_g"
                  value={formData.protein_g}
                  onChange={handleInputChange}
                />
              </div>
              <div className="form-group">
                <label htmlFor="fat_g">Fat (g)</label>
                <input
                  type="number"
                  step="0.1"
                  id="fat_g"
                  name="fat_g"
                  value={formData.fat_g}
                  onChange={handleInputChange}
                />
              </div>
              <div className="form-group">
                <label htmlFor="carbs_g">Carbs (g)</label>
                <input
                  type="number"
                  step="0.1"
                  id="carbs_g"
                  name="carbs_g"
                  value={formData.carbs_g}
                  onChange={handleInputChange}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="fiber_g">Fiber (g)</label>
                <input
                  type="number"
                  step="0.1"
                  id="fiber_g"
                  name="fiber_g"
                  value={formData.fiber_g}
                  onChange={handleInputChange}
                />
              </div>
              <div className="form-group">
                <label htmlFor="sugar_g">Sugar (g)</label>
                <input
                  type="number"
                  step="0.1"
                  id="sugar_g"
                  name="sugar_g"
                  value={formData.sugar_g}
                  onChange={handleInputChange}
                />
              </div>
              <div className="form-group">
                <label htmlFor="meal_type">Meal Type</label>
                <select
                  id="meal_type"
                  name="meal_type"
                  value={formData.meal_type}
                  onChange={handleInputChange}
                >
                  <option value="">Select meal type</option>
                  <option value="Breakfast">Breakfast</option>
                  <option value="Lunch">Lunch</option>
                  <option value="Dinner">Dinner</option>
                  <option value="Snack">Snack</option>
                </select>
              </div>
            </div>

            <button type="submit" disabled={loading} className="manual-submit-btn">
              {loading ? 'Saving...' : 'Save Food Entry'}
            </button>
          </form>
        </div>
      </div>

      {/* Today's Summary */}
      <div className="today-summary">
        <h2>📊 Today's Nutrition Summary</h2>
        <div className="summary-grid">
          <div className="summary-card">
            <h3>Total Calories</h3>
            <p className="summary-value">{Math.round(todayTotals.calories)}</p>
            <p className="summary-unit">kcal</p>
          </div>
          <div className="summary-card">
            <h3>Protein</h3>
            <p className="summary-value">{Math.round(todayTotals.protein)}</p>
            <p className="summary-unit">g</p>
          </div>
          <div className="summary-card">
            <h3>Fat</h3>
            <p className="summary-value">{Math.round(todayTotals.fat)}</p>
            <p className="summary-unit">g</p>
          </div>
          <div className="summary-card">
            <h3>Carbs</h3>
            <p className="summary-value">{Math.round(todayTotals.carbs)}</p>
            <p className="summary-unit">g</p>
          </div>
          <div className="summary-card">
            <h3>Fiber</h3>
            <p className="summary-value">{Math.round(todayTotals.fiber)}</p>
            <p className="summary-unit">g</p>
          </div>
          <div className="summary-card">
            <h3>Food Items</h3>
            <p className="summary-value">{todayEntries.length}</p>
            <p className="summary-unit">entries</p>
          </div>
        </div>

        {/* Charts */}
        <div className="charts-container">
          <div className="chart-card">
            <h3>Macronutrient Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
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
      </div>

      {/* Food History */}
      <div className="food-history">
        <h2>📝 Recent Food Entries</h2>
        {foodHistory.length === 0 ? (
          <div className="empty-state">
            <p>No food entries yet. Start by logging your first meal!</p>
          </div>
        ) : (
          <div className="history-list">
            {foodHistory.slice(0, 10).map((entry) => (
              <div key={entry.id} className="history-item">
                <div className="history-header">
                  <h4>{entry.description}</h4>
                  <div className="history-actions">
                    <button
                      onClick={() => setShowDetailedView(showDetailedView === entry.id ? null : entry.id)}
                      className="detail-btn"
                    >
                      {showDetailedView === entry.id ? 'Hide' : 'Details'}
                    </button>
                    <button
                      onClick={() => setEditingFood(editingFood?.id === entry.id ? null : entry)}
                      className="edit-btn"
                    >
                      {editingFood?.id === entry.id ? 'Cancel' : 'Edit'}
                    </button>
                    <button
                      onClick={() => handleDeleteFood(entry.id)}
                      className="delete-btn"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                
                <div className="history-summary">
                  <span className="calories">{entry.calories || 0} kcal</span>
                  <span className="protein">{entry.protein_g || 0}g protein</span>
                  <span className="carbs">{entry.carbs_g || 0}g carbs</span>
                  <span className="fat">{entry.fat_g || 0}g fat</span>
                  {entry.meal_type && <span className="meal-type">{entry.meal_type}</span>}
                  <span className="date">
                    {new Date(entry.logged_at).toLocaleDateString()}
                  </span>
                </div>

                {showDetailedView === entry.id && (
                  <div className="detailed-view">
                    <h5>Detailed Nutrition</h5>
                    <div className="nutrition-details">
                      <div className="nutrition-row">
                        <span>Fiber:</span>
                        <span>{entry.fiber_g || 0}g</span>
                      </div>
                      <div className="nutrition-row">
                        <span>Sugar:</span>
                        <span>{entry.sugar_g || 0}g</span>
                      </div>
                      <div className="nutrition-row">
                        <span>Serving Size:</span>
                        <span>{entry.serving_size || 'Not specified'}</span>
                      </div>
                      <div className="nutrition-row">
                        <span>Source:</span>
                        <span>{entry.source || 'Manual entry'}</span>
                      </div>
                      {entry.confidence_score && (
                        <div className="nutrition-row">
                          <span>AI Confidence:</span>
                          <span>{Math.round(entry.confidence_score * 100)}%</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {editingFood?.id === entry.id && (
                  <div className="edit-form">
                    <div className="edit-row">
                      <input
                        type="text"
                        value={editingFood.description}
                        onChange={(e) => setEditingFood({...editingFood, description: e.target.value})}
                        placeholder="Description"
                      />
                      <input
                        type="number"
                        value={editingFood.calories || ''}
                        onChange={(e) => setEditingFood({...editingFood, calories: parseInt(e.target.value) || null})}
                        placeholder="Calories"
                      />
                      <input
                        type="number"
                        step="0.1"
                        value={editingFood.protein_g || ''}
                        onChange={(e) => setEditingFood({...editingFood, protein_g: parseFloat(e.target.value) || null})}
                        placeholder="Protein (g)"
                      />
                    </div>
                    <div className="edit-actions">
                      <button
                        onClick={() => handleUpdateFood(entry.id, editingFood)}
                        className="save-btn"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingFood(null)}
                        className="cancel-btn"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default FoodLog; 