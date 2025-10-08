# 🚀 Deploy TG-Bot-Fets to Fly.io

This guide will help you deploy your Telegram bot with X (Twitter) bot integration to Fly.io for continuous cloud operation.

## 📋 Prerequisites

1. **Fly.io Account**: Sign up at [fly.io](https://fly.io)
2. **Fly CLI**: Install the Fly.io command line tool
3. **Environment Variables**: Ensure your `.env` file is properly configured

## 🛠️ Quick Deployment

### Option 1: Automated Deployment (Recommended)

```bash
# Run the automated deployment script
./deploy.sh
```

This script will:
- ✅ Install Fly CLI if needed
- ✅ Create the Fly.io app
- ✅ Set up persistent storage
- ✅ Configure secrets from your `.env` file
- ✅ Deploy the application

### Option 2: Manual Deployment

```bash
# 1. Install Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. Login to Fly.io
fly auth login

# 3. Create the app
fly apps create tg-bot-fets --org personal

# 4. Create persistent volume
fly volumes create tg_bot_data --size 1 --region iad

# 5. Set secrets manually
fly secrets set TELEGRAM_BOT_TOKEN="your_token" --app tg-bot-fets
fly secrets set X_BEARER_TOKEN="your_token" --app tg-bot-fets
fly secrets set X_API_KEY="your_key" --app tg-bot-fets
fly secrets set X_API_SECRET="your_secret" --app tg-bot-fets
fly secrets set X_ACCESS_TOKEN="your_token" --app tg-bot-fets
fly secrets set X_ACCESS_TOKEN_SECRET="your_secret" --app tg-bot-fets
fly secrets set FIREBASE_CREDENTIALS_PATH="your_path" --app tg-bot-fets
fly secrets set FIREBASE_DATABASE_URL="your_url" --app tg-bot-fets
fly secrets set ENCRYPTION_KEY="your_key" --app tg-bot-fets

# 6. Deploy
fly deploy
```

## 🔧 Configuration Files

### Dockerfile
- Uses Python 3.11 slim image
- Installs system dependencies
- Runs as non-root user for security
- Exposes port 8080 for health checks

### fly.toml
- App name: `tg-bot-fets`
- Primary region: `iad` (Washington DC)
- VM specs: 1 CPU, 512MB RAM
- Auto-scaling: 1 machine minimum
- Health checks every 30 seconds

### .dockerignore
- Excludes development files
- Excludes test files and documentation
- Optimizes Docker build size

## 🌐 Health Monitoring

Your deployed bot will have a health check endpoint:

```
https://tg-bot-fets.fly.dev/health
```

Health check response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-28T10:30:00Z",
  "bot_running": true,
  "x_bot_running": true,
  "components_initialized": true,
  "last_tweet_id": "1960990669154951320"
}
```

## 📊 Management Commands

```bash
# Check app status
fly status --app tg-bot-fets

# View logs
fly logs --app tg-bot-fets

# Scale the app
fly scale count 2 --app tg-bot-fets

# Restart the app
fly apps restart tg-bot-fets

# Update secrets
fly secrets set NEW_SECRET="value" --app tg-bot-fets

# View app info
fly info --app tg-bot-fets
```

## 🔍 Troubleshooting

### Common Issues

1. **Build Failures**
```bash
   # Check build logs
   fly logs --app tg-bot-fets
   
   # Rebuild and deploy
   fly deploy --app tg-bot-fets
   ```

2. **Runtime Errors**
```bash
   # View real-time logs
   fly logs --app tg-bot-fets --follow
   
   # Check health endpoint
   curl https://tg-bot-fets.fly.dev/health
   ```

3. **Secret Issues**
```bash
   # List current secrets
   fly secrets list --app tg-bot-fets

   # Remove and re-add secrets
   fly secrets unset SECRET_NAME --app tg-bot-fets
   fly secrets set SECRET_NAME="value" --app tg-bot-fets
```

### Performance Optimization

1. **Scale Up**: Increase RAM/CPU if needed
```bash
   fly scale memory 1024 --app tg-bot-fets
   fly scale cpu 2 --app tg-bot-fets
   ```

2. **Auto-scaling**: Enable automatic scaling
   ```bash
   fly scale count 1-5 --app tg-bot-fets
   ```

## 🔐 Security Features

- ✅ Non-root user execution
- ✅ Environment variables as secrets
- ✅ HTTPS enforced
- ✅ Health check monitoring
- ✅ Automatic restarts on failure

## 💰 Cost Optimization

- **Free Tier**: 3 shared-cpu-1x 256mb VMs
- **Shared CPU**: $1.94/month per VM
- **Dedicated CPU**: $7.50/month per VM
- **Storage**: $0.15/GB/month

**Recommended**: Start with 1 shared-cpu-1x VM (~$2/month)

## 🚀 What Happens After Deployment

1. **Bot Startup**: Telegram bot initializes and connects
2. **X Bot Activation**: Twitter monitoring begins automatically
3. **Health Monitoring**: Fly.io monitors the `/health` endpoint
4. **Auto-restart**: App restarts automatically if it crashes
5. **Continuous Operation**: Bot runs 24/7 in the cloud

## 📱 Monitoring Your Bot

- **Telegram**: Send `/start` to test bot functionality
- **Health Check**: Visit health endpoint to see status
- **Logs**: Monitor real-time logs for any issues
- **Metrics**: View performance metrics in Fly.io dashboard

## 🔄 Updates and Maintenance

```bash
# Update code and redeploy
git pull origin main
fly deploy --app tg-bot-fets

# Update secrets
fly secrets set UPDATED_SECRET="new_value" --app tg-bot-fets

# Restart for changes
fly apps restart tg-bot-fets
```

## 🎯 Benefits of Fly.io Deployment

- ✅ **24/7 Operation**: Bot runs continuously
- ✅ **Auto-scaling**: Handles traffic spikes
- ✅ **Global CDN**: Fast response times worldwide
- ✅ **Health Monitoring**: Automatic restarts on failure
- ✅ **Cost Effective**: Pay only for what you use
- ✅ **Easy Management**: Simple CLI commands
- ✅ **Persistent Storage**: Data survives restarts

---

**Ready to deploy?** Run `./deploy.sh` and your bot will be live on Fly.io in minutes! 🚀
