#!/bin/bash

# Test script for IP detection logic
# This script tests the IP detection functions from ec2-production-setup.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Source the functions from the main script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/ec2-production-setup.sh"

echo "=================================="
echo "IP Detection Test"
echo "=================================="
echo ""

# Test IP validation function
echo "Testing IP validation..."
test_ips=("192.168.1.1" "10.0.0.1" "172.16.0.1" "256.1.2.3" "1.2.3.4.5" "invalid" "")

for ip in "${test_ips[@]}"; do
    if validate_ip "$ip"; then
        success "Valid IP: $ip"
    else
        warning "Invalid IP: $ip"
    fi
done
echo ""

# Test EC2 metadata detection
echo "Testing EC2 metadata detection..."
get_ec2_ip

echo ""
echo "Detection Results:"
echo "  - Private IP: $EC2_PRIVATE_IP"
echo "  - Public IP: $EC2_PUBLIC_IP"
echo "  - Selected IP: $EC2_IP"
echo ""

# Test connectivity
if [ -n "$EC2_IP" ]; then
    echo "Testing connectivity to selected IP..."
    if test_ip_connectivity "$EC2_IP" 80; then
        success "Port 80 is reachable on $EC2_IP"
    else
        warning "Port 80 is not reachable on $EC2_IP"
    fi
    
    if test_ip_connectivity "$EC2_IP" 443; then
        success "Port 443 is reachable on $EC2_IP"
    else
        warning "Port 443 is not reachable on $EC2_IP"
    fi
else
    error "No IP detected for connectivity testing"
fi

echo ""
echo "=================================="
echo "Test completed!"
echo "==================================" 