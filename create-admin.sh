#!/bin/bash

echo "👤 Creating default admin user..."
echo "================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run ec2-quick-setup.sh first."
    exit 1
fi

# Create admin user using the backend API
echo "📝 Creating admin user: admin@admin.com / 123456"

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 10

# Try to create the admin user
RESPONSE=$(curl -s -X POST "http://100.123.199.100:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@admin.com",
    "password": "123456"
  }')

if echo "$RESPONSE" | grep -q "User registered"; then
    echo "✅ Admin user created successfully!"
    echo ""
    echo "🔑 Login credentials:"
    echo "   Email: admin@admin.com"
    echo "   Password: 123456"
    echo ""
    echo "🌐 You can now login at:"
    echo "   http://$(grep API_URL .env | cut -d'=' -f2 | sed 's|http://||' | sed 's|:8000||'):3000"
else
    echo "⚠️  Admin user creation response: $RESPONSE"
    echo "   (User might already exist or there was an error)"
fi

echo ""
echo "🔧 If you need to reset the admin password, you can:"
echo "   1. Delete the user from the database"
echo "   2. Run this script again"
echo "   3. Or register a new user through the web interface" 