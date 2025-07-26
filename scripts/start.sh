#!/bin/bash

echo "🚀 Starting HealthUp - Personal Health Tracker"
echo "================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env files exist
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating backend environment file..."
    cp backend/env.example backend/.env
    echo "⚠️  Please edit backend/.env and add your Google Gemini API key"
fi

if [ ! -f "frontend/.env" ]; then
    echo "📝 Creating frontend environment file..."
    cp frontend/env.example frontend/.env
    echo "⚠️  Please edit frontend/.env and add your Google Gemini API key"
fi

# Detect Tailscale IP
TAILSCALE_IP=""
if command -v tailscale &> /dev/null; then
    TAILSCALE_IP=$(tailscale ip -4 2>/dev/null | head -n1)
    if [ -n "$TAILSCALE_IP" ]; then
        echo "🌐 Detected Tailscale IP: $TAILSCALE_IP"
        export API_URL="http://$TAILSCALE_IP:8000"
    else
        echo "⚠️  Tailscale detected but no IP found"
        export API_URL="http://localhost:8000"
    fi
else
    echo "ℹ️  Tailscale not detected, using localhost"
    export API_URL="http://localhost:8000"
fi

# Start the application
echo "🐳 Starting services with Docker Compose..."
echo "🔗 API URL: $API_URL"
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Access your application:"
    echo "   Frontend (Local): http://localhost:3000"
    if [ -n "$TAILSCALE_IP" ]; then
        echo "   Frontend (Network): http://$TAILSCALE_IP:3000"
        echo "   Backend API (Network): http://$TAILSCALE_IP:8000"
        echo "   API Documentation (Network): http://$TAILSCALE_IP:8000/docs"
    fi
    echo "   Backend API (Local): http://localhost:8000"
    echo "   API Documentation (Local): http://localhost:8000/docs"
    echo ""
    echo "📱 Mobile Access:"
    if [ -n "$TAILSCALE_IP" ]; then
        echo "   Open http://$TAILSCALE_IP:3000 on your mobile device"
        echo "   (Make sure your device is on the same Tailscale network)"
    else
        echo "   Install Tailscale to access from other devices"
    fi
    echo ""
    echo "📊 Monitor services:"
    echo "   docker compose logs -f"
    echo ""
    echo "🛑 Stop services:"
    echo "   docker compose down"
else
    echo "❌ Some services failed to start. Check logs with:"
    echo "   docker compose logs"
    exit 1
fi 