#!/bin/bash
# Docker installation script for Capibara Core

set -e

echo "🐳 Installing Docker for Capibara Core..."

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "📱 Detected macOS"
    
    if command -v brew &> /dev/null; then
        echo "🍺 Installing Docker via Homebrew..."
        brew install --cask docker
    else
        echo "❌ Homebrew not found. Please install Docker Desktop manually:"
        echo "   https://www.docker.com/products/docker-desktop/"
        exit 1
    fi
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "🐧 Detected Linux"
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        echo "⚠️  Running as root. This is not recommended."
    fi
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    echo "✅ Docker installed. Please log out and log back in for group changes to take effect."
    
else
    echo "❌ Unsupported OS: $OSTYPE"
    echo "Please install Docker manually: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker installation complete!"
echo "🚀 Please start Docker Desktop and run 'capibara doctor' to verify installation."
