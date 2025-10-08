#!/bin/bash

# Oracle Cloud Deployment Script for TG-Fets Trading Bot
# This script helps deploy your bot to Oracle Cloud Infrastructure

set -e

echo "======================================"
echo "Oracle Cloud Deployment Script"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create a .env file with your configuration."
    exit 1
fi

echo -e "${GREEN}Step 1: Building Docker Image${NC}"
echo "Building image for Oracle Cloud..."
docker build -f Dockerfile.oracle -t tg-fets-bot:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${RED}✗ Docker build failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Step 2: Saving Docker Image${NC}"
echo "Saving image to tarball for transfer to Oracle Cloud..."
docker save tg-fets-bot:latest -o tg-fets-bot.tar

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker image saved to tg-fets-bot.tar${NC}"
    echo -e "${YELLOW}File size: $(du -h tg-fets-bot.tar | cut -f1)${NC}"
else
    echo -e "${RED}✗ Failed to save Docker image${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Step 3: Creating deployment package${NC}"
echo "Creating oracle-deploy directory..."
mkdir -p oracle-deploy

# Copy necessary files
cp tg-fets-bot.tar oracle-deploy/
cp .env oracle-deploy/env.production
cp deploy_oracle.sh oracle-deploy/
cp run_oracle.sh oracle-deploy/

# Generate encoded Firebase credentials and add to env file
echo ""
echo "Encoding Firebase credentials..."
python3 encode_firebase_creds.py

if [ -f firebase_creds_encoded.txt ]; then
    echo ""
    echo "Adding Firebase credentials to env.production..."
    cat firebase_creds_encoded.txt >> oracle-deploy/env.production
    echo -e "${GREEN}✓ Firebase credentials added to environment${NC}"
fi

echo -e "${GREEN}✓ Deployment package created in oracle-deploy/${NC}"

echo ""
echo "======================================"
echo -e "${GREEN}Build Complete!${NC}"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Create an Oracle Cloud account (if you haven't already)"
echo "2. Create a Compute Instance (use Always Free tier)"
echo "3. Upload the oracle-deploy directory to your instance:"
echo "   ${YELLOW}scp -r oracle-deploy ubuntu@YOUR_INSTANCE_IP:~/${NC}"
echo ""
echo "4. SSH into your instance:"
echo "   ${YELLOW}ssh ubuntu@YOUR_INSTANCE_IP${NC}"
echo ""
echo "5. On the instance, run:"
echo "   ${YELLOW}cd oracle-deploy${NC}"
echo "   ${YELLOW}chmod +x run_oracle.sh${NC}"
echo "   ${YELLOW}./run_oracle.sh${NC}"
echo ""
echo "See ORACLE_DEPLOYMENT.md for detailed instructions"
echo "======================================"

