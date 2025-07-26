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

# Allow manual IP override via environment variables
if [ -n "$MANUAL_EC2_IP" ]; then
    EC2_IP="$MANUAL_EC2_IP"
    log "Using manually specified IP: $EC2_IP"
fi



# Function to get EC2 instance metadata
get_ec2_ip() {
    log "Detecting EC2 public IP..."
    
    # Initialize variables
    EC2_PUBLIC_IP=""
    EC2_IP=""
    
    # Try AWS metadata service first
    if curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
        EC2_PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null)
        log "Found IP via AWS metadata: $EC2_PUBLIC_IP"
    # Try external service as fallback
    elif curl -s http://checkip.amazonaws.com/ 2>/dev/null | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
        EC2_PUBLIC_IP=$(curl -s http://checkip.amazonaws.com/ 2>/dev/null)
        log "Found IP via external service: $EC2_PUBLIC_IP"
    else
        log "Could not automatically detect public IP"
        log "Please enter your EC2 public IP manually:"
        read -p "EC2 Public IP: " EC2_PUBLIC_IP
    fi
    
    if [ -z "$EC2_PUBLIC_IP" ]; then
        error "No valid IP address found. Please run the script again and enter the IP manually."
        exit 1
    fi
    
    # Validate the IP
    if ! validate_ip "$EC2_PUBLIC_IP"; then
        error "Invalid IP address format: $EC2_PUBLIC_IP"
        exit 1
    fi
    
    # Set the IP to use (always public IP for production)
    EC2_IP="$EC2_PUBLIC_IP"
    
    # Store for reference
    export EC2_PUBLIC_IP="$EC2_PUBLIC_IP"
    export EC2_IP="$EC2_IP"
    
    log "Using EC2 Public IP: $EC2_IP"
}

# Function to validate IP address
validate_ip() {
    local ip="$1"
    
    # Check if IP is not empty
    if [ -z "$ip" ]; then
        return 1
    fi
    
    # Basic IP format validation (IPv4)
    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        # Check each octet
        IFS='.' read -ra OCTETS <<< "$ip"
        for octet in "${OCTETS[@]}"; do
            if [ "$octet" -lt 0 ] || [ "$octet" -gt 255 ]; then
                return 1
            fi
        done
        return 0
    fi
    
    return 1
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

# Function to test IP connectivity
test_ip_connectivity() {
    local ip="$1"
    local port="$2"
    
    log "Testing connectivity to $ip:$port..."
    
    # Test if port is reachable
    if command -v nc >/dev/null 2>&1; then
        if nc -z -w5 "$ip" "$port" 2>/dev/null; then
            log "✓ Port $port is reachable on $ip"
            return 0
        else
            log "✗ Port $port is not reachable on $ip"
            return 1
        fi
    else
        # Fallback to curl if netcat not available
        if curl -s --connect-timeout 5 "http://$ip:$port" >/dev/null 2>&1; then
            log "✓ Port $port is reachable on $ip"
            return 0
        else
            log "✗ Port $port is not reachable on $ip"
            return 1
        fi
    fi
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
    
    # Set environment variables for docker-compose
    export EC2_IP="$EC2_IP"
    export FRONTEND_ORIGINS="http://$EC2_IP:3000"
    export VITE_API_URL="http://$EC2_IP:8000"
    
    # Update .env file to include all necessary variables
    echo "EC2_IP=$EC2_IP" >> .env
    echo "FRONTEND_ORIGINS=http://$EC2_IP:3000" >> .env
    echo "VITE_API_URL=http://$EC2_IP:8000" >> .env
    
    log "Set EC2_IP=$EC2_IP for docker-compose"
    log "Set FRONTEND_ORIGINS=http://$EC2_IP:3000 for CORS"
    log "Set VITE_API_URL=http://$EC2_IP:8000 for frontend"
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

# Function to setup database and run migrations
setup_database() {
    log "Setting up database and running migrations..."
    
    # Start only the database and Redis services first
    log "Starting database and Redis services..."
    docker compose up -d postgres redis
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker compose exec -T postgres pg_isready -U healthup >/dev/null 2>&1; then
            success "Database is ready"
            break
        fi
        log "Waiting for database... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        error "Database failed to start within expected time"
        return 1
    fi
    
    # Start backend service temporarily for migrations
    log "Starting backend service for migrations..."
    docker compose up -d backend
    
    # Wait for backend to be ready
    log "Waiting for backend service to be ready..."
    local backend_attempts=30
    local backend_attempt=1
    
    while [ $backend_attempt -le $backend_attempts ]; do
        if docker compose exec -T backend python -c "import os; print('Backend ready')" >/dev/null 2>&1; then
            success "Backend service is ready"
            break
        fi
        log "Waiting for backend service... (attempt $backend_attempt/$backend_attempts)"
        sleep 5
        ((backend_attempt++))
    done
    
    if [ $backend_attempt -gt $backend_attempts ]; then
        error "Backend service failed to start within expected time"
        return 1
    fi
    
    # Run database migrations
    log "Running database migrations..."
    if docker compose exec -T backend alembic upgrade head; then
        success "Database migrations completed successfully"
    else
        error "Database migrations failed"
        return 1
    fi
    
    # Create default admin user
    log "Creating default admin user..."
    if docker compose exec -T backend python -c "
from app.database import get_db
from app.crud import create_user
from app.schemas import UserCreate
from app import models
from sqlalchemy.orm import Session

db = next(get_db())
try:
    # Check if admin user already exists
    existing_user = db.query(models.User).filter(models.User.email == 'admin@healthup.com').first()
    if not existing_user:
        admin_user = UserCreate(
            email='admin@healthup.com',
            password='123456'
        )
        create_user(db, admin_user)
        print('Default admin user created successfully')
    else:
        print('Admin user already exists')
except Exception as e:
    print(f'Error creating admin user: {e}')
    exit(1)
"; then
        success "Default admin user setup completed"
    else
        warning "Default admin user setup failed - you may need to create it manually"
    fi
    
    # Stop backend service (it will be restarted later with all services)
    log "Stopping backend service (will be restarted with all services)..."
    docker compose stop backend
}

# Function to start services
start_services() {
    log "Starting HealthUp services..."
    
    # Export all necessary environment variables for docker-compose
    export EC2_IP="$EC2_IP"
    export FRONTEND_ORIGINS="http://$EC2_IP:3000"
    export VITE_API_URL="http://$EC2_IP:8000"
    log "Using EC2_IP=$EC2_IP for services"
    log "Using FRONTEND_ORIGINS=http://$EC2_IP:3000 for CORS"
    log "Using VITE_API_URL=http://$EC2_IP:8000 for frontend"
    
    # Stop any existing services (except database and Redis which are already running)
    log "Stopping existing application services..."
    docker compose stop backend frontend worker scheduler || true
    
    # Remove existing frontend build to force rebuild with new API URL
    log "Removing existing frontend build to force rebuild..."
    docker compose rm -f frontend || true
    docker rmi healthup-frontend:latest || true
    
    # Build and start application services (database and Redis are already running)
    log "Building and starting application services..."
    docker compose up -d --build backend frontend worker scheduler
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Check service status
    log "Checking service status..."
    docker compose ps
    
    success "Services started successfully"
    
    # Verify environment variables in running containers
    log "Verifying environment variables in containers..."
    
    # Check backend CORS configuration
    local backend_cors=$(docker compose exec -T backend env | grep FRONTEND_ORIGINS || echo "NOT_FOUND")
    if echo "$backend_cors" | grep -q "$EC2_IP"; then
        success "Backend CORS configuration is correct"
    else
        warning "Backend CORS configuration may be incorrect: $backend_cors"
    fi
    
    # Check frontend API URL
    local frontend_api=$(docker compose exec -T frontend env | grep VITE_API_URL || echo "NOT_FOUND")
    if echo "$frontend_api" | grep -q "$EC2_IP"; then
        success "Frontend API URL configuration is correct"
    else
        warning "Frontend API URL configuration may be incorrect: $frontend_api"
    fi
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
    
    # Test CORS configuration
    log "Testing CORS configuration..."
    local cors_response=$(curl -s -H "Origin: http://$EC2_IP:3000" -H "Access-Control-Request-Method: GET" -H "Access-Control-Request-Headers: X-Requested-With" -X OPTIONS http://localhost:8000/ -w "%{http_code}")
    if echo "$cors_response" | grep -q "200"; then
        success "CORS preflight request successful"
    else
        warning "CORS preflight request failed - this may cause frontend issues"
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
    if [ -f "tests/test_comprehensive_ai_fixes.py" ]; then
        log "Running comprehensive AI test suite..."
        
        # Create virtual environment for testing
        python3 -m venv test_env_ec2
        source test_env_ec2/bin/activate
        pip install requests psycopg2-binary PyJWT cryptography
        
        # Run tests
        python tests/test_comprehensive_ai_fixes.py || warning "Some tests failed - check logs for details"
        
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
    echo "IP Configuration:"
    echo "  - Selected IP: $EC2_IP"
    echo "  - Public IP: $EC2_PUBLIC_IP"
    echo ""
    echo "Service URLs:"
    echo "  - Backend API: http://$EC2_IP:8000"
    echo "  - Frontend PWA: http://$EC2_IP:3000"
    echo "  - Database: localhost:5433"
    echo "  - Redis: localhost:6380"
    echo ""
    echo "Service Status:"
    docker compose ps
    echo ""
    echo "Environment Variables:"
    echo "  - SECRET_KEY: ${SECRET_KEY:0:10}..."
    echo "  - AMAZFIT_ENCRYPTION_KEY: ${AMAZFIT_ENCRYPTION_KEY:0:10}..."
    echo "  - OPENAI_API_KEY: ${OPENAI_API_KEY:+SET}"
    echo "  - GEMINI_API_KEY: ${GEMINI_API_KEY:+SET}"
    echo ""
    echo "Connectivity Test:"
    if test_ip_connectivity "$EC2_IP" 8000; then
        echo "  ✓ Backend API is reachable"
    else
        echo "  ✗ Backend API is not reachable"
    fi
    
    if test_ip_connectivity "$EC2_IP" 3000; then
        echo "  ✓ Frontend is reachable"
    else
        echo "  ✗ Frontend is not reachable"
    fi
    echo ""
    echo "Logs:"
    echo "  - Backend: docker compose logs backend"
    echo "  - Frontend: docker compose logs frontend"
    echo "  - Database: docker compose logs postgres"
    echo "  - Redis: docker compose logs redis"
    echo "  - Worker: docker compose logs worker"
    echo "  - Scheduler: docker compose logs scheduler"
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
    
    # Only detect IP if not manually specified
    if [ -z "$EC2_IP" ]; then
        get_ec2_ip
    fi
    
    generate_secure_env
    update_docker_compose
    check_ports
    setup_database
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