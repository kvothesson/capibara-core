#!/bin/bash
# Capibara Core Installation Script

set -e

echo "🚀 Installing Capibara Core..."

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ required. Found: $python_version"
    echo "Please upgrade Python and try again."
    exit 1
fi

echo "✅ Python version: $python_version"

# Install Capibara Core
echo "📦 Installing Capibara Core..."
pip3 install -e .

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker not found. Installing Docker..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install --cask docker
        else
            echo "❌ Homebrew not found. Please install Docker Desktop manually:"
            echo "   https://www.docker.com/products/docker-desktop/"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
        sudo usermod -aG docker $USER
        echo "✅ Docker installed. Please log out and log back in for group changes to take effect."
    else
        echo "❌ Unsupported OS: $OSTYPE"
        echo "Please install Docker manually: https://docs.docker.com/get-docker/"
        exit 1
    fi
else
    echo "✅ Docker found"
fi

# Create config directory
mkdir -p ~/.capibara
echo "✅ Created config directory: ~/.capibara"

# Copy example config
if [ ! -f ~/.capibara/.env ]; then
    cp env.example ~/.capibara/.env
    echo "✅ Created config file: ~/.capibara/.env"
    echo "📝 Please edit ~/.capibara/.env and add your API keys"
else
    echo "ℹ️  Config file already exists: ~/.capibara/.env"
fi

# Pull Docker image
echo "🐳 Pulling Docker image..."
docker pull python:3.11-slim

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Configure API keys: nano ~/.capibara/.env"
echo "2. Check system health: capibara doctor"
echo "3. Run your first script: capibara run 'Hello World' --execute"
echo ""
echo "For help: capibara --help"
