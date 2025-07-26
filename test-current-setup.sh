#!/bin/bash

# Quick test script to verify current setup
set -e

echo "Testing current HealthUp setup..."

# Check if services are running
echo "1. Checking service status..."
docker compose ps

# Test backend API
echo "2. Testing backend API..."
if curl -s http://localhost:8000/ >/dev/null; then
    echo "✓ Backend API is responding"
else
    echo "✗ Backend API is not responding"
    exit 1
fi

# Test frontend
echo "3. Testing frontend..."
if curl -s http://localhost:3000/ >/dev/null; then
    echo "✓ Frontend is responding"
else
    echo "✗ Frontend is not responding"
    exit 1
fi

# Test database
echo "4. Testing database..."
if docker compose exec -T postgres pg_isready -U healthup >/dev/null 2>&1; then
    echo "✓ Database is ready"
else
    echo "✗ Database is not ready"
    exit 1
fi

# Test Redis
echo "5. Testing Redis..."
if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
    echo "✓ Redis is ready"
else
    echo "✗ Redis is not ready"
    exit 1
fi

echo "✓ All tests passed! Setup is working correctly." 