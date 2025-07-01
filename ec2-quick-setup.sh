#!/bin/bash

echo "🚀 HealthUp Quick EC2 Setup"
echo "============================"

# Get EC2 public IP
EC2_PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || curl -s http://checkip.amazonaws.com/)

echo "📍 EC2 Public IP: $EC2_PUBLIC_IP"
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
docker compose up -d

echo "⏳ Waiting for services to start..."
sleep 30

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