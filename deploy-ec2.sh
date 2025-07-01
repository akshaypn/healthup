#!/bin/bash

echo "🚀 HealthUp EC2 Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if running on EC2
if [ ! -f /sys/hypervisor/uuid ] || [ "$(head -c 3 /sys/hypervisor/uuid)" != "ec2" ]; then
    print_warning "This script is designed to run on EC2 instances"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
print_status "Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_success "Docker installed successfully"
else
    print_success "Docker is already installed"
fi

# Install Docker Compose
print_status "Installing Docker Compose..."
if ! command -v docker compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    sudo ln -s /usr/local/bin/docker-compose /usr/local/bin/docker-compose
    print_success "Docker Compose installed successfully"
else
    print_success "Docker Compose is already installed"
fi

# Get EC2 public IP
EC2_PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
if [ -z "$EC2_PUBLIC_IP" ]; then
    EC2_PUBLIC_IP=$(curl -s http://checkip.amazonaws.com/)
fi

print_success "EC2 Public IP: $EC2_PUBLIC_IP"

# Create .env file from example
if [ ! -f ".env" ]; then
    print_status "Creating .env file from example..."
    cp env.production.example .env
    
    # Generate secure passwords
    SECURE_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
    
    # Update .env with actual values
    sed -i "s/your-secure-postgres-password-here/$SECURE_PASSWORD/g" .env
    sed -i "s/your-super-secret-key-change-this-in-production/$SECRET_KEY/g" .env
    sed -i "s/your-ec2-public-ip/$EC2_PUBLIC_IP/g" .env
    
    print_warning "Please edit .env and add your Google Gemini API key:"
    print_warning "  nano .env"
    print_warning "  Set GEMINI_API_KEY=your-actual-api-key"
    
    read -p "Press Enter after you've updated the .env file..."
else
    print_success ".env file already exists"
fi

# Configure firewall (if using UFW)
if command -v ufw &> /dev/null; then
    print_status "Configuring firewall..."
    sudo ufw allow 22/tcp    # SSH
    sudo ufw allow 80/tcp    # HTTP
    sudo ufw allow 443/tcp   # HTTPS
    sudo ufw allow 3000/tcp  # Frontend
    sudo ufw allow 8000/tcp  # Backend API
    sudo ufw --force enable
    print_success "Firewall configured"
fi

# Start services
print_status "Starting HealthUp services..."
docker compose up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check service status
if docker compose ps | grep -q "Up"; then
    print_success "All services are running!"
    echo ""
    echo "🌐 HealthUp is now accessible at:"
    echo "   Frontend: http://$EC2_PUBLIC_IP:3000"
    echo "   Backend API: http://$EC2_PUBLIC_IP:8000"
    echo "   API Documentation: http://$EC2_PUBLIC_IP:8000/docs"
    echo ""
    echo "📱 Mobile Access:"
    echo "   Open http://$EC2_PUBLIC_IP:3000 on your mobile device"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: docker compose logs -f"
    echo "   Stop services: docker compose down"
    echo "   Restart services: docker compose restart"
    echo "   Update application: git pull && docker compose up -d --build"
    echo ""
    echo "💡 Next Steps:"
    echo "   1. Register a new account at http://$EC2_PUBLIC_IP:3000"
    echo "   2. Start logging your health data"
    echo "   3. Consider setting up a domain name and SSL certificate"
    echo "   4. Set up automated backups for the database"
else
    print_error "Some services failed to start"
    print_error "Check logs with: docker compose logs"
    exit 1
fi 