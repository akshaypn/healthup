#!/bin/bash

# Quick Tailscale Server Setup Script
# This script installs prerequisites and deploys HealthUp on your Tailscale server

set -e

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

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_error "Please do not run this script as root"
        log_info "Run as a regular user with sudo privileges"
        exit 1
    fi
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install Docker
    if ! command -v docker &> /dev/null; then
        log_info "Installing Docker..."
        sudo apt install -y docker.io
        sudo systemctl enable docker
        sudo systemctl start docker
        sudo usermod -aG docker $USER
        log_success "Docker installed"
    else
        log_success "Docker already installed"
    fi
    
    
    # Install other dependencies
    log_info "Installing additional dependencies..."
    sudo apt install -y git curl jq openssl
    
    log_success "All dependencies installed"
}

# Check Tailscale connectivity
check_tailscale() {
    log_info "Checking Tailscale connectivity..."
    
    if ! command -v tailscale &> /dev/null; then
        log_warning "Tailscale not installed. Please install Tailscale first."
        log_info "Visit: https://tailscale.com/download"
        return 1
    fi
    
    # Check Tailscale status
    TAILSCALE_STATUS=$(sudo tailscale status 2>/dev/null || echo "offline")
    
    if echo "$TAILSCALE_STATUS" | grep -q "100.123.199.100"; then
        log_success "Tailscale is running and server IP found"
        return 0
    else
        log_warning "Tailscale may not be properly configured"
        log_info "Current status:"
        echo "$TAILSCALE_STATUS"
        return 1
    fi
}

# Clone and setup repository
setup_repository() {
    log_info "Setting up HealthUp repository..."
    
    # Check if we're in the right directory
    if [ -f "docker-compose.yml" ] && [ -d "backend" ] && [ -d "frontend" ]; then
        log_success "HealthUp repository already present"
    else
        log_error "HealthUp repository not found in current directory"
        log_info "Please run this script from the HealthUp project directory"
        exit 1
    fi
    
    # Make scripts executable
    chmod +x deploy-tailscale.sh
    chmod +x test-tailscale-session.sh
    
    log_success "Repository setup complete"
}

# Deploy application
deploy_application() {
    log_info "Deploying HealthUp application..."
    
    # Run deployment script
    if ./deploy-tailscale.sh; then
        log_success "Application deployed successfully"
        return 0
    else
        log_error "Application deployment failed"
        return 1
    fi
}

# Test deployment
test_deployment() {
    log_info "Testing deployment..."
    
    # Wait a moment for services to be fully ready
    sleep 10
    
    # Run comprehensive tests
    if ./test-tailscale-session.sh; then
        log_success "All tests passed"
        return 0
    else
        log_warning "Some tests failed - check logs for details"
        return 1
    fi
}

# Display final information
show_final_info() {
    echo
    log_success "=========================================="
    log_success "HealthUp Tailscale Setup Complete!"
    log_success "=========================================="
    echo
    log_info "Access URLs:"
    log_info "Frontend: http://100.123.199.100:3000"
    log_info "Backend: http://100.123.199.100:8000"
    log_info "Health Check: http://100.123.199.100:8000/health"
    echo
    log_info "Admin Credentials:"
    log_info "Email: admin@admin.com"
    log_info "Password: 123456"
    echo
    log_info "Management Commands:"
    log_info "  Check status: docker compose ps"
    log_info "  View logs: docker compose logs -f"
    log_info "  Restart: docker compose restart"
    log_info "  Stop: docker compose down"
    echo
    log_info "Testing Commands:"
    log_info "  Test sessions: ./test-tailscale-session.sh"
    log_info "  Test login: curl -X POST http://100.123.199.100:8000/auth/login \\"
    log_info "    -H 'Content-Type: application/json' \\"
    log_info "    -d '{\"email\":\"admin@admin.com\",\"password\":\"123456\"}'"
    echo
    log_info "Documentation:"
    log_info "  Full guide: TAILSCALE_DEPLOYMENT_GUIDE.md"
    log_info "  Session management: SESSION_MANAGEMENT_GUIDE.md"
}

# Main setup function
main_setup() {
    log_info "Starting HealthUp Tailscale server setup..."
    
    # Check if not running as root
    check_root
    
    # Install dependencies
    install_dependencies
    
    # Check Tailscale
    if ! check_tailscale; then
        log_warning "Tailscale check failed, but continuing..."
    fi
    
    # Setup repository
    setup_repository
    
    # Deploy application
    if deploy_application; then
        # Test deployment
        test_deployment
        
        # Show final information
        show_final_info
    else
        log_error "Setup failed during deployment"
        log_info "Check the logs above for details"
        log_info "You can try running: ./deploy-tailscale.sh"
        exit 1
    fi
}

# Check if script is run with arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "HealthUp Tailscale Quick Setup Script"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  (no args)  Run complete setup"
        echo "  help       Show this help message"
        echo
        echo "This script will:"
        echo "  1. Install Docker and dependencies"
        echo "  2. Check Tailscale connectivity"
        echo "  3. Setup HealthUp repository"
        echo "  4. Deploy the application"
        echo "  5. Test session management"
        echo
        echo "Prerequisites:"
        echo "  - Ubuntu/Debian system"
        echo "  - Tailscale installed and configured"
        echo "  - HealthUp repository in current directory"
        ;;
    *)
        main_setup
        ;;
esac 