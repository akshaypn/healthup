#!/bin/bash

echo "🔧 HealthUp IP Configuration"
echo "============================"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run ec2-quick-setup.sh first."
    exit 1
fi

echo "Current .env configuration:"
echo "---------------------------"
grep -E "^(API_URL|CORS_ORIGINS)=" .env || echo "No API_URL or CORS_ORIGINS found"

echo ""
echo "Enter your EC2 public IP address:"
read -p "EC2 Public IP: " EC2_PUBLIC_IP

if [[ ! $EC2_PUBLIC_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Invalid IP address format"
    exit 1
fi

# Update .env file
echo "📝 Updating .env file..."
sed -i "s|API_URL=.*|API_URL=http://$EC2_PUBLIC_IP:8000|g" .env
sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=http://$EC2_PUBLIC_IP:3000|g" .env

echo "✅ Updated .env with IP: $EC2_PUBLIC_IP"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend: http://$EC2_PUBLIC_IP:3000"
echo "   Backend: http://$EC2_PUBLIC_IP:8000"
echo "   API Docs: http://$EC2_PUBLIC_IP:8000/docs"
echo ""
echo "🔄 Restart services to apply changes:"
echo "   docker compose down && docker compose up -d" 