#!/bin/bash

# HealthUp Tailscale Server Deployment Script
# This script deploys the healthup application on a Tailscale server
# with proper session management and cookie configuration

set -e

# Configuration
TAILSCALE_IP="100.123.199.100"  # Your Tailscale server IP
BACKEND_PORT="8000"
FRONTEND_PORT="3000"
POSTGRES_PORT="5433"
REDIS_PORT="6380"

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

# Check if we're on the Tailscale server
check_tailscale_server() {
    log_info "Checking if we're on the Tailscale server..."
    
    # Check if we can reach the Tailscale IP
    if ping -c 1 $TAILSCALE_IP > /dev/null 2>&1; then
        log_success "Tailscale connectivity confirmed"
    else
        log_warning "Cannot ping $TAILSCALE_IP - make sure you're on the Tailscale server"
    fi
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    
}

# Create production environment file
create_production_env() {
    log_info "Creating production environment configuration..."
    
    cat > .env << EOF
# Production Environment Variables for Tailscale Server

# Database Configuration
POSTGRES_PASSWORD=healthup_secure_password_$(openssl rand -hex 8)

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=20160
REFRESH_TOKEN_EXPIRE_DAYS=30

# Cookie Configuration for Tailscale (HTTP)
COOKIE_SECURE=false
COOKIE_DOMAIN=
COOKIE_SAMESITE=lax

# Redis
REDIS_URL=redis://redis:6379

# OpenAI API (set your key)
OPENAI_API_KEY=your-openai-api-key-here

# API Configuration
API_URL=http://$TAILSCALE_IP:$BACKEND_PORT

# CORS Configuration for Tailscale
CORS_ORIGINS=http://$TAILSCALE_IP:$FRONTEND_PORT

# Database
DATABASE_URL=postgresql://healthup:healthup@postgres/healthup

# App Settings
ENVIRONMENT=production

# MCP Server Configuration
MCP_TIMEOUT=30

# Frontend URL
VITE_API_URL=http://$TAILSCALE_IP:$BACKEND_PORT
EOF

    log_success "Production environment file created"
}

# Update docker-compose for Tailscale
update_docker_compose() {
    log_info "Updating docker-compose.yml for Tailscale deployment..."
    
    # Create a backup
    cp docker-compose.yml docker-compose.yml.backup
    
    # Update the docker-compose.yml with Tailscale configuration
    sed -i "s/CORS_ORIGINS=.*/CORS_ORIGINS=http:\/\/$TAILSCALE_IP:$FRONTEND_PORT/" docker-compose.yml
    sed -i "s/VITE_API_URL=.*/VITE_API_URL=http:\/\/$TAILSCALE_IP:$BACKEND_PORT/" docker-compose.yml
    
    log_success "Docker Compose updated for Tailscale"
}

# Create admin user
create_admin_user() {
    log_info "Creating admin user..."
    
    # Wait for backend to be ready
    log_info "Waiting for backend to be ready..."
    for i in {1..60}; do
        if curl -s --connect-timeout 5 "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
            log_success "Backend is ready"
            break
        fi
        if [ $i -eq 60 ]; then
            log_warning "Backend may not be fully ready, but continuing..."
        fi
        sleep 3
    done
    
    # Create admin user
    log_info "Attempting to create admin user..."
    ADMIN_RESPONSE=$(curl -s --connect-timeout 10 -X POST "http://localhost:$BACKEND_PORT/auth/register" \
        -H "Content-Type: application/json" \
        -d '{"email":"admin@admin.com","password":"123456"}' 2>/dev/null || echo "Connection failed")
    
    if echo "$ADMIN_RESPONSE" | grep -q "User registered successfully\|Email already registered"; then
        log_success "Admin user creation successful"
    else
        log_warning "Admin user creation may have failed: $ADMIN_RESPONSE"
        log_info "User may already exist or backend is still starting up"
    fi
    
    log_success "Admin user created (admin@admin.com / 123456)"
}

# Test session management
test_session_management() {
    log_info "Testing session management and cookies..."
    
    # Test login and cookie setting
    log_info "Testing login with admin credentials..."
    
    # Login and save cookies
    LOGIN_RESPONSE=$(curl -s --connect-timeout 10 -X POST "http://localhost:$BACKEND_PORT/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"admin@admin.com","password":"123456"}' \
        -c test_cookies.txt 2>/dev/null || echo "Connection failed")
    
    if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
        log_success "Login successful - cookies set"
        
        # Check if cookies were properly set
        if [ -f test_cookies.txt ]; then
            COOKIE_COUNT=$(grep -c "access_token\|refresh_token" test_cookies.txt || echo "0")
            if [ "$COOKIE_COUNT" -ge 2 ]; then
                log_success "Authentication cookies properly set ($COOKIE_COUNT cookies)"
                log_info "Cookie contents:"
                cat test_cookies.txt | grep -E "(access_token|refresh_token)" | head -2
            else
                log_error "Authentication cookies not set properly"
                return 1
            fi
        fi
        
        # Test authenticated endpoint access
        log_info "Testing authenticated endpoint access..."
        ME_RESPONSE=$(curl -s -X GET "http://localhost:$BACKEND_PORT/auth/me" \
            -b test_cookies.txt \
            -H "Content-Type: application/json")
        
        if echo "$ME_RESPONSE" | grep -q "admin@admin.com"; then
            log_success "Authenticated endpoint access successful"
        else
            log_error "Authenticated endpoint access failed"
            return 1
        fi
        
        # Test token refresh
        log_info "Testing token refresh..."
        REFRESH_RESPONSE=$(curl -s -X POST "http://localhost:$BACKEND_PORT/auth/refresh" \
            -b test_cookies.txt \
            -H "Content-Type: application/json" \
            -c test_cookies_refreshed.txt)
        
        if echo "$REFRESH_RESPONSE" | grep -q "access_token"; then
            log_success "Token refresh successful"
        else
            log_error "Token refresh failed"
            return 1
        fi
        
        # Test logout
        log_info "Testing logout..."
        LOGOUT_RESPONSE=$(curl -s -X POST "http://localhost:$BACKEND_PORT/auth/logout" \
            -b test_cookies_refreshed.txt \
            -H "Content-Type: application/json" \
            -c test_cookies_cleared.txt)
        
        if echo "$LOGOUT_RESPONSE" | grep -q "Logged out successfully"; then
            log_success "Logout successful"
        else
            log_error "Logout failed"
            return 1
        fi
        
        # Clean up test files
        rm -f test_cookies.txt test_cookies_refreshed.txt test_cookies_cleared.txt
        
    else
        log_error "Login failed: $LOGIN_RESPONSE"
        return 1
    fi
}

# Main deployment function
deploy() {
    log_info "Starting HealthUp deployment on Tailscale server..."
    
    # Check prerequisites
    check_tailscale_server
    
    # Create production environment
    create_production_env
    
    # Update docker-compose
    update_docker_compose
    
    # Stop any existing containers
    log_info "Stopping existing containers..."
    docker compose down || true
    
    # Build and start services
    log_info "Building and starting services..."
    docker compose up -d --build
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Create admin user
    create_admin_user
    
    # Test session management
    if test_session_management; then
        log_success "Session management tests passed!"
    else
        log_error "Session management tests failed!"
        exit 1
    fi
    
    # Display access information
    echo
    log_success "=========================================="
    log_success "HealthUp deployed successfully!"
    log_success "=========================================="
    echo
    log_info "Access URLs:"
    log_info "Frontend: http://$TAILSCALE_IP:$FRONTEND_PORT"
    log_info "Backend API: http://$TAILSCALE_IP:$BACKEND_PORT"
    log_info "Health Check: http://$TAILSCALE_IP:$BACKEND_PORT/health"
    echo
    log_info "Admin Credentials:"
    log_info "Email: admin@admin.com"
    log_info "Password: 123456"
    echo
    log_info "Session Management:"
    log_info "- 2-week login sessions with automatic refresh"
    log_info "- httpOnly cookies for security"
    log_info "- Automatic token refresh on expiry"
    echo
    log_info "To check logs: docker compose logs -f"
    log_info "To stop: docker compose down"
    log_info "To restart: docker compose restart"
}

# Check if script is run with arguments
case "${1:-}" in
    "test")
        log_info "Running session management tests only..."
        test_session_management
        ;;
    "stop")
        log_info "Stopping HealthUp services..."
        docker compose down
        ;;
    "restart")
        log_info "Restarting HealthUp services..."
        docker compose restart
        ;;
    "logs")
        log_info "Showing HealthUp logs..."
        docker compose logs -f
        ;;
    "help"|"-h"|"--help")
        echo "HealthUp Tailscale Deployment Script"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  (no args)  Deploy HealthUp on Tailscale server"
        echo "  test       Test session management and cookies"
        echo "  stop       Stop HealthUp services"
        echo "  restart    Restart HealthUp services"
        echo "  logs       Show service logs"
        echo "  help       Show this help message"
        ;;
    *)
        deploy
        ;;
esac 