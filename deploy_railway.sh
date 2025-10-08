#!/bin/bash

echo "🚂 Deploying to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check if user is logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway..."
    railway login
fi

# Create new project if it doesn't exist
echo "📁 Creating/updating Railway project..."
railway init --name "tg-fets-trading-bot" --yes

# Set environment variables from .env file
echo "🔧 Setting environment variables..."
if [ -f .env ]; then
    while IFS= read -r line; do
        if [[ $line != \#* ]] && [[ -n $line ]]; then
            key=$(echo $line | cut -d'=' -f1)
            value=$(echo $line | cut -d'=' -f2-)
            echo "Setting $key..."
            railway variables set "$key"="$value"
        fi
    done < .env
else
    echo "⚠️  .env file not found. Please set environment variables manually in Railway dashboard."
fi

# Deploy the application
echo "🚀 Deploying application..."
railway up

echo "✅ Deployment complete!"
echo "🌐 Your app should be available at: https://tg-fets-trading-bot-production.up.railway.app"
echo "📊 Monitor your deployment at: https://railway.app/project/[PROJECT_ID]"
