#!/bin/bash

# Render Deployment Helper Script
# This script helps you prepare for Render deployment

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=============================================="
echo -e "${BLUE}Render Deployment Helper${NC}"
echo "=============================================="
echo ""

# Step 1: Check if render.yaml exists
if [ ! -f render.yaml ]; then
    echo -e "${YELLOW}⚠️  render.yaml not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ render.yaml found${NC}"

# Step 2: Check if Dockerfile.render exists
if [ ! -f Dockerfile.render ]; then
    echo -e "${YELLOW}⚠️  Dockerfile.render not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Dockerfile.render found${NC}"

# Step 3: Generate Firebase credentials
echo ""
echo "Generating Firebase credentials..."
python3 encode_firebase_creds.py > /dev/null 2>&1

if [ -f firebase_creds_encoded.txt ]; then
    echo -e "${GREEN}✅ Firebase credentials encoded${NC}"
else
    echo -e "${YELLOW}⚠️  Failed to encode Firebase credentials${NC}"
fi

# Step 4: Check if committed to Git
echo ""
echo "Checking Git status..."

if git rev-parse --git-dir > /dev/null 2>&1; then
    if [[ -n $(git status -s) ]]; then
        echo -e "${YELLOW}⚠️  You have uncommitted changes${NC}"
        echo ""
        echo "Would you like to commit and push? (y/n)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            git add .
            echo "Enter commit message:"
            read -r commit_msg
            git commit -m "$commit_msg"
            git push
            echo -e "${GREEN}✅ Changes pushed to Git${NC}"
        fi
    else
        echo -e "${GREEN}✅ Git repository is clean${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Not a Git repository${NC}"
    echo "Initialize Git? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        git init
        git add .
        echo "Enter commit message:"
        read -r commit_msg
        git commit -m "$commit_msg"
        echo -e "${GREEN}✅ Git initialized and files committed${NC}"
        echo ""
        echo "Add remote and push:"
        echo "  git remote add origin YOUR_REPO_URL"
        echo "  git push -u origin main"
    fi
fi

# Step 5: Show environment variables
echo ""
echo "=============================================="
echo -e "${GREEN}Deployment Ready!${NC}"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Go to https://render.com and sign up"
echo "2. Click 'New +' → 'Web Service'"
echo "3. Connect your GitHub repository"
echo "4. Configure:"
echo "   - Environment: Docker"
echo "   - Dockerfile: Dockerfile.render"
echo "   - Plan: Free"
echo ""
echo "5. Add these environment variables in Render:"
echo ""

# Read .env and show required variables
if [ -f .env ]; then
    echo -e "${BLUE}From your .env file:${NC}"
    while IFS= read -r line; do
        if [[ ! "$line" =~ ^#.*$ ]] && [[ -n "$line" ]]; then
            var_name=$(echo "$line" | cut -d'=' -f1)
            if [[ "$var_name" != "FIREBASE_CREDENTIALS_PATH" ]]; then
                echo "   $var_name"
            fi
        fi
    done < .env
fi

echo ""
echo -e "${YELLOW}IMPORTANT: Add Firebase credentials${NC}"
if [ -f firebase_creds_encoded.txt ]; then
    echo "Copy this to Render's FIREBASE_CREDENTIALS variable:"
    echo ""
    cat firebase_creds_encoded.txt
fi

echo ""
echo "=============================================="
echo "See RENDER_DEPLOYMENT.md for detailed guide"
echo "=============================================="

