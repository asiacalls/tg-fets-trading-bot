#!/bin/bash

echo "🚀 Fly.io Deployment Helper for TG-Fets Trading Bot"
echo "=================================================="

# Check if fly CLI is installed
if ! command -v fly &> /dev/null; then
    echo "❌ Fly CLI not found. Please install it first:"
    echo ""
    echo "macOS: brew install flyctl"
    echo "Linux: curl -L https://fly.io/install.sh | sh"
    echo "Windows: Download from https://fly.io/docs/hands-on/install-flyctl/"
    echo ""
    echo "After installation, run: fly auth login"
    exit 1
fi

echo "✅ Fly CLI is installed"

# Check if user is logged in
if ! fly auth whoami &> /dev/null; then
    echo "❌ Not logged in to Fly.io. Please run:"
    echo "   fly auth login"
    exit 1
fi

echo "✅ Logged in to Fly.io as: $(fly auth whoami)"

# Check if all required files exist
echo ""
echo "📋 Checking required files for Fly.io..."

required_files=("new_bot.py" "requirements.txt" "fly.toml" "Dockerfile")
missing_files=()

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo ""
    echo "❌ Missing required files. Please create them before deploying."
    exit 1
fi

echo ""
echo "✅ All required files are present!"
echo ""

# Check if app already exists
if fly apps list | grep -q "tg-fets-trading-bot"; then
    echo "🎯 App 'tg-fets-trading-bot' already exists on Fly.io"
    echo ""
    echo "To deploy updates:"
    echo "   fly deploy"
    echo ""
    echo "To view logs:"
    echo "   fly logs -f"
    echo ""
    echo "To check status:"
    echo "   fly status"
else
    echo "🚀 App 'tg-fets-trading-bot' not found. Ready to create!"
    echo ""
    echo "To deploy:"
    echo "   fly launch"
    echo ""
    echo "Or manually:"
    echo "   fly apps create tg-fets-trading-bot"
    echo "   fly deploy"
fi

echo ""
echo "📖 See FLY_DEPLOYMENT.md for detailed instructions"
echo ""
echo "🎯 Your bot will be live 24/7 on Fly.io (FREE tier available)!"
