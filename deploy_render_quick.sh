#!/bin/bash

echo "🚀 Quick Render Deployment for TG-Fets Trading Bot"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "new_bot.py" ]; then
    print_error "new_bot.py not found. Please run this script from the project root."
    exit 1
fi

print_success "Project files found"

# Check if render.yaml exists
if [ ! -f "render.yaml" ]; then
    print_error "render.yaml not found"
    exit 1
fi

print_success "render.yaml found"

# Check if Dockerfile.render exists
if [ ! -f "Dockerfile.render" ]; then
    print_error "Dockerfile.render not found"
    exit 1
fi

print_success "Dockerfile.render found"

# Generate Firebase credentials
print_status "Generating Firebase credentials..."
if [ -f "encode_firebase_creds.py" ]; then
    python3 encode_firebase_creds.py > /dev/null 2>&1
    if [ -f "firebase_creds_encoded.txt" ]; then
        print_success "Firebase credentials encoded"
        FIREBASE_CREDS=$(cat firebase_creds_encoded.txt)
        print_status "Firebase credentials ready for Render"
    else
        print_warning "Failed to generate Firebase credentials"
    fi
else
    print_warning "encode_firebase_creds.py not found"
fi

# Check Git status
print_status "Checking Git status..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    if [[ -n $(git status -s) ]]; then
        print_warning "You have uncommitted changes"
        echo ""
        echo "Would you like to commit and push? (y/n)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            git add .
            echo "Enter commit message (or press Enter for default):"
            read -r commit_msg
            if [ -z "$commit_msg" ]; then
                commit_msg="Deploy to Render - $(date)"
            fi
            git commit -m "$commit_msg"
            git push
            print_success "Changes pushed to Git"
        else
            print_warning "Skipping Git commit. Make sure to push changes before deploying."
        fi
    else
        print_success "Git repository is clean"
    fi
else
    print_warning "Not a Git repository"
    echo "Initialize Git? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        git init
        git add .
        echo "Enter commit message:"
        read -r commit_msg
        if [ -z "$commit_msg" ]; then
            commit_msg="Initial commit for Render deployment"
        fi
        git commit -m "$commit_msg"
        print_success "Git initialized and files committed"
        echo ""
        print_warning "Add remote and push:"
        echo "  git remote add origin YOUR_REPO_URL"
        echo "  git push -u origin main"
    fi
fi

echo ""
echo "=================================================="
print_success "Ready for Render Deployment!"
echo "=================================================="
echo ""
print_status "Next steps:"
echo ""
echo "1. 🌐 Go to https://render.com and sign up"
echo "2. 🔗 Click 'New +' → 'Web Service'"
echo "3. 📁 Connect your GitHub repository"
echo "4. ⚙️  Configure:"
echo "   - Name: tg-fets-bot"
echo "   - Environment: Docker"
echo "   - Dockerfile: Dockerfile.render"
echo "   - Plan: Free"
echo "   - Health Check Path: /health"
echo ""
echo "5. 🔐 Add these environment variables:"
echo ""

# Show required environment variables
if [ -f ".env" ]; then
    print_status "Required environment variables:"
    while IFS= read -r line; do
        if [[ ! "$line" =~ ^#.*$ ]] && [[ -n "$line" ]] && [[ "$line" == *"="* ]]; then
            var_name=$(echo "$line" | cut -d'=' -f1)
            if [[ "$var_name" != "FIREBASE_CREDENTIALS_PATH" ]]; then
                echo "   $var_name"
            fi
        fi
    done < .env
fi

echo ""
if [ -n "$FIREBASE_CREDS" ]; then
    print_warning "IMPORTANT: Add Firebase credentials"
    echo "Copy this to Render's FIREBASE_CREDENTIALS variable:"
    echo ""
    echo "$FIREBASE_CREDS"
    echo ""
fi

echo "6. 🚀 Click 'Create Web Service'"
echo ""
print_success "Your bot will be deployed and running in minutes!"
echo ""
print_status "After deployment:"
echo "- Check logs in Render Dashboard"
echo "- Test your bot with /start command"
echo "- Monitor health at https://your-app.onrender.com/health"
echo ""
echo "=================================================="
echo "📖 See RENDER_DEPLOYMENT.md for detailed guide"
echo "=================================================="
