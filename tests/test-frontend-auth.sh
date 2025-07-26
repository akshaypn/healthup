#!/bin/bash

# Test script to simulate frontend authentication flow
FRONTEND_URL="http://100.123.199.100:3000"
BACKEND_URL="http://100.123.199.100:8000"

echo "Testing frontend authentication flow..."
echo ""

# Test 1: Get the frontend page
echo "1. Getting frontend page..."
FRONTEND_PAGE=$(curl -s "$FRONTEND_URL")
if [[ $FRONTEND_PAGE == *"HealthUp"* ]]; then
    echo "✅ Frontend page loaded successfully"
else
    echo "❌ Frontend page failed to load"
fi
echo ""

# Test 2: Simulate login from frontend
echo "2. Simulating frontend login..."
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/auth/login" \
  -H "Origin: $FRONTEND_URL" \
  -H "Referer: $FRONTEND_URL/" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword123"}' \
  -c frontend_cookies.txt)

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Login successful"
    echo "Cookies set:"
    cat frontend_cookies.txt
else
    echo "❌ Login failed: HTTP $HTTP_CODE"
    echo "Response: $RESPONSE_BODY"
fi
echo ""

# Test 3: Simulate frontend API calls
echo "3. Testing frontend API calls with cookies..."
API_CALLS=(
    "GET /auth/me"
    "GET /dashboard"
    "GET /weight/history"
)

for call in "${API_CALLS[@]}"; do
    METHOD=$(echo "$call" | cut -d' ' -f1)
    ENDPOINT=$(echo "$call" | cut -d' ' -f2)
    
    echo "Testing $METHOD $ENDPOINT..."
    RESPONSE=$(curl -s -w "\n%{http_code}" -X "$METHOD" "$BACKEND_URL$ENDPOINT" \
      -H "Origin: $FRONTEND_URL" \
      -H "Referer: $FRONTEND_URL/" \
      -b frontend_cookies.txt)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    RESPONSE_BODY=$(echo "$RESPONSE" | head -n -1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ $METHOD $ENDPOINT: Success"
    else
        echo "❌ $METHOD $ENDPOINT: HTTP $HTTP_CODE"
        echo "   Response: $RESPONSE_BODY"
    fi
done
echo ""

# Test 4: Test logout
echo "4. Testing logout..."
LOGOUT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/auth/logout" \
  -H "Origin: $FRONTEND_URL" \
  -H "Referer: $FRONTEND_URL/" \
  -b frontend_cookies.txt)

HTTP_CODE=$(echo "$LOGOUT_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Logout successful"
else
    echo "❌ Logout failed: HTTP $HTTP_CODE"
fi
echo ""

# Cleanup
rm -f frontend_cookies.txt

echo "Frontend authentication test completed!" 