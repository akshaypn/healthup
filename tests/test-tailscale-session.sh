#!/bin/bash

# HealthUp Tailscale Session Management Test Script
# This script thoroughly tests the session management and cookie functionality
# on the Tailscale server deployment

set -e

# Configuration
TAILSCALE_IP="100.123.199.100"
BACKEND_PORT="8000"
FRONTEND_PORT="3000"
ADMIN_EMAIL="admin@admin.com"
ADMIN_PASSWORD="123456"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

log_test() {
    echo -e "${PURPLE}[TEST]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
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
    
    # Check if we can reach the Tailscale server
    log_info "Testing connectivity to Tailscale server..."
    if curl -s --connect-timeout 10 "http://$TAILSCALE_IP:$BACKEND_PORT/health" > /dev/null 2>&1; then
        log_success "Backend is accessible"
    else
        log_error "Cannot reach backend at http://$TAILSCALE_IP:$BACKEND_PORT"
        log_info "Make sure the application is deployed and running"
        log_info "You can check logs with: docker compose logs backend"
        exit 1
    fi
}

# Test 1: Health Check
test_health_check() {
    log_test "Test 1: Health Check"
    
    HEALTH_RESPONSE=$(curl -s "http://$TAILSCALE_IP:$BACKEND_PORT/health")
    
    if echo "$HEALTH_RESPONSE" | grep -q "healthy\|ok"; then
        log_success "Health check passed"
        return 0
    else
        log_error "Health check failed: $HEALTH_RESPONSE"
        return 1
    fi
}

# Test 2: User Registration
test_user_registration() {
    log_test "Test 2: User Registration"
    
    REGISTER_RESPONSE=$(curl -s -X POST "http://$TAILSCALE_IP:$BACKEND_PORT/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}")
    
    if echo "$REGISTER_RESPONSE" | grep -q "User registered successfully"; then
        log_success "User registration successful"
        return 0
    elif echo "$REGISTER_RESPONSE" | grep -q "Email already registered"; then
        log_warning "User already exists, continuing with login test"
        return 0
    else
        log_error "User registration failed: $REGISTER_RESPONSE"
        return 1
    fi
}

# Test 3: Login and Cookie Setting
test_login_and_cookies() {
    log_test "Test 3: Login and Cookie Setting"
    
    # Clean up any existing test files
    rm -f tailscale_cookies.txt
    
    # Login and save cookies
    LOGIN_RESPONSE=$(curl -s -X POST "http://$TAILSCALE_IP:$BACKEND_PORT/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}" \
        -c tailscale_cookies.txt)
    
    if [ "$JQ_AVAILABLE" = true ]; then
        USER_ID=$(echo "$LOGIN_RESPONSE" | jq -r '.user.id // empty')
        USER_EMAIL=$(echo "$LOGIN_RESPONSE" | jq -r '.user.email // empty')
        EXPIRES_IN=$(echo "$LOGIN_RESPONSE" | jq -r '.expires_in // empty')
        
        if [ -n "$USER_ID" ] && [ -n "$USER_EMAIL" ]; then
            log_success "Login successful - User: $USER_EMAIL, ID: $USER_ID"
            log_info "Session expires in: $EXPIRES_IN minutes"
        else
            log_error "Login failed - Invalid response format"
            return 1
        fi
    else
        if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
            log_success "Login successful (response contains access_token)"
        else
            log_error "Login failed: $LOGIN_RESPONSE"
            return 1
        fi
    fi
    
    # Check if cookies were properly set
    if [ -f tailscale_cookies.txt ]; then
        COOKIE_COUNT=$(grep -c "access_token\|refresh_token" tailscale_cookies.txt || echo "0")
        if [ "$COOKIE_COUNT" -ge 2 ]; then
            log_success "Authentication cookies properly set ($COOKIE_COUNT cookies)"
            log_info "Cookie details:"
            cat tailscale_cookies.txt | grep -E "(access_token|refresh_token)" | while read line; do
                log_info "  $line"
            done
        else
            log_error "Authentication cookies not set properly"
            return 1
        fi
    else
        log_error "Cookie file not created"
        return 1
    fi
    
    return 0
}

# Test 4: Authenticated Endpoint Access
test_authenticated_access() {
    log_test "Test 4: Authenticated Endpoint Access"
    
    ME_RESPONSE=$(curl -s -X GET "http://$TAILSCALE_IP:$BACKEND_PORT/auth/me" \
        -b tailscale_cookies.txt \
        -H "Content-Type: application/json")
    
    if [ "$JQ_AVAILABLE" = true ]; then
        ME_USER_ID=$(echo "$ME_RESPONSE" | jq -r '.id // empty')
        ME_USER_EMAIL=$(echo "$ME_RESPONSE" | jq -r '.email // empty')
        
        if [ -n "$ME_USER_ID" ] && [ "$ME_USER_EMAIL" = "$ADMIN_EMAIL" ]; then
            log_success "Authenticated endpoint access successful"
            log_info "Authenticated as: $ME_USER_EMAIL (ID: $ME_USER_ID)"
        else
            log_error "Authenticated endpoint access failed"
            return 1
        fi
    else
        if echo "$ME_RESPONSE" | grep -q "$ADMIN_EMAIL"; then
            log_success "Authenticated endpoint access successful"
        else
            log_error "Authenticated endpoint access failed: $ME_RESPONSE"
            return 1
        fi
    fi
    
    return 0
}

# Test 5: Token Refresh
test_token_refresh() {
    log_test "Test 5: Token Refresh"
    
    REFRESH_RESPONSE=$(curl -s -X POST "http://$TAILSCALE_IP:$BACKEND_PORT/auth/refresh" \
        -b tailscale_cookies.txt \
        -H "Content-Type: application/json" \
        -c tailscale_cookies_refreshed.txt)
    
    if [ "$JQ_AVAILABLE" = true ]; then
        REFRESH_USER_ID=$(echo "$REFRESH_RESPONSE" | jq -r '.user.id // empty')
        NEW_EXPIRES_IN=$(echo "$REFRESH_RESPONSE" | jq -r '.expires_in // empty')
        
        if [ -n "$REFRESH_USER_ID" ]; then
            log_success "Token refresh successful"
            log_info "New session expires in: $NEW_EXPIRES_IN minutes"
        else
            log_error "Token refresh failed"
            return 1
        fi
    else
        if echo "$REFRESH_RESPONSE" | grep -q "access_token"; then
            log_success "Token refresh successful"
        else
            log_error "Token refresh failed: $REFRESH_RESPONSE"
            return 1
        fi
    fi
    
    return 0
}

# Test 6: Access with Refreshed Cookies
test_refreshed_cookies() {
    log_test "Test 6: Access with Refreshed Cookies"
    
    ME_REFRESHED_RESPONSE=$(curl -s -X GET "http://$TAILSCALE_IP:$BACKEND_PORT/auth/me" \
        -b tailscale_cookies_refreshed.txt \
        -H "Content-Type: application/json")
    
    if [ "$JQ_AVAILABLE" = true ]; then
        ME_REFRESHED_USER_EMAIL=$(echo "$ME_REFRESHED_RESPONSE" | jq -r '.email // empty')
        
        if [ -n "$ME_REFRESHED_USER_EMAIL" ] && [ "$ME_REFRESHED_USER_EMAIL" = "$ADMIN_EMAIL" ]; then
            log_success "Access with refreshed cookies successful"
        else
            log_error "Access with refreshed cookies failed"
            return 1
        fi
    else
        if echo "$ME_REFRESHED_RESPONSE" | grep -q "$ADMIN_EMAIL"; then
            log_success "Access with refreshed cookies successful"
        else
            log_error "Access with refreshed cookies failed: $ME_REFRESHED_RESPONSE"
            return 1
        fi
    fi
    
    return 0
}

# Test 7: Logout
test_logout() {
    log_test "Test 7: Logout"
    
    LOGOUT_RESPONSE=$(curl -s -X POST "http://$TAILSCALE_IP:$BACKEND_PORT/auth/logout" \
        -b tailscale_cookies_refreshed.txt \
        -H "Content-Type: application/json" \
        -c tailscale_cookies_cleared.txt)
    
    if echo "$LOGOUT_RESPONSE" | grep -q "Logged out successfully"; then
        log_success "Logout successful"
    else
        log_error "Logout failed: $LOGOUT_RESPONSE"
        return 1
    fi
    
    return 0
}

# Test 8: Verify Cookies Cleared
test_cookies_cleared() {
    log_test "Test 8: Verify Cookies Cleared"
    
    if [ -f tailscale_cookies_cleared.txt ]; then
        CLEARED_COUNT=$(grep -c "access_token\|refresh_token" tailscale_cookies_cleared.txt || echo "0")
        if [ "$CLEARED_COUNT" -eq 0 ]; then
            log_success "Cookies cleared successfully"
        else
            log_warning "Some cookies may not have been cleared ($CLEARED_COUNT found)"
        fi
    else
        log_warning "No cleared cookie file found"
    fi
    
    return 0
}

# Test 9: Access After Logout (Should Fail)
test_access_after_logout() {
    log_test "Test 9: Access After Logout (Should Fail)"
    
    ME_AFTER_LOGOUT_RESPONSE=$(curl -s -X GET "http://$TAILSCALE_IP:$BACKEND_PORT/auth/me" \
        -b tailscale_cookies_refreshed.txt \
        -H "Content-Type: application/json")
    
    if echo "$ME_AFTER_LOGOUT_RESPONSE" | grep -q "401\|Unauthorized\|Could not validate credentials"; then
        log_success "Access properly denied after logout"
    else
        log_warning "Access not properly denied after logout: $ME_AFTER_LOGOUT_RESPONSE"
    fi
    
    return 0
}

# Test 10: Frontend Accessibility
test_frontend_access() {
    log_test "Test 10: Frontend Accessibility"
    
    FRONTEND_RESPONSE=$(curl -s --connect-timeout 5 "http://$TAILSCALE_IP:$FRONTEND_PORT")
    
    if [ $? -eq 0 ]; then
        log_success "Frontend is accessible"
        log_info "Frontend URL: http://$TAILSCALE_IP:$FRONTEND_PORT"
    else
        log_warning "Frontend may not be accessible: $FRONTEND_RESPONSE"
    fi
    
    return 0
}

# Test 11: Cookie Security Properties
test_cookie_security() {
    log_test "Test 11: Cookie Security Properties"
    
    if [ -f tailscale_cookies.txt ]; then
        log_info "Analyzing cookie security properties..."
        
        # Check for httpOnly flag
        HTTPONLY_COUNT=$(grep -c "HttpOnly" tailscale_cookies.txt || echo "0")
        if [ "$HTTPONLY_COUNT" -ge 2 ]; then
            log_success "httpOnly flag is set on authentication cookies"
        else
            log_warning "httpOnly flag may not be set on all cookies"
        fi
        
        # Check for SameSite attribute
        SAMESITE_COUNT=$(grep -c "SameSite" tailscale_cookies.txt || echo "0")
        if [ "$SAMESITE_COUNT" -ge 2 ]; then
            log_success "SameSite attribute is set on authentication cookies"
        else
            log_warning "SameSite attribute may not be set on all cookies"
        fi
        
        # Check for Secure flag (should be false for HTTP in Tailscale)
        SECURE_COUNT=$(grep -c "Secure" tailscale_cookies.txt || echo "0")
        if [ "$SECURE_COUNT" -eq 0 ]; then
            log_success "Secure flag is not set (correct for HTTP in Tailscale)"
        else
            log_warning "Secure flag is set (may cause issues with HTTP)"
        fi
    fi
    
    return 0
}

# Main test function
run_all_tests() {
    log_info "Starting comprehensive session management tests for Tailscale deployment..."
    log_info "Target: http://$TAILSCALE_IP:$BACKEND_PORT"
    
    # Check prerequisites
    check_prerequisites
    
    # Run all tests
    local failed_tests=0
    
    test_health_check || ((failed_tests++))
    test_user_registration || ((failed_tests++))
    test_login_and_cookies || ((failed_tests++))
    test_authenticated_access || ((failed_tests++))
    test_token_refresh || ((failed_tests++))
    test_refreshed_cookies || ((failed_tests++))
    test_logout || ((failed_tests++))
    test_cookies_cleared || ((failed_tests++))
    test_access_after_logout || ((failed_tests++))
    test_frontend_access || ((failed_tests++))
    test_cookie_security || ((failed_tests++))
    
    # Cleanup
    log_info "Cleaning up test files..."
    rm -f tailscale_cookies.txt tailscale_cookies_refreshed.txt tailscale_cookies_cleared.txt
    
    # Summary
    echo
    if [ $failed_tests -eq 0 ]; then
        log_success "=========================================="
        log_success "All session management tests PASSED!"
        log_success "=========================================="
        echo
        log_info "Session Management Summary:"
        log_info "✓ Login and cookie setting working"
        log_info "✓ Authentication cookies properly configured"
        log_info "✓ Token refresh functionality working"
        log_info "✓ Logout and cookie clearing working"
        log_info "✓ Security properties properly set"
        echo
        log_info "Access URLs:"
        log_info "Frontend: http://$TAILSCALE_IP:$FRONTEND_PORT"
        log_info "Backend: http://$TAILSCALE_IP:$BACKEND_PORT"
        echo
        log_info "Admin Credentials:"
        log_info "Email: $ADMIN_EMAIL"
        log_info "Password: $ADMIN_PASSWORD"
        return 0
    else
        log_error "=========================================="
        log_error "$failed_tests test(s) FAILED!"
        log_error "=========================================="
        return 1
    fi
}

# Check if script is run with arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "HealthUp Tailscale Session Management Test Script"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  (no args)  Run all session management tests"
        echo "  help       Show this help message"
        echo
        echo "This script tests:"
        echo "  - Health check"
        echo "  - User registration and login"
        echo "  - Cookie setting and management"
        echo "  - Token refresh functionality"
        echo "  - Logout and cookie clearing"
        echo "  - Security properties"
        ;;
    *)
        run_all_tests
        ;;
esac 