#!/bin/bash

echo "🌐 HealthUp Network Setup"
echo "========================="

# Check if Tailscale is installed
if ! command -v tailscale &> /dev/null; then
    echo "❌ Tailscale is not installed."
    echo ""
    echo "📱 To access HealthUp from other devices:"
    echo "   1. Install Tailscale on your devices:"
    echo "      - Desktop: https://tailscale.com/download"
    echo "      - Mobile: App Store / Google Play"
    echo "   2. Sign in with the same account on all devices"
    echo "   3. Run this script again"
    exit 1
fi

# Check if Tailscale is running
if ! tailscale status &> /dev/null; then
    echo "❌ Tailscale is not running."
    echo "   Please start Tailscale and try again."
    exit 1
fi

# Get Tailscale IP
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null | head -n1)

if [ -z "$TAILSCALE_IP" ]; then
    echo "❌ Could not get Tailscale IP address."
    echo "   Please check your Tailscale connection."
    exit 1
fi

echo "✅ Tailscale is running"
echo "🌐 Your Tailscale IP: $TAILSCALE_IP"
echo ""

# Check if services are running
if ! docker compose ps | grep -q "Up"; then
    echo "❌ HealthUp services are not running."
    echo "   Please run './start.sh' first."
    exit 1
fi

echo "✅ HealthUp services are running"
echo ""

# Show access URLs
echo "📱 Access HealthUp from other devices:"
echo "   Frontend: http://$TAILSCALE_IP:3000"
echo "   Backend API: http://$TAILSCALE_IP:8000"
echo "   API Docs: http://$TAILSCALE_IP:8000/docs"
echo ""

# Show other devices on network
echo "🔍 Other devices on your Tailscale network:"
tailscale status | grep -v "akshaythinkpad" | grep -E "^[0-9]" | while read line; do
    if [[ $line =~ ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) ]]; then
        ip="${BASH_REMATCH[1]}"
        name=$(echo "$line" | awk '{print $2}')
        echo "   $name: $ip"
    fi
done

echo ""
echo "💡 Tips:"
echo "   - Make sure all devices are signed into the same Tailscale account"
echo "   - The app will work on mobile browsers"
echo "   - You can bookmark the URL for easy access"
echo "   - If you can't connect, check your firewall settings" 