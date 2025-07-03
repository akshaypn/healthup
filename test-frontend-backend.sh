#!/bin/bash

# Test script for frontend-backend communication
FRONTEND_URL="http://100.123.199.100:3000"
BACKEND_URL="http://100.123.199.100:8000"

echo "Testing frontend-backend communication..."
echo "Frontend URL: $FRONTEND_URL"
echo "Backend URL: $BACKEND_URL"
echo ""

# Test 1: Check if frontend is accessible
echo "1. Testing frontend accessibility..."
FRONTEND_RESPONSE=$(curl -s -w "\n%{http_code}" -I "$FRONTEND_URL")
HTTP_CODE=$(echo "$FRONTEND_RESPONSE" | tail -n1)
echo "HTTP Code: $HTTP_CODE"
echo ""

# Test 2: Test CORS preflight request
echo "2. Testing CORS preflight request..."
CORS_RESPONSE=$(curl -s -w "\n%{http_code}" -X OPTIONS "$BACKEND_URL/auth/me" \
  -H "Origin: $FRONTEND_URL" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type")

HTTP_CODE=$(echo "$CORS_RESPONSE" | tail -n1)
echo "HTTP Code: $HTTP_CODE"
echo ""

# Test 3: Test actual request with Origin header
echo "3. Testing request with Origin header..."
ORIGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BACKEND_URL/auth/me" \
  -H "Origin: $FRONTEND_URL" \
  -H "Content-Type: application/json")

HTTP_CODE=$(echo "$ORIGIN_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$ORIGIN_RESPONSE" | head -n -1)
echo "HTTP Code: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"
echo ""

# Test 4: Test login with Origin header
echo "4. Testing login with Origin header..."
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/auth/login" \
  -H "Origin: $FRONTEND_URL" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword123"}' \
  -c test_cookies.txt)

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)
echo "HTTP Code: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"
echo ""

# Test 5: Test protected endpoint with cookies and Origin
echo "5. Testing protected endpoint with cookies and Origin..."
PROTECTED_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BACKEND_URL/dashboard" \
  -H "Origin: $FRONTEND_URL" \
  -b test_cookies.txt)

HTTP_CODE=$(echo "$PROTECTED_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$PROTECTED_RESPONSE" | head -n -1)
echo "HTTP Code: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"
echo ""

# Cleanup
rm -f test_cookies.txt

echo "Test completed!" 