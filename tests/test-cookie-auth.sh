#!/bin/bash

# Test script for cookie-based authentication
API_URL="http://100.123.199.100:8000"

echo "Testing cookie-based authentication..."
echo "API URL: $API_URL"
echo ""

# Test 1: Register a test user
echo "1. Testing user registration..."
REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword123"}')

HTTP_CODE=$(echo "$REGISTER_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$REGISTER_RESPONSE" | head -n -1)

echo "HTTP Code: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"
echo ""

# Test 2: Login and capture cookies
echo "2. Testing login with cookie capture..."
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword123"}' \
  -c cookies.txt)

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)

echo "HTTP Code: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"
echo ""

# Display cookies
echo "Cookies received:"
cat cookies.txt
echo ""

# Test 3: Access protected endpoint with cookies
echo "3. Testing protected endpoint access with cookies..."
PROTECTED_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/auth/me" \
  -b cookies.txt)

HTTP_CODE=$(echo "$PROTECTED_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$PROTECTED_RESPONSE" | head -n -1)

echo "HTTP Code: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"
echo ""

# Test 4: Access dashboard with cookies
echo "4. Testing dashboard access with cookies..."
DASHBOARD_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/dashboard" \
  -b cookies.txt)

HTTP_CODE=$(echo "$DASHBOARD_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$DASHBOARD_RESPONSE" | head -n -1)

echo "HTTP Code: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"
echo ""

# Test 5: Test without cookies (should fail)
echo "5. Testing protected endpoint without cookies (should fail)..."
NO_COOKIE_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/auth/me")

HTTP_CODE=$(echo "$NO_COOKIE_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$NO_COOKIE_RESPONSE" | head -n -1)

echo "HTTP Code: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"
echo ""

# Test 6: Test token refresh
echo "6. Testing token refresh..."
REFRESH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/refresh" \
  -b cookies.txt \
  -c cookies_refresh.txt)

HTTP_CODE=$(echo "$REFRESH_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$REFRESH_RESPONSE" | head -n -1)

echo "HTTP Code: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"
echo ""

# Test 7: Logout
echo "7. Testing logout..."
LOGOUT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/logout" \
  -b cookies.txt)

HTTP_CODE=$(echo "$LOGOUT_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$LOGOUT_RESPONSE" | head -n -1)

echo "HTTP Code: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"
echo ""

# Cleanup
rm -f cookies.txt cookies_refresh.txt

echo "Test completed!" 