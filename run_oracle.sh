#!/bin/bash

# Script to run on Oracle Cloud instance
# This script loads and runs the Docker container

set -e

echo "======================================"
echo "TG-Fets Bot - Oracle Cloud Runner"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker not found. Installing Docker...${NC}"
    
    # Update package list
    sudo apt-get update
    
    # Install required packages
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Set up stable repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    echo -e "${GREEN}✓ Docker installed successfully${NC}"
    echo -e "${YELLOW}Note: You may need to log out and back in for group changes to take effect${NC}"
fi

# Stop existing container if running
echo -e "${YELLOW}Stopping existing container (if any)...${NC}"
docker stop tg-fets-bot 2>/dev/null || true
docker rm tg-fets-bot 2>/dev/null || true

# Load Docker image
if [ -f tg-fets-bot.tar ]; then
    echo -e "${GREEN}Loading Docker image...${NC}"
    docker load -i tg-fets-bot.tar
    echo -e "${GREEN}✓ Image loaded${NC}"
else
    echo -e "${RED}Error: tg-fets-bot.tar not found${NC}"
    exit 1
fi

# Check for environment file
if [ ! -f env.production ]; then
    echo -e "${RED}Error: env.production file not found${NC}"
    echo "Please ensure you uploaded the env.production file"
    exit 1
fi

# Run the container
echo -e "${GREEN}Starting TG-Fets Bot container...${NC}"
docker run -d \
    --name tg-fets-bot \
    --restart unless-stopped \
    --env-file env.production \
    -p 8080:8080 \
    tg-fets-bot:latest

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo -e "${GREEN}✓ Bot started successfully!${NC}"
    echo "======================================"
    echo ""
    echo "Useful commands:"
    echo "  View logs:        ${YELLOW}docker logs -f tg-fets-bot${NC}"
    echo "  Stop bot:         ${YELLOW}docker stop tg-fets-bot${NC}"
    echo "  Start bot:        ${YELLOW}docker start tg-fets-bot${NC}"
    echo "  Restart bot:      ${YELLOW}docker restart tg-fets-bot${NC}"
    echo "  Check status:     ${YELLOW}docker ps${NC}"
    echo ""
    echo "Viewing logs now (Ctrl+C to exit)..."
    echo "======================================"
    sleep 2
    docker logs -f tg-fets-bot
else
    echo -e "${RED}✗ Failed to start container${NC}"
    exit 1
fi

