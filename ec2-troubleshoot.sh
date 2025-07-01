#!/bin/bash

echo "🔧 HealthUp EC2 Troubleshooting"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Docker status
print_status "Checking Docker status..."
if docker info > /dev/null 2>&1; then
    print_success "Docker is running"
else
    print_error "Docker is not running"
    echo "Try: sudo systemctl start docker"
    exit 1
fi

# Check Docker Compose
print_status "Checking Docker Compose..."
if command -v docker compose &> /dev/null; then
    print_success "Docker Compose is available"
else
    print_error "Docker Compose not found"
    echo "Try: sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose"
    exit 1
fi

# Check if .env exists
print_status "Checking environment file..."
if [ -f ".env" ]; then
    print_success ".env file exists"
    if grep -q "your-gemini-api-key-here" .env; then
        print_warning "Please update your Gemini API key in .env file"
    fi
else
    print_error ".env file not found"
    echo "Run: ./ec2-quick-setup.sh"
    exit 1
fi

# Check service status
print_status "Checking service status..."
if docker compose ps | grep -q "Up"; then
    print_success "Some services are running"
    docker compose ps
else
    print_warning "No services are running"
fi

# Check for build errors
print_status "Checking for build errors..."
if docker compose logs --tail=50 | grep -i "error\|failed\|exit"; then
    print_error "Found errors in logs:"
    docker compose logs --tail=20 | grep -i "error\|failed\|exit"
else
    print_success "No obvious errors in recent logs"
fi

# Check frontend build specifically
print_status "Checking frontend build..."
if docker compose logs frontend | grep -i "build\|error\|failed"; then
    print_warning "Frontend build issues detected:"
    docker compose logs frontend | grep -i "build\|error\|failed" | tail -10
fi

# Check backend build
print_status "Checking backend build..."
if docker compose logs backend | grep -i "error\|failed"; then
    print_warning "Backend issues detected:"
    docker compose logs backend | grep -i "error\|failed" | tail -10
fi

# Check database
print_status "Checking database..."
if docker compose logs postgres | grep -i "error\|failed"; then
    print_warning "Database issues detected:"
    docker compose logs postgres | grep -i "error\|failed" | tail -10
fi

# Check ports
print_status "Checking port availability..."
for port in 3000 8000 5433 6380; do
    if netstat -tuln | grep ":$port "; then
        print_success "Port $port is in use"
    else
        print_warning "Port $port is not in use"
    fi
done

# Check disk space
print_status "Checking disk space..."
df -h | grep -E "(Filesystem|/dev/)"

# Check memory
print_status "Checking memory usage..."
free -h

# Provide solutions
echo ""
echo "🔧 Common Solutions:"
echo "1. If frontend build fails:"
echo "   docker compose logs frontend"
echo "   docker compose build frontend --no-cache"
echo ""
echo "2. If backend build fails:"
echo "   docker compose logs backend"
echo "   docker compose build backend --no-cache"
echo ""
echo "3. If database fails:"
echo "   docker compose logs postgres"
echo "   docker compose restart postgres"
echo ""
echo "4. Restart all services:"
echo "   docker compose down"
echo "   docker compose up -d --build"
echo ""
echo "5. Check all logs:"
echo "   docker compose logs -f" 