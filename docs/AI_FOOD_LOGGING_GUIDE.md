# AI-Powered Food Logging System

## Overview

HealthUp now features an advanced AI-powered food logging system that allows users to describe their meals in natural language. The AI automatically extracts nutritional data, serving sizes, meal types, and timing information, then creates comprehensive food logs with micronutrients and vitamins.

## Features

### 🤖 AI Food Parser
- **Natural Language Input**: Describe meals in plain English
- **Automatic Nutrition Extraction**: AI fetches nutritional data from Google search
- **Smart Parsing**: Extracts serving sizes, meal types, and timing
- **Comprehensive Data**: Includes macronutrients, vitamins, and minerals
- **Confidence Scoring**: Shows AI confidence in extracted data

### 📊 Enhanced Nutritional Tracking
- **Macronutrients**: Calories, protein, fat, carbs, fiber, sugar
- **Vitamins**: A, C, D, E, K, B-complex vitamins
- **Minerals**: Calcium, iron, magnesium, zinc, and more
- **Fat Types**: Saturated, trans, polyunsaturated, monounsaturated
- **Cholesterol**: Total cholesterol tracking

### 🔄 CRUD Operations
- **Create**: AI-parsed or manual food logs
- **Read**: View detailed nutrition information
- **Update**: Edit any food log entry
- **Delete**: Remove unwanted entries

### 📱 Mobile-First Design
- **Responsive Interface**: Works on all devices
- **Touch-Friendly**: Optimized for mobile use
- **Offline Support**: PWA capabilities

## Architecture

### MCP Server Integration
The system uses Model Context Protocol (MCP) servers for AI-powered food parsing:

```
┌─────────────┐    HTTP/JSON    ┌─────────────┐
│   Frontend  │◄──────────────►│  MCP Server │
│  (React)    │                 │  (FastAPI)  │
└─────────────┘                 └─────────────┘
       │                               │
       │                               │
       ▼                               ▼
┌─────────────┐                 ┌─────────────┐
│   Backend   │                 │ Google APIs │
│  (FastAPI)  │                 │ Nutrition DB│
└─────────────┘                 └─────────────┘
       │
       ▼
┌─────────────┐
│ PostgreSQL  │
│   Database  │
└─────────────┘
```

### Data Flow
1. **User Input**: Natural language description of food
2. **AI Parsing**: MCP server extracts food items and metadata
3. **Nutrition Search**: Google search for current nutritional data
4. **Data Extraction**: AI extracts structured nutrition information
5. **Database Storage**: Comprehensive food log with all nutrients
6. **User Review**: User can edit, delete, or approve AI suggestions

## Setup Instructions

### 1. Backend Configuration

Update your `backend/.env` file:

```env
# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8001
MCP_API_KEY=your-mcp-api-key-here
MCP_TIMEOUT=30
```

### 2. Run Database Migrations

```bash
# Apply the new database schema
docker compose exec backend alembic upgrade head
```

### 3. Start MCP Server (Optional)

For testing, you can run the example MCP server:

```bash
cd backend
python mcp_server_example.py
```

This will start a mock MCP server on `http://localhost:8001` with sample nutrition data.

### 4. Deploy Application

```bash
# Start all services
docker compose up -d

# Check logs
docker compose logs -f backend
```

## Usage Guide

### AI Food Parsing

1. **Navigate to Food Logging**: Go to the Food Tracking page
2. **Use AI Parser**: Click on the "🤖 AI Food Parser" section
3. **Describe Your Meal**: Enter natural language description
   ```
   Example: "I had 2 cups of oatmeal with 1 banana and 1 tbsp honey for breakfast at 8am"
   ```
4. **Review AI Results**: Check the parsed food items and confidence scores
5. **Create Food Logs**: Click "✅ Create Food Logs" to save to database

### Manual Food Entry

1. **Use Manual Form**: Scroll to "📝 Manual Food Entry" section
2. **Fill Details**: Enter food description, serving size, and meal type
3. **Add Nutrition**: Input macronutrients and micronutrients
4. **Save Entry**: Click "Log Food" to save

### Managing Food Logs

1. **View Today's Meals**: See all logged meals for the day
2. **Detailed View**: Click "Details" to see comprehensive nutrition
3. **Edit Entries**: Click "Edit" to modify any food log
4. **Delete Entries**: Click "Delete" to remove unwanted logs

## API Endpoints

### Food Parsing
- `POST /food/parse` - Parse natural language food input
- `POST /food/parse/{session_id}/create-logs` - Create food logs from parsing session
- `GET /food/parse/sessions` - Get user's parsing sessions
- `GET /food/parse/sessions/{session_id}` - Get specific parsing session

### Food Management
- `POST /food` - Create food log
- `GET /food/history` - Get all food logs
- `GET /food/today` - Get today's food logs
- `PUT /food/{food_id}` - Update food log
- `DELETE /food/{food_id}` - Delete food log
- `GET /food/nutrition-summary` - Get nutrition summary

## MCP Server Implementation

### Required Tools

Your MCP server should implement these tools:

#### 1. Google Search Tool
```json
{
  "tool_name": "google_search",
  "parameters": {
    "query": "oatmeal nutrition facts",
    "num_results": 5
  }
}
```

#### 2. Nutrition Extraction Tool
```json
{
  "tool_name": "extract_nutrition",
  "parameters": {
    "food_item": "oatmeal",
    "serving_size": "1 cup",
    "search_results": [...],
    "extract_micronutrients": true
  }
}
```

#### 3. Food Input Parsing Tool
```json
{
  "tool_name": "parse_food_input",
  "parameters": {
    "user_input": "I had oatmeal for breakfast",
    "extract_datetime": true,
    "extract_serving_sizes": true,
    "extract_meal_types": true
  }
}
```

### Example MCP Server

See `backend/mcp_server_example.py` for a complete implementation.

## Database Schema

### Enhanced FoodLog Table

```sql
CREATE TABLE food_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    description TEXT,
    
    -- Macronutrients
    calories INTEGER,
    protein_g NUMERIC(6,2),
    fat_g NUMERIC(6,2),
    carbs_g NUMERIC(6,2),
    fiber_g NUMERIC(6,2),
    sugar_g NUMERIC(6,2),
    
    -- Vitamins
    vitamin_a_mcg NUMERIC(8,2),
    vitamin_c_mg NUMERIC(8,2),
    vitamin_d_mcg NUMERIC(8,2),
    -- ... more vitamins
    
    -- Minerals
    calcium_mg NUMERIC(8,2),
    iron_mg NUMERIC(8,2),
    magnesium_mg NUMERIC(8,2),
    -- ... more minerals
    
    -- Metadata
    serving_size VARCHAR,
    meal_type VARCHAR,
    confidence_score NUMERIC(3,2),
    source VARCHAR,
    search_queries JSONB,
    logged_at TIMESTAMP WITH TIME ZONE
);
```

### FoodParsingSession Table

```sql
CREATE TABLE food_parsing_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    session_id VARCHAR UNIQUE NOT NULL,
    user_input TEXT NOT NULL,
    parsed_foods JSONB,
    extracted_datetime TIMESTAMP WITH TIME ZONE,
    confidence_score NUMERIC(3,2),
    status VARCHAR,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);
```

## Testing

### Test AI Parsing

1. Start the example MCP server:
   ```bash
   cd backend
   python mcp_server_example.py
   ```

2. Update your backend environment:
   ```env
   MCP_SERVER_URL=http://localhost:8001
   ```

3. Test with sample inputs:
   - "I had oatmeal with banana for breakfast"
   - "2 cups of rice with chicken breast for lunch"
   - "Apple as a snack"

### Test API Endpoints

```bash
# Parse food input
curl -X POST "http://localhost:8000/food/parse" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_input": "oatmeal with banana for breakfast"}'

# Create food logs from session
curl -X POST "http://localhost:8000/food/parse/SESSION_ID/create-logs" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### Common Issues

1. **MCP Server Connection Failed**
   - Check if MCP server is running
   - Verify URL in environment variables
   - Check network connectivity

2. **AI Parsing Returns No Results**
   - Ensure MCP server implements required tools
   - Check server logs for errors
   - Verify input format

3. **Database Migration Errors**
   - Run `alembic upgrade head` inside container
   - Check database connection
   - Verify schema changes

### Debug Mode

Enable debug logging in your backend:

```env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

## Production Deployment

### MCP Server Requirements

For production, your MCP server should:

1. **Use Real Google Search API**: Replace mock search with actual Google Search API
2. **Implement Rate Limiting**: Respect API quotas and limits
3. **Add Authentication**: Secure your MCP server endpoints
4. **Use Production Nutrition DB**: Connect to USDA or similar nutrition database
5. **Add Caching**: Cache frequently requested nutrition data
6. **Monitor Performance**: Track response times and success rates

### Security Considerations

1. **API Key Management**: Store MCP API keys securely
2. **Input Validation**: Validate all user inputs
3. **Rate Limiting**: Implement rate limiting on food parsing endpoints
4. **Data Privacy**: Ensure nutrition data is handled securely

## Future Enhancements

### Planned Features

1. **Image Recognition**: Upload food photos for automatic identification
2. **Barcode Scanning**: Scan product barcodes for instant nutrition data
3. **Recipe Parsing**: Parse recipe ingredients automatically
4. **Meal Planning**: AI-powered meal suggestions
5. **Nutritional Goals**: Track progress toward nutritional targets
6. **Social Features**: Share meals and nutrition insights

### Advanced AI Features

1. **Multi-language Support**: Parse food descriptions in multiple languages
2. **Regional Cuisine**: Support for regional and ethnic foods
3. **Allergy Detection**: Identify potential allergens in meals
4. **Dietary Restrictions**: Respect vegetarian, vegan, gluten-free preferences
5. **Portion Estimation**: AI-powered portion size estimation

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review server logs for error messages
3. Test with the example MCP server
4. Verify database migrations are applied
5. Check API documentation at `/docs`

## Contributing

To contribute to the AI food logging system:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

---

**Note**: This system is designed to work with any MCP-compatible server. The example server provided is for testing purposes only. For production use, implement a robust MCP server with real nutrition data sources. 