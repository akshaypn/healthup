#!/bin/bash

# Test script for authentication flow
API_URL="http://localhost:8000"

echo "Testing authentication flow..."

# Test login
echo "1. Testing login..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@admin.com", "password": "admin123"}')

echo "Login response:"
echo "$LOGIN_RESPONSE" | jq '.'

# Extract access token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Login failed - no access token received"
    exit 1
fi

echo "✅ Login successful - access token received"

# Test /auth/me endpoint
echo ""
echo "2. Testing /auth/me endpoint..."
ME_RESPONSE=$(curl -s -X GET "$API_URL/auth/me" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Auth me response:"
echo "$ME_RESPONSE" | jq '.'

if echo "$ME_RESPONSE" | jq -e '.id' > /dev/null; then
    echo "✅ /auth/me successful"
else
    echo "❌ /auth/me failed"
    exit 1
fi

# Test dashboard endpoint
echo ""
echo "3. Testing /dashboard endpoint..."
DASHBOARD_RESPONSE=$(curl -s -X GET "$API_URL/dashboard" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Dashboard response:"
echo "$DASHBOARD_RESPONSE" | jq '.'

if echo "$DASHBOARD_RESPONSE" | jq -e '.stats' > /dev/null; then
    echo "✅ Dashboard successful"
else
    echo "❌ Dashboard failed"
    exit 1
fi

# Test weight history endpoint
echo ""
echo "4. Testing /weight/history endpoint..."
WEIGHT_RESPONSE=$(curl -s -X GET "$API_URL/weight/history" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Weight history response:"
echo "$WEIGHT_RESPONSE" | jq '.'

if echo "$WEIGHT_RESPONSE" | jq -e '.logs' > /dev/null; then
    echo "✅ Weight history successful"
else
    echo "❌ Weight history failed"
    exit 1
fi

echo ""
echo "🎉 All authentication tests passed!" 