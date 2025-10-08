#!/bin/bash

echo "🚀 Deploying TG-Bot-Fets to Fly.io..."

# Check if fly CLI is installed
if ! command -v fly &> /dev/null; then
    echo "❌ Fly CLI not found. Installing..."
    curl -L https://fly.io/install.sh | sh
    export PATH="$HOME/.fly/bin:$PATH"
fi

# Check if user is logged in
if ! fly auth whoami &> /dev/null; then
    echo "🔐 Please log in to Fly.io..."
    fly auth login
fi

# Create app if it doesn't exist
if ! fly apps list | grep -q "tg-fets-trading-bot"; then
    echo "📱 Creating new Fly.io app: tg-fets-trading-bot"
    fly apps create tg-fets-trading-bot --org personal
fi

# Create volume for persistent data
if ! fly volumes list | grep -q "tg_bot_data"; then
    echo "💾 Creating persistent volume..."
    fly volumes create tg_bot_data --size 1 --region iad
fi

# Set secrets from .env file
echo "🔐 Setting secrets from .env file..."
if [ -f .env ]; then
    # Read .env file and set secrets
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        if [[ $key =~ ^[[:space:]]*# ]] || [[ -z $key ]]; then
            continue
        fi
        
        # Remove quotes and spaces
        key=$(echo $key | xargs)
        value=$(echo $value | xargs | sed 's/^"//;s/"$//')
        
                    if [ ! -z "$key" ] && [ ! -z "$value" ]; then
                echo "Setting secret: $key"
                fly secrets set "$key=$value" --app tg-fets-trading-bot
            fi
    done < .env
else
    echo "⚠️  No .env file found. Please set secrets manually:"
    echo "fly secrets set TELEGRAM_BOT_TOKEN=your_token --app tg-fets-trading-bot"
    echo "fly secrets set X_BEARER_TOKEN=your_token --app tg-fets-trading-bot"
    echo "fly secrets set X_API_KEY=your_key --app tg-fets-trading-bot"
    echo "fly secrets set X_API_SECRET=your_secret --app tg-fets-trading-bot"
    echo "fly secrets set X_ACCESS_TOKEN=your_token --app tg-fets-trading-bot"
    echo "fly secrets set X_ACCESS_TOKEN_SECRET=your_secret --app tg-fets-trading-bot"
    echo "fly secrets set FIREBASE_CREDENTIALS_PATH=your_path --app tg-fets-trading-bot"
    echo "fly secrets set X_ACCESS_TOKEN_SECRET=your_secret --app tg-fets-trading-bot"
    echo "fly secrets set ENCRYPTION_KEY=your_key --app tg-fets-trading-bot"
fi

# Deploy the app
echo "🚀 Deploying to Fly.io..."
fly deploy

echo "✅ Deployment complete!"
echo "🌐 Your bot is now running on Fly.io!"
echo "📱 Check status: fly status --app tg-fets-trading-bot"
echo "📊 View logs: fly logs --app tg-fets-trading-bot"
echo "🔍 Health check: https://tg-fets-trading-bot.fly.dev/health"
