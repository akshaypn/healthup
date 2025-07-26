#!/bin/bash

# HealthUp Android App Build Script
# This script builds the Android APK for the HealthUp app

set -e

echo "🏗️  Building HealthUp Android App..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the HealthUpAndroid directory."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is not installed. Please install npm first."
    exit 1
fi

# Check if Expo CLI is installed
if ! command -v expo &> /dev/null; then
    echo "📦 Installing Expo CLI..."
    npm install -g @expo/cli
fi

echo "📦 Installing dependencies..."
npm install

echo "🔧 Checking configuration..."
if [ ! -f "app.json" ]; then
    echo "❌ Error: app.json not found. Please ensure the app is properly configured."
    exit 1
fi

echo "🧹 Cleaning previous builds..."
rm -rf android/
rm -rf ios/
rm -rf .expo/

echo "🔨 Building Android APK..."
npx expo build:android --type apk

echo "✅ Build completed successfully!"
echo "📱 APK file should be available in the build output."
echo ""
echo "To install on a device:"
echo "1. Enable 'Install from unknown sources' in Android settings"
echo "2. Transfer the APK to your device"
echo "3. Install the APK file"
echo ""
echo "To run in development mode:"
echo "npm start"
echo "Then scan the QR code with Expo Go app" 