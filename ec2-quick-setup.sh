#!/bin/bash

echo "🚀 HealthUp Quick EC2 Setup"
echo "============================"

# Get EC2 public IP - try multiple methods
echo "🔍 Detecting EC2 public IP..."
EC2_PUBLIC_IP=""

# Try AWS metadata service first
if curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
    EC2_PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null)
    echo "✅ Found IP via AWS metadata: $EC2_PUBLIC_IP"
# Try external service as fallback
elif curl -s http://checkip.amazonaws.com/ 2>/dev/null | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
    EC2_PUBLIC_IP=$(curl -s http://checkip.amazonaws.com/ 2>/dev/null)
    echo "✅ Found IP via external service: $EC2_PUBLIC_IP"
else
    echo "⚠️  Could not automatically detect public IP"
    echo "   Please enter your EC2 public IP manually:"
    read -p "   EC2 Public IP: " EC2_PUBLIC_IP
fi

if [ -z "$EC2_PUBLIC_IP" ]; then
    echo "❌ No valid IP address found. Please run the script again and enter the IP manually."
    exit 1
fi

echo "📍 Using EC2 Public IP: $EC2_PUBLIC_IP"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Production Environment Variables
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
GEMINI_API_KEY=your-gemini-api-key-here
API_URL=http://$EC2_PUBLIC_IP:8000
CORS_ORIGINS=http://$EC2_PUBLIC_IP:3000
EOF
    echo "✅ .env file created"
    echo "⚠️  Please edit .env and add your Google Gemini API key"
    echo "   nano .env"
    echo ""
    read -p "Press Enter after updating the .env file..."
fi

# Start services
echo "🐳 Starting HealthUp services..."
echo "🔨 Building Docker images (this may take a few minutes)..."
docker compose up -d --build

echo "⏳ Waiting for services to start..."
sleep 45

# Check status
if docker compose ps | grep -q "Up"; then
    echo ""
    echo "✅ HealthUp is now running!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Frontend: http://$EC2_PUBLIC_IP:3000"
    echo "   Backend: http://$EC2_PUBLIC_IP:8000"
    echo "   API Docs: http://$EC2_PUBLIC_IP:8000/docs"
    echo ""
    echo "📱 Mobile Access:"
    echo "   Open http://$EC2_PUBLIC_IP:3000 on your phone"
    echo ""
    echo "🔧 Quick Commands:"
    echo "   View logs: docker compose logs -f"
    echo "   Stop: docker compose down"
    echo "   Restart: docker compose restart"
else
    echo "❌ Services failed to start"
    echo "Check logs: docker compose logs"
fi 