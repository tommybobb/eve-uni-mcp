#!/bin/bash
# Quick deployment script for Raspberry Pi

set -e

# Parse arguments
USE_GHCR=false
if [[ "$1" == "--use-ghcr" ]]; then
    USE_GHCR=true
fi

echo "🥧 EVE University Wiki MCP - Raspberry Pi Quick Deploy"
echo "======================================================"
echo

if [ "$USE_GHCR" = true ]; then
    echo "📦 Mode: Using pre-built image from GitHub Container Registry"
else
    echo "🏗️  Mode: Building image locally"
fi
echo

# Check if we're on ARM
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" && "$ARCH" != "armv7l" ]]; then
    echo "⚠️  Warning: Not running on ARM architecture ($ARCH)"
    echo "This script is optimized for Raspberry Pi but will continue anyway."
    echo
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "📦 Docker not found."
    echo ""
    echo "⚠️  SECURITY NOTICE:"
    echo "This script can install Docker automatically, but this requires running"
    echo "a remote script with elevated privileges."
    echo ""
    echo "Options:"
    echo "  1. Install Docker automatically (runs: curl -fsSL https://get.docker.com | sh)"
    echo "  2. Install Docker manually (recommended)"
    echo ""
    read -p "Choose option (1 or 2): " choice
    
    if [[ "$choice" == "1" ]]; then
        echo "Installing Docker automatically..."
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker $USER
        echo "✅ Docker installed! You may need to log out and back in."
        echo "Then run this script again."
        exit 0
    else
        echo ""
        echo "Please install Docker manually:"
        echo "  Visit: https://docs.docker.com/engine/install/"
        echo ""
        echo "For Raspberry Pi OS:"
        echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
        echo "  cat get-docker.sh  # Review the script first!"
        echo "  sudo sh get-docker.sh"
        echo "  sudo usermod -aG docker \$USER"
        echo ""
        exit 0
    fi
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Docker Compose not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y docker-compose
fi

echo "✅ Docker is installed"
echo

# Get IP address
IP=$(hostname -I | awk '{print $1}')
echo "📡 Your Raspberry Pi IP: $IP"
echo

# Setup environment
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
fi

# Build or pull image
if [ "$USE_GHCR" = true ]; then
    echo "📥 Pulling pre-built image from GitHub Container Registry..."
    docker pull ghcr.io/tommybobb/eve-uni-mcp:latest

    echo
    echo "🚀 Starting service with pre-built image..."
    docker-compose -f docker-compose.ghcr.yml up -d
else
    echo "🏗️  Building container (this may take a few minutes on Pi)..."
    docker-compose build

    echo
    echo "🚀 Starting service..."
    docker-compose up -d
fi

echo
echo "⏳ Waiting for service to start..."
sleep 5

# Health check
echo "🏥 Checking health..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Service is healthy!"
else
    echo "❌ Service health check failed"
    echo "Showing logs:"
    docker-compose logs
    exit 1
fi

echo
echo "======================================================"
echo "🎉 Deployment Complete!"
echo "======================================================"
echo
echo "Service is running at:"
echo "  🔗 SSE Endpoint: http://$IP:8000/sse"
echo "  ❤️  Health Check: http://$IP:8000/health"
echo
echo "Add this to Claude Desktop config:"
echo "  {\"mcpServers\": {\"eve-university-wiki\": {\"url\": \"http://$IP:8000/sse\"}}}"
echo
echo "Useful commands:"
echo "  docker-compose logs -f    # View logs"
echo "  docker-compose ps         # Check status"
echo "  docker-compose restart    # Restart service"
echo "  docker-compose down       # Stop service"
echo
echo "Or use the Makefile:"
echo "  make logs                 # View logs"
echo "  make health               # Check health"
echo "  make restart              # Restart"
echo
echo "To update:"
if [ "$USE_GHCR" = true ]; then
    echo "  docker pull ghcr.io/tommybobb/eve-uni-mcp:latest"
    echo "  docker-compose -f docker-compose.ghcr.yml restart"
else
    echo "  git pull origin main"
    echo "  make rebuild"
fi
echo
