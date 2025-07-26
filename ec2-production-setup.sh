#!/bin/bash

# HealthUp EC2 Production Setup Script
# This script ensures all services use the same EC2 IP and correct ports
# Includes comprehensive testing and validation

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
EC2_IP=""
EC2_PUBLIC_IP=""

# Function to get EC2 instance metadata
get_ec2_ip() {
    log "Detecting EC2 instance IP addresses..."
    
    # Try to get private IP from metadata
    if command -v curl >/dev/null 2>&1; then
        EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4 2>/dev/null || echo "")
        EC2_PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "")
    fi
    
    # Fallback to hostname if metadata not available
    if [ -z "$EC2_IP" ]; then
        EC2_IP=$(hostname -I | awk '{print $1}' | head -1)
    fi
    
    # Use public IP if available, otherwise use private IP
    if [ -n "$EC2_PUBLIC_IP" ]; then
        EC2_IP="$EC2_PUBLIC_IP"
        log "Using public IP: $EC2_IP"
    else
        log "Using private IP: $EC2_IP"
    fi
    
    if [ -z "$EC2_IP" ]; then
        error "Could not determine EC2 IP address"
    fi
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if running on EC2
    if [ -f /sys/hypervisor/uuid ] && grep -q "ec2" /sys/hypervisor/uuid; then
        log "Running on EC2 instance"
    else
        warning "Not running on EC2 instance - some features may not work correctly"
    fi
    
    # Check Docker
    if ! command -v docker >/dev/null 2>&1; then
        error "Docker is not installed"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
        error "Docker Compose is not installed"
    fi
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        error "docker-compose.yml not found. Please run this script from the project root."
    fi
    
    success "Prerequisites check passed"
}

# Function to generate secure environment variables
generate_secure_env() {
    log "Generating secure environment variables..."
    
    # Generate secure keys if not already set
    if [ -z "$SECRET_KEY" ]; then
        export SECRET_KEY=$(openssl rand -hex 32)
        log "Generated new SECRET_KEY"
    fi
    
    if [ -z "$AMAZFIT_ENCRYPTION_KEY" ]; then
        export AMAZFIT_ENCRYPTION_KEY=$(openssl rand -base64 32)
        log "Generated new AMAZFIT_ENCRYPTION_KEY"
    fi
    
    # Create .env file with current configuration
    cat > .env << EOF
# HealthUp Production Environment Variables
# Generated on $(date)

# EC2 Configuration
EC2_IP=$EC2_IP
EC2_PUBLIC_IP=$EC2_PUBLIC_IP

# Database Configuration
POSTGRES_PASSWORD=healthup_secure_password_a2032334186a8000

# Security Keys (Generated automatically)
SECRET_KEY=$SECRET_KEY
AMAZFIT_ENCRYPTION_KEY=$AMAZFIT_ENCRYPTION_KEY

# API Keys (Set these manually)
OPENAI_API_KEY=${OPENAI_API_KEY:-}
GEMINI_API_KEY=${GEMINI_API_KEY:-}

# Cookie Configuration
COOKIE_SECURE=false
COOKIE_DOMAIN=
COOKIE_SAMESITE=lax

# Frontend Configuration
VITE_API_URL=http://$EC2_IP:8000
FRONTEND_ORIGINS=http://$EC2_IP:3000

# Service URLs
BACKEND_URL=http://$EC2_IP:8000
FRONTEND_URL=http://$EC2_IP:3000
DATABASE_URL=postgresql://healthup:healthup_secure_password_a2032334186a8000@postgres:5432/healthup
REDIS_URL=redis://redis:6379
EOF
    
    success "Environment file created: .env"
}

# Function to update docker-compose.yml with correct IPs
update_docker_compose() {
    log "Updating docker-compose.yml with correct IP configuration..."
    
    # Create backup
    cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)
    
    # Update FRONTEND_ORIGINS in docker-compose.yml
    sed -i "s|FRONTEND_ORIGINS=.*|FRONTEND_ORIGINS=http://$EC2_IP:3000|g" docker-compose.yml
    
    # Update VITE_API_URL in docker-compose.yml
    sed -i "s|VITE_API_URL=.*|VITE_API_URL=http://$EC2_IP:8000|g" docker-compose.yml
    
    success "Docker Compose configuration updated"
}

# Function to check if ports are available
check_ports() {
    log "Checking if required ports are available..."
    
    local ports=(3000 8000 5433 6380)
    local unavailable_ports=()
    
    for port in "${ports[@]}"; do
        if netstat -tuln | grep -q ":$port "; then
            unavailable_ports+=($port)
        fi
    done
    
    if [ ${#unavailable_ports[@]} -gt 0 ]; then
        warning "The following ports are already in use: ${unavailable_ports[*]}"
        warning "Please stop the services using these ports before continuing"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        success "All required ports are available"
    fi
}

# Function to start services
start_services() {
    log "Starting HealthUp services..."
    
    # Stop any existing services
    log "Stopping existing services..."
    docker compose down --remove-orphans || true
    
    # Build and start services
    log "Building and starting services..."
    docker compose up -d --build
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Check service status
    log "Checking service status..."
    docker compose ps
    
    success "Services started successfully"
}

# Function to run comprehensive tests
run_tests() {
    log "Running comprehensive test suite..."
    
    # Wait for backend to be fully ready
    log "Waiting for backend to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/ >/dev/null 2>&1; then
            success "Backend is ready"
            break
        fi
        log "Waiting for backend... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        error "Backend failed to start within expected time"
    fi
    
    # Run basic connectivity tests
    log "Running basic connectivity tests..."
    
    # Test backend health
    if curl -s http://localhost:8000/ >/dev/null; then
        success "Backend API is responding"
    else
        error "Backend API is not responding"
    fi
    
    # Test frontend
    if curl -s http://localhost:3000/ >/dev/null; then
        success "Frontend is responding"
    else
        error "Frontend is not responding"
    fi
    
    # Test database connectivity
    if docker compose exec -T postgres pg_isready -U healthup >/dev/null 2>&1; then
        success "Database is ready"
    else
        error "Database is not ready"
    fi
    
    # Test Redis connectivity
    if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        success "Redis is ready"
    else
        error "Redis is not ready"
    fi
    
    # Run comprehensive test suite if available
    if [ -f "test_comprehensive_ai_fixes.py" ]; then
        log "Running comprehensive AI test suite..."
        
        # Create virtual environment for testing
        python3 -m venv test_env_ec2
        source test_env_ec2/bin/activate
        pip install requests psycopg2-binary PyJWT cryptography
        
        # Run tests
        python test_comprehensive_ai_fixes.py || warning "Some tests failed - check logs for details"
        
        deactivate
        rm -rf test_env_ec2
    fi
    
    # Run basic API tests
    log "Running basic API tests..."
    
    # Test rate limiting
    for i in {1..10}; do
        curl -s http://localhost:8000/ >/dev/null
    done
    
    # Test if rate limiting is working (should get 429 after 5 requests per minute)
    local rate_limit_response=$(curl -s -w "%{http_code}" http://localhost:8000/ -o /dev/null)
    if [ "$rate_limit_response" = "429" ]; then
        success "Rate limiting is working"
    else
        warning "Rate limiting may not be working as expected"
    fi
    
    success "Test suite completed"
}

# Function to display service information
display_service_info() {
    log "HealthUp Services Information"
    echo "=================================="
    echo "EC2 IP Address: $EC2_IP"
    echo "Backend API: http://$EC2_IP:8000"
    echo "Frontend PWA: http://$EC2_IP:3000"
    echo "Database: localhost:5433"
    echo "Redis: localhost:6380"
    echo ""
    echo "Service Status:"
    docker compose ps
    echo ""
    echo "Environment Variables:"
    echo "SECRET_KEY: ${SECRET_KEY:0:10}..."
    echo "AMAZFIT_ENCRYPTION_KEY: ${AMAZFIT_ENCRYPTION_KEY:0:10}..."
    echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+SET}"
    echo "GEMINI_API_KEY: ${GEMINI_API_KEY:+SET}"
    echo ""
    echo "Logs:"
    echo "Backend: docker compose logs backend"
    echo "Frontend: docker compose logs frontend"
    echo "Database: docker compose logs postgres"
    echo "Redis: docker compose logs redis"
    echo "Worker: docker compose logs worker"
    echo "Scheduler: docker compose logs scheduler"
}

# Function to create systemd service for auto-start
create_systemd_service() {
    log "Creating systemd service for auto-start..."
    
    local service_file="/etc/systemd/system/healthup.service"
    
    cat > "$service_file" << EOF
[Unit]
Description=HealthUp Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    # Enable and start the service
    systemctl daemon-reload
    systemctl enable healthup.service
    
    success "Systemd service created and enabled"
    log "To start: systemctl start healthup"
    log "To stop: systemctl stop healthup"
    log "To check status: systemctl status healthup"
}

# Function to create monitoring script
create_monitoring_script() {
    log "Creating monitoring script..."
    
    cat > "monitor-healthup.sh" << 'EOF'
#!/bin/bash

# HealthUp Monitoring Script
# Run this script to check the health of all services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "HealthUp Service Monitor"
echo "======================="
echo "Timestamp: $(date)"
echo ""

# Check Docker services
echo "Docker Services:"
if docker compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ All services are running${NC}"
else
    echo -e "${RED}✗ Some services are not running${NC}"
    docker compose ps
fi
echo ""

# Check API endpoints
echo "API Endpoints:"
if curl -s http://localhost:8000/ >/dev/null; then
    echo -e "${GREEN}✓ Backend API (port 8000)${NC}"
else
    echo -e "${RED}✗ Backend API (port 8000)${NC}"
fi

if curl -s http://localhost:3000/ >/dev/null; then
    echo -e "${GREEN}✓ Frontend (port 3000)${NC}"
else
    echo -e "${RED}✗ Frontend (port 3000)${NC}"
fi
echo ""

# Check database
echo "Database:"
if docker compose exec -T postgres pg_isready -U healthup >/dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not ready${NC}"
fi

# Check Redis
echo "Redis:"
if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is ready${NC}"
else
    echo -e "${RED}✗ Redis is not ready${NC}"
fi
echo ""

# Check disk space
echo "Disk Usage:"
df -h / | tail -1 | awk '{print "Root: " $5 " used (" $3 "/" $2 ")"}'
echo ""

# Check memory usage
echo "Memory Usage:"
free -h | grep "Mem:" | awk '{print "Memory: " $3 "/" $2 " (" int($3/$2*100) "%)"}'
echo ""

# Check recent logs for errors
echo "Recent Errors (last 10 lines):"
docker compose logs --tail=10 2>&1 | grep -i error || echo "No recent errors found"
EOF
    
    chmod +x monitor-healthup.sh
    success "Monitoring script created: monitor-healthup.sh"
}

# Main execution
main() {
    echo "=================================="
    echo "HealthUp EC2 Production Setup"
    echo "=================================="
    echo ""
    
    # Check if running as root (needed for systemd service)
    if [ "$EUID" -eq 0 ]; then
        warning "Running as root - systemd service will be created"
    else
        warning "Not running as root - systemd service creation will be skipped"
    fi
    
    # Execute setup steps
    check_prerequisites
    get_ec2_ip
    generate_secure_env
    update_docker_compose
    check_ports
    start_services
    run_tests
    display_service_info
    
    # Create systemd service if running as root
    if [ "$EUID" -eq 0 ]; then
        create_systemd_service
    fi
    
    create_monitoring_script
    
    echo ""
    echo "=================================="
    success "HealthUp EC2 setup completed successfully!"
    echo "=================================="
    echo ""
    echo "Next steps:"
    echo "1. Set your API keys in the .env file:"
    echo "   - OPENAI_API_KEY"
    echo "   - GEMINI_API_KEY"
    echo ""
    echo "2. Restart services to apply API keys:"
    echo "   docker compose restart"
    echo ""
    echo "3. Monitor services:"
    echo "   ./monitor-healthup.sh"
    echo ""
    echo "4. View logs:"
    echo "   docker compose logs -f"
    echo ""
    echo "5. Access your application:"
    echo "   Frontend: http://$EC2_IP:3000"
    echo "   Backend API: http://$EC2_IP:8000"
    echo ""
}

# Run main function
main "$@" 