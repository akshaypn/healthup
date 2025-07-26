#!/bin/bash

# Simple EC2 IP detection test
echo "🔍 Testing EC2 IP Detection"
echo "=========================="

# Test AWS metadata service
echo "Testing AWS metadata service..."
if curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null)
    echo "✅ Found public IP via AWS metadata: $PUBLIC_IP"
else
    echo "❌ AWS metadata service failed"
fi

# Test external service
echo "Testing external service..."
if curl -s http://checkip.amazonaws.com/ 2>/dev/null | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
    EXTERNAL_IP=$(curl -s http://checkip.amazonaws.com/ 2>/dev/null)
    echo "✅ Found IP via external service: $EXTERNAL_IP"
else
    echo "❌ External service failed"
fi

# Test private IP
echo "Testing private IP..."
PRIVATE_IP=$(hostname -I | awk '{print $1}' | head -1)
echo "✅ Private IP: $PRIVATE_IP"

echo ""
echo "Summary:"
echo "  - Public IP (metadata): ${PUBLIC_IP:-Not available}"
echo "  - Public IP (external): ${EXTERNAL_IP:-Not available}"
echo "  - Private IP: $PRIVATE_IP" 