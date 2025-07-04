# Amazfit Integration Guide

This guide explains how to use the Amazfit integration with your HealthUp backend.

## Overview

The Amazfit integration allows you to:
- Sync activity data (steps, calories, distance)
- Sync heart rate data
- Sync sleep data
- Store data in your local database
- Access data through REST API endpoints

## Prerequisites

1. **Amazfit Device**: You need an Amazfit smartwatch/band
2. **Zepp App**: Install the Zepp app and pair your device
3. **Valid Credentials**: You need a valid `app_token` and `user_id` from the Amazfit API

## Getting Credentials

### Method 1: Extract from Zepp App (Recommended)
1. Install Zepp app and pair your device
2. Use a tool like [huami-token](https://github.com/argrento/huami-token) to extract credentials
3. Or use HTTP proxy to capture the `apptoken` header during sync

### Method 2: Two-step Login
1. Get access token: `POST https://api-user.huami.com/registrations/{email}/tokens`
2. Get app token: `POST https://account.huami.com/v2/client/login`

## API Endpoints

### 1. Save Credentials
```http
POST /amazfit/credentials
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
  "app_token": "your_app_token_here",
  "user_id_amazfit": "your_amazfit_user_id"
}
```

### 2. Sync Data
```http
POST /amazfit/sync
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
  "sync_activity": true,
  "sync_steps": true,
  "sync_heart_rate": true,
  "sync_sleep": true,
  "days_back": 7
}
```

### 3. Get Activity Data
```http
GET /amazfit/activity?limit=7
Authorization: Bearer <your_jwt_token>
```

### 4. Get Steps Data
```http
GET /amazfit/steps?limit=7
Authorization: Bearer <your_jwt_token>
```

### 5. Get Heart Rate Data
```http
GET /amazfit/heart-rate?limit=7
Authorization: Bearer <your_jwt_token>
```

### 6. Get Today's Summary
```http
GET /amazfit/today
Authorization: Bearer <your_jwt_token>
```

## Testing the Integration

### 1. Update Test Script
Edit `test_amazfit_integration_complete.py` and update:
```python
FRESH_APP_TOKEN = "your_actual_app_token"
FRESH_USER_ID = "your_actual_user_id"
```

### 2. Run Tests
```bash
cd backend
source venv/bin/activate
python test_amazfit_integration_complete.py
```

### 3. Test Individual Components
```bash
# Test service only
python test_working_amazfit.py

# Test token validity
python test_token_validity.py
```

## Data Structure

### Activity Data
```json
{
  "id": 1,
  "user_id": "user-uuid",
  "date": "2025-07-02",
  "calories_burned": 105,
  "active_minutes": 45,
  "distance_km": 2.5,
  "steps": 2372,
  "sleep_hours": 8.5,
  "deep_sleep_hours": 2.1,
  "light_sleep_hours": 4.2,
  "rem_sleep_hours": 1.8,
  "awake_hours": 0.4,
  "raw_data": {...}
}
```

### Heart Rate Session
```json
{
  "id": 1,
  "user_id": "user-uuid",
  "avg_hr": 72,
  "max_hr": 120,
  "min_hr": 58,
  "duration_minutes": 1440,
  "session_data": {
    "hr_values": [72, 73, 71, ...],
    "stats": {...}
  },
  "logged_at": "2025-07-02T00:00:00Z"
}
```

## Frontend Integration

### 1. Setup Credentials
```javascript
const setupAmazfit = async (appToken, userId) => {
  const response = await fetch('/amazfit/credentials', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      app_token: appToken,
      user_id_amazfit: userId
    })
  });
  return response.json();
};
```

### 2. Sync Data
```javascript
const syncAmazfitData = async (daysBack = 7) => {
  const response = await fetch('/amazfit/sync', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      sync_activity: true,
      sync_steps: true,
      sync_heart_rate: true,
      sync_sleep: true,
      days_back: daysBack
    })
  });
  return response.json();
};
```

### 3. Get Activity Data
```javascript
const getActivityData = async (limit = 7) => {
  const response = await fetch(`/amazfit/activity?limit=${limit}`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  return response.json();
};
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Token is expired or invalid
   - Solution: Get a fresh token from Zepp app

2. **404 Not Found**: API endpoints changed
   - Solution: Check the latest Amazfit API documentation

3. **No Data**: Device not synced recently
   - Solution: Sync your device with Zepp app first

4. **Invalid Heart Rate Data**: Data format changed
   - Solution: Check the decoding logic in `decode_hr_blob()`

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Rate Limiting

The Amazfit API has rate limits:
- Poll every 5 minutes for heart rate/steps
- Poll every 30 minutes for workouts
- Use exponential backoff on 429 errors

## Security Notes

1. **Store tokens securely**: Encrypt tokens at rest
2. **Use HTTPS**: Always communicate over TLS
3. **Token rotation**: Refresh tokens periodically
4. **Access control**: Validate user permissions

## Next Steps

1. Test with your fresh credentials
2. Integrate with your frontend
3. Set up automated syncing
4. Add data visualization
5. Implement alerts and notifications

## Support

If you encounter issues:
1. Check the test scripts for examples
2. Review the Amazfit API documentation
3. Check the logs for error messages
4. Verify your credentials are valid 