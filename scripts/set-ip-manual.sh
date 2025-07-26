#!/bin/bash

# Manual IP setting script for HealthUp production setup
# This script allows you to manually specify the IP address to use

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=================================="
echo "HealthUp Manual IP Configuration"
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

# Get current IPs
echo "Current IP addresses:"
echo "1. Local IP: $(hostname -I | awk '{print $1}')"
echo "2. Public IP: $(curl -s --connect-timeout 5 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'Not available')"
echo "3. Enter custom IP"
echo ""

read -p "Select option (1-3): " -n 1 -r
echo

case $REPLY in
    1)
        SELECTED_IP=$(hostname -I | awk '{print $1}')
        echo -e "${GREEN}Selected local IP: $SELECTED_IP${NC}"
        ;;
    2)
        SELECTED_IP=$(curl -s --connect-timeout 5 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "")
        if [ -n "$SELECTED_IP" ]; then
            echo -e "${GREEN}Selected public IP: $SELECTED_IP${NC}"
        else
            echo -e "${RED}Public IP not available${NC}"
            exit 1
        fi
        ;;
    3)
        read -p "Enter custom IP address: " SELECTED_IP
        if validate_ip "$SELECTED_IP"; then
            echo -e "${GREEN}Selected custom IP: $SELECTED_IP${NC}"
        else
            echo -e "${RED}Invalid IP address format${NC}"
            exit 1
        fi
        ;;
    *)
        echo -e "${RED}Invalid selection${NC}"
        exit 1
        ;;
esac

# Export the IP for use with the production setup script
export MANUAL_EC2_IP="$SELECTED_IP"

echo ""
echo "IP address set: $SELECTED_IP"
echo ""
echo "To run the production setup with this IP:"
echo "MANUAL_EC2_IP=$SELECTED_IP ./scripts/ec2-production-setup.sh"
echo ""
echo "Or run the setup now? (y/N)"
read -p "" -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running production setup..."
    ./scripts/ec2-production-setup.sh
else
    echo "IP configured. Run the production setup script when ready."
fi 