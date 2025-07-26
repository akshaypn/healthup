#!/bin/bash

# Script to set IP address for docker-compose
# This script sets the EC2_IP environment variable and updates .env

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=================================="
echo "Set IP for Docker Compose"
echo "=================================="
echo ""

# Function to validate IP address
validate_ip() {
    local ip="$1"
    
    if [ -z "$ip" ]; then
        return 1
    fi
    
    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
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

# Get IP from user
echo "Enter the IP address to use for services:"
echo "1. Localhost (127.0.0.1) - for local development"
echo "2. EC2 Public IP - for production"
echo "3. Custom IP"
echo ""

read -p "Select option (1-3): " -n 1 -r
echo

case $REPLY in
    1)
        SELECTED_IP="127.0.0.1"
        echo -e "${GREEN}Selected localhost: $SELECTED_IP${NC}"
        ;;
    2)
        # Try to get EC2 public IP
        EC2_PUBLIC_IP=$(curl -s --connect-timeout 5 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "")
        if [ -n "$EC2_PUBLIC_IP" ]; then
            SELECTED_IP="$EC2_PUBLIC_IP"
            echo -e "${GREEN}Detected EC2 public IP: $SELECTED_IP${NC}"
        else
            echo -e "${YELLOW}Could not detect EC2 public IP automatically${NC}"
            read -p "Enter EC2 public IP: " SELECTED_IP
        fi
        ;;
    3)
        read -p "Enter custom IP address: " SELECTED_IP
        ;;
    *)
        echo -e "${RED}Invalid selection${NC}"
        exit 1
        ;;
esac

# Validate IP
if ! validate_ip "$SELECTED_IP"; then
    echo -e "${RED}Invalid IP address format${NC}"
    exit 1
fi

# Update .env file
echo ""
echo "Updating .env file..."

# Remove existing EC2_IP line if it exists
if [ -f ".env" ]; then
    sed -i '/^EC2_IP=/d' .env
fi

# Add EC2_IP to .env
echo "EC2_IP=$SELECTED_IP" >> .env

# Export for current session
export EC2_IP="$SELECTED_IP"

echo -e "${GREEN}IP address set to: $SELECTED_IP${NC}"
echo ""
echo "Environment variables:"
echo "  - EC2_IP=$SELECTED_IP"
echo "  - VITE_API_URL=http://$SELECTED_IP:8000"
echo "  - FRONTEND_ORIGINS=http://$SELECTED_IP:3000"
echo ""
echo "To restart services with new IP:"
echo "  docker compose down"
echo "  docker compose up -d"
echo ""
echo "Or restart individual services:"
echo "  docker compose restart backend frontend" 