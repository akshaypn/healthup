#!/bin/bash

echo "🚀 HealthUp Comprehensive Endpoint Test"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local headers="$5"
    
    echo -n "Testing $name... "
    
    if [ -n "$data" ]; then
        if [ -n "$headers" ]; then
            response=$(curl -s -w "%{http_code}" -X "$method" "$url" -H "$headers" -d "$data")
        else
            response=$(curl -s -w "%{http_code}" -X "$method" "$url" -d "$data")
        fi
    else
        if [ -n "$headers" ]; then
            response=$(curl -s -w "%{http_code}" -X "$method" "$url" -H "$headers")
        else
            response=$(curl -s -w "%{http_code}" -X "$method" "$url")
        fi
    fi
    
    # Extract status code (last 3 characters)
    status_code="${response: -3}"
    # Extract response body (everything except last 3 characters)
    response_body="${response%???}"
    
    if [ "$status_code" -ge 200 ] && [ "$status_code" -lt 300 ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL (Status: $status_code)${NC}"
        echo "  Response: $response_body"
        ((TESTS_FAILED++))
    fi
}

# Get authentication token
echo -e "${BLUE}🔐 Getting authentication token...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@admin.com", "password": "123456"}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
    echo -e "${GREEN}✅ Authentication successful${NC}"
else
    echo -e "${RED}❌ Authentication failed${NC}"
    exit 1
fi

AUTH_HEADER="Authorization: Bearer $TOKEN"

echo ""
echo -e "${BLUE}📊 Testing Backend API Endpoints${NC}"
echo "----------------------------------------"

# Basic endpoints
test_endpoint "Root endpoint" "GET" "http://localhost:8000/"
test_endpoint "Health check" "GET" "http://localhost:8000/health"

# Authentication endpoints
test_endpoint "User profile" "GET" "http://localhost:8000/auth/me" "" "$AUTH_HEADER"

# Dashboard
test_endpoint "Dashboard" "GET" "http://localhost:8000/dashboard" "" "$AUTH_HEADER"

# Food logging endpoints
test_endpoint "Food history" "GET" "http://localhost:8000/food/history" "" "$AUTH_HEADER"
test_endpoint "Today's food" "GET" "http://localhost:8000/food/today" "" "$AUTH_HEADER"
test_endpoint "Nutrition summary" "GET" "http://localhost:8000/food/nutrition-summary" "" "$AUTH_HEADER"

# Create a test food log
FOOD_DATA='{"description": "Test food for endpoint testing", "calories": 200, "protein_g": 20, "fat_g": 10, "carbs_g": 15}'
test_endpoint "Create food log" "POST" "http://localhost:8000/food" "$FOOD_DATA" "Content-Type: application/json; $AUTH_HEADER"

# Get the food log ID for further testing
FOOD_RESPONSE=$(curl -s -X GET "http://localhost:8000/food/history" -H "$AUTH_HEADER")
FOOD_ID=$(echo "$FOOD_RESPONSE" | jq -r '.logs[0].id')

if [ "$FOOD_ID" != "null" ] && [ "$FOOD_ID" != "" ]; then
    test_endpoint "Update food log" "PUT" "http://localhost:8000/food/$FOOD_ID" '{"description": "Updated test food"}' "Content-Type: application/json; $AUTH_HEADER"
    test_endpoint "Analyze food log" "POST" "http://localhost:8000/food/$FOOD_ID/analyze" "" "$AUTH_HEADER"
    test_endpoint "Get food analysis" "GET" "http://localhost:8000/food/$FOOD_ID/analysis" "" "$AUTH_HEADER"
    test_endpoint "Delete food log" "DELETE" "http://localhost:8000/food/$FOOD_ID" "" "$AUTH_HEADER"
fi

# AI food parsing
PARSE_DATA='{"user_input": "I had a grilled chicken breast with brown rice for lunch"}'
test_endpoint "AI food parsing" "POST" "http://localhost:8000/food/parse" "$PARSE_DATA" "Content-Type: application/json; $AUTH_HEADER"

# Weight logging
test_endpoint "Weight history" "GET" "http://localhost:8000/weight/history" "" "$AUTH_HEADER"
test_endpoint "Create weight log" "POST" "http://localhost:8000/weight" '{"kg": 75.5}' "Content-Type: application/json; $AUTH_HEADER"

# AI coach chat
test_endpoint "AI coach chat" "POST" "http://localhost:8000/coach/chat" '{"message": "How can I improve my nutrition?"}' "Content-Type: application/json; $AUTH_HEADER"

# AI insights
test_endpoint "Daily insight" "GET" "http://localhost:8000/insight/daily" "" "$AUTH_HEADER"
test_endpoint "Weekly insight" "GET" "http://localhost:8000/insight/weekly" "" "$AUTH_HEADER"

echo ""
echo -e "${BLUE}🌐 Testing Frontend Accessibility${NC}"
echo "----------------------------------------"

# Test frontend
test_endpoint "Frontend root" "GET" "http://localhost:3000/"
test_endpoint "Frontend health" "GET" "http://localhost:3000/health"

echo ""
echo -e "${BLUE}🗄️  Testing Database Services${NC}"
echo "----------------------------------------"

# Test database connectivity
test_endpoint "PostgreSQL" "GET" "http://localhost:5433" "" ""

# Test Redis (basic connectivity)
if docker compose exec redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis connectivity${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Redis connectivity${NC}"
    ((TESTS_FAILED++))
fi

echo ""
echo -e "${BLUE}📈 Test Summary${NC}"
echo "=================="
echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"
echo -e "${BLUE}📊 Total Tests: $((TESTS_PASSED + TESTS_FAILED))${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All tests passed! HealthUp is fully operational.${NC}"
    echo ""
    echo -e "${BLUE}🌐 Access your application:${NC}"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Documentation: http://localhost:8000/docs"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️  Some tests failed. Please check the logs above.${NC}"
    exit 1
fi 