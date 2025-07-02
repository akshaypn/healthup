#!/bin/bash

echo "🧪 Testing HealthUp Deployment"
echo "=============================="

# Test local setup
API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

echo "📍 API URL: $API_URL"
echo "📍 Frontend URL: $FRONTEND_URL"
echo ""

# Test 1: Backend API health
echo "🔍 Test 1: Backend API Health"
if curl -s "$API_URL/docs" | grep -q "FastAPI"; then
    echo "✅ Backend API is running"
else
    echo "❌ Backend API is not accessible"
    exit 1
fi

# Test 2: Frontend accessibility
echo "🔍 Test 2: Frontend Accessibility"
if curl -s "$FRONTEND_URL" | grep -q "HealthUp"; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend is not accessible"
    exit 1
fi

# Test 3: Login functionality
echo "🔍 Test 3: Login Functionality"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@admin.com", "password": "123456"}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login is working"
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "   Token received: ${TOKEN:0:20}..."
else
    echo "❌ Login failed: $LOGIN_RESPONSE"
    exit 1
fi

# Test 4: User profile access
echo "🔍 Test 4: User Profile Access"
PROFILE_RESPONSE=$(curl -s -X GET "$API_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN")

if echo "$PROFILE_RESPONSE" | grep -q "admin@admin.com"; then
    echo "✅ User profile access is working"
else
    echo "❌ User profile access failed: $PROFILE_RESPONSE"
    exit 1
fi

echo ""
echo "🎉 All tests passed! HealthUp is working correctly."
echo ""
echo "🌐 Access URLs:"
echo "   Frontend: $FRONTEND_URL"
echo "   Backend API: $API_URL"
echo "   API Docs: $API_URL/docs"
echo ""
echo "🔑 Login credentials:"
echo "   Email: admin@admin.com"
echo "   Password: 123456" 