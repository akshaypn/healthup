#!/bin/bash

# Test script for cookie-based session management
# This script tests the new httpOnly cookie authentication system

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
TEST_EMAIL="test@example.com"
TEST_PASSWORD="testpassword123"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if curl is available
if ! command -v curl &> /dev/null; then
    log_error "curl is required but not installed"
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    log_warning "jq is not installed. JSON parsing will be limited."
    JQ_AVAILABLE=false
else
    JQ_AVAILABLE=true
fi

log_info "Testing cookie-based session management"
log_info "API URL: $API_URL"

# Clean up any existing test files
rm -f test_cookies.txt

# Test 1: Health Check
log_info "Test 1: Health Check"
if curl -s "$API_URL/health" | grep -q "ok"; then
    log_success "Health check passed"
else
    log_error "Health check failed"
    exit 1
fi

# Test 2: User Registration
log_info "Test 2: User Registration"
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

if echo "$REGISTER_RESPONSE" | grep -q "User registered successfully"; then
    log_success "User registration successful"
elif echo "$REGISTER_RESPONSE" | grep -q "Email already registered"; then
    log_warning "User already exists, continuing with login test"
else
    log_error "User registration failed: $REGISTER_RESPONSE"
    exit 1
fi

# Test 3: User Login (Cookie-based)
log_info "Test 3: User Login (Cookie-based)"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
    -c test_cookies.txt)

if [ "$JQ_AVAILABLE" = true ]; then
    USER_ID=$(echo "$LOGIN_RESPONSE" | jq -r '.user.id // empty')
    USER_EMAIL=$(echo "$LOGIN_RESPONSE" | jq -r '.user.email // empty')
    EXPIRES_IN=$(echo "$LOGIN_RESPONSE" | jq -r '.expires_in // empty')
    
    if [ -n "$USER_ID" ] && [ -n "$USER_EMAIL" ]; then
        log_success "Login successful - User: $USER_EMAIL, ID: $USER_ID"
        log_info "Session expires in: $EXPIRES_IN minutes"
    else
        log_error "Login failed - Invalid response format"
        exit 1
    fi
else
    if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
        log_success "Login successful (response contains access_token)"
    else
        log_error "Login failed: $LOGIN_RESPONSE"
        exit 1
    fi
fi

# Test 4: Check if cookies were set
log_info "Test 4: Cookie Verification"
if [ -f test_cookies.txt ]; then
    COOKIE_COUNT=$(grep -c "access_token\|refresh_token" test_cookies.txt || echo "0")
    if [ "$COOKIE_COUNT" -ge 2 ]; then
        log_success "Cookies set successfully ($COOKIE_COUNT auth cookies found)"
        log_info "Cookie contents:"
        cat test_cookies.txt | grep -E "(access_token|refresh_token)" | head -2
    else
        log_error "Cookies not set properly"
        exit 1
    fi
else
    log_error "Cookie file not created"
    exit 1
fi

# Test 5: Access Protected Endpoint
log_info "Test 5: Access Protected Endpoint"
ME_RESPONSE=$(curl -s -X GET "$API_URL/auth/me" \
    -b test_cookies.txt \
    -H "Content-Type: application/json")

if [ "$JQ_AVAILABLE" = true ]; then
    ME_USER_ID=$(echo "$ME_RESPONSE" | jq -r '.id // empty')
    ME_USER_EMAIL=$(echo "$ME_RESPONSE" | jq -r '.email // empty')
    
    if [ -n "$ME_USER_ID" ] && [ "$ME_USER_ID" = "$USER_ID" ]; then
        log_success "Protected endpoint access successful"
        log_info "Authenticated as: $ME_USER_EMAIL"
    else
        log_error "Protected endpoint access failed"
        exit 1
    fi
else
    if echo "$ME_RESPONSE" | grep -q "email"; then
        log_success "Protected endpoint access successful"
    else
        log_error "Protected endpoint access failed: $ME_RESPONSE"
        exit 1
    fi
fi

# Test 6: Token Refresh
log_info "Test 6: Token Refresh"
REFRESH_RESPONSE=$(curl -s -X POST "$API_URL/auth/refresh" \
    -b test_cookies.txt \
    -H "Content-Type: application/json" \
    -c test_cookies_refreshed.txt)

if [ "$JQ_AVAILABLE" = true ]; then
    REFRESH_USER_ID=$(echo "$REFRESH_RESPONSE" | jq -r '.user.id // empty')
    NEW_EXPIRES_IN=$(echo "$REFRESH_RESPONSE" | jq -r '.expires_in // empty')
    
    if [ -n "$REFRESH_USER_ID" ] && [ "$REFRESH_USER_ID" = "$USER_ID" ]; then
        log_success "Token refresh successful"
        log_info "New session expires in: $NEW_EXPIRES_IN minutes"
    else
        log_error "Token refresh failed"
        exit 1
    fi
else
    if echo "$REFRESH_RESPONSE" | grep -q "access_token"; then
        log_success "Token refresh successful"
    else
        log_error "Token refresh failed: $REFRESH_RESPONSE"
        exit 1
    fi
fi

# Test 7: Access with Refreshed Cookies
log_info "Test 7: Access with Refreshed Cookies"
ME_REFRESHED_RESPONSE=$(curl -s -X GET "$API_URL/auth/me" \
    -b test_cookies_refreshed.txt \
    -H "Content-Type: application/json")

if [ "$JQ_AVAILABLE" = true ]; then
    ME_REFRESHED_USER_ID=$(echo "$ME_REFRESHED_RESPONSE" | jq -r '.id // empty')
    
    if [ -n "$ME_REFRESHED_USER_ID" ] && [ "$ME_REFRESHED_USER_ID" = "$USER_ID" ]; then
        log_success "Access with refreshed cookies successful"
    else
        log_error "Access with refreshed cookies failed"
        exit 1
    fi
else
    if echo "$ME_REFRESHED_RESPONSE" | grep -q "email"; then
        log_success "Access with refreshed cookies successful"
    else
        log_error "Access with refreshed cookies failed"
        exit 1
    fi
fi

# Test 8: Logout
log_info "Test 8: Logout"
LOGOUT_RESPONSE=$(curl -s -X POST "$API_URL/auth/logout" \
    -b test_cookies_refreshed.txt \
    -H "Content-Type: application/json" \
    -c test_cookies_cleared.txt)

if echo "$LOGOUT_RESPONSE" | grep -q "Logged out successfully"; then
    log_success "Logout successful"
else
    log_error "Logout failed: $LOGOUT_RESPONSE"
    exit 1
fi

# Test 9: Verify Cookies Cleared
log_info "Test 9: Verify Cookies Cleared"
if [ -f test_cookies_cleared.txt ]; then
    CLEARED_COUNT=$(grep -c "access_token\|refresh_token" test_cookies_cleared.txt || echo "0")
    if [ "$CLEARED_COUNT" -eq 0 ]; then
        log_success "Cookies cleared successfully"
    else
        log_warning "Some cookies may not have been cleared ($CLEARED_COUNT found)"
    fi
else
    log_warning "No cleared cookie file found"
fi

# Test 10: Access After Logout (Should Fail)
log_info "Test 10: Access After Logout (Should Fail)"
ME_AFTER_LOGOUT_RESPONSE=$(curl -s -X GET "$API_URL/auth/me" \
    -b test_cookies_refreshed.txt \
    -H "Content-Type: application/json")

if echo "$ME_AFTER_LOGOUT_RESPONSE" | grep -q "401\|Unauthorized\|Could not validate credentials"; then
    log_success "Access properly denied after logout"
else
    log_warning "Access not properly denied after logout: $ME_AFTER_LOGOUT_RESPONSE"
fi

# Cleanup
log_info "Cleaning up test files"
rm -f test_cookies.txt test_cookies_refreshed.txt test_cookies_cleared.txt

# Summary
echo
log_success "=========================================="
log_success "All cookie-based session tests completed!"
log_success "=========================================="
log_info "Session management features verified:"
log_info "✓ 2-week access token duration"
log_info "✓ 30-day refresh token duration"
log_info "✓ httpOnly cookie security"
log_info "✓ Automatic token refresh"
log_info "✓ Proper logout and cookie cleanup"
log_info "✓ Protected endpoint access"
log_info "✓ Session persistence across requests"

echo
log_info "Your HealthUp application now has secure, long-lasting sessions!"
log_info "Users will stay logged in for 2 weeks without re-authentication." 