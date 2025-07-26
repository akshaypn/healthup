#!/bin/bash

# Apply current configuration to running services
# This script updates the config.js and restarts services with new environment variables

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=================================="
echo "HealthUp Configuration Apply"
echo "=================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    error ".env file not found. Please run the production setup first."
    exit 1
fi

# Source the environment variables
source .env

if [ -z "$EC2_IP" ]; then
    error "EC2_IP not found in .env file"
    exit 1
fi

log "Using IP: $EC2_IP"

# Update config.js with current IP
log "Updating frontend config.js..."
cat > frontend/public/config.js << EOF
// Runtime configuration for HealthUp
// Generated on $(date)

window.HEALTHUP_CONFIG = {
  API_URL: 'http://$EC2_IP:8000'
};
EOF

success "Updated config.js with IP: $EC2_IP"

# Update index.html preconnect
log "Updating index.html preconnect..."
sed -i "s|href=\"http://[0-9.]*:8000\"|href=\"http://$EC2_IP:8000\"|g" frontend/index.html

success "Updated index.html preconnect"

# Restart services to pick up new environment variables
log "Restarting services..."
docker compose restart frontend backend

success "Services restarted"

# Wait for services to be ready
log "Waiting for services to be ready..."
sleep 10

# Test connectivity
log "Testing connectivity..."
if curl -s http://localhost:8000/ >/dev/null; then
    success "Backend is responding"
else
    warning "Backend is not responding"
fi

if curl -s http://localhost:3000/ >/dev/null; then
    success "Frontend is responding"
else
    warning "Frontend is not responding"
fi

echo ""
echo "=================================="
success "Configuration applied successfully!"
echo "=================================="
echo ""
echo "Access URLs:"
echo "  Frontend: http://$EC2_IP:3000"
echo "  Backend: http://$EC2_IP:8000"
echo ""
echo "If you're still seeing CORS errors, try:"
echo "  docker compose logs backend"
echo "  docker compose logs frontend" 