# Railway Deployment Guide for TG-Fets Trading Bot

## Overview
This guide will help you deploy your Telegram and X (Twitter) trading bot to Railway, a modern cloud platform that's often easier to use than Fly.io.

## Prerequisites
- [Railway account](https://railway.app/) (free tier available)
- Railway CLI installed (`npm install -g @railway/cli`)
- Your `.env` file with all required environment variables

## Quick Deployment

### Option 1: Automated Deployment (Recommended)
```bash
./deploy_railway.sh
```

### Option 2: Manual Deployment
```bash
# Login to Railway
railway login

# Initialize project
railway init --name "tg-fets-trading-bot"

# Set environment variables
railway variables set TELEGRAM_BOT_TOKEN="your_token"
railway variables set FIREBASE_CREDENTIALS="your_credentials"
# ... set all other variables

# Deploy
railway up
```

## Environment Variables Required

Make sure these are set in Railway dashboard or via CLI:

### Telegram Bot
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token

### Firebase
- `FIREBASE_CREDENTIALS` - Firebase service account JSON (base64 encoded)

### X (Twitter) API
- `X_BEARER_TOKEN` - Twitter API bearer token
- `X_API_KEY` - Twitter API key
- `X_API_SECRET` - Twitter API secret
- `X_ACCESS_TOKEN` - Twitter access token
- `X_ACCESS_TOKEN_SECRET` - Twitter access token secret

### Web3 Configuration
- `BSC_TEST_RPC_URL` - BSC Testnet RPC URL
- `BSC_RPC_URL` - BSC Mainnet RPC URL
- `ETH_RPC_URL` - Ethereum RPC URL

## Railway Configuration

### railway.json
- Uses Dockerfile for building
- Health check endpoint: `/health`
- Restart policy: Restart on failure with max 10 retries

### Dockerfile.railway
- Python 3.11 slim image
- Optimized for Railway deployment
- Includes health checks
- Non-root user for security

## Deployment Process

1. **Build**: Railway builds your Docker image
2. **Deploy**: Deploys to Railway's infrastructure
3. **Health Check**: Monitors the `/health` endpoint
4. **Auto-restart**: Restarts on failures

## Monitoring & Management

### View Logs
```bash
railway logs
```

### Check Status
```bash
railway status
```

### Redeploy
```bash
railway up
```

### Open Dashboard
```bash
railway open
```

## Benefits of Railway over Fly.io

1. **Easier Setup**: Simpler CLI commands
2. **Better UI**: Modern dashboard interface
3. **Auto-scaling**: Automatic resource management
4. **Git Integration**: Automatic deployments from Git
5. **Environment Variables**: Easy management via dashboard
6. **Logs**: Better log viewing and search
7. **Metrics**: Built-in performance monitoring

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Dockerfile syntax
   - Verify requirements.txt dependencies
   - Check for missing files

2. **Environment Variables**
   - Ensure all required variables are set
   - Check for typos in variable names
   - Verify sensitive data is properly encoded

3. **Health Check Failures**
   - Verify `/health` endpoint works locally
   - Check if port 8080 is exposed
   - Review application logs

4. **Dependencies Issues**
   - Update requirements.txt if needed
   - Check for version conflicts
   - Verify system dependencies in Dockerfile

### Getting Help

- Railway Documentation: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway
- Check logs: `railway logs --follow`

## Cost Optimization

- **Free Tier**: 500 hours/month
- **Pro Plan**: $5/month for unlimited usage
- **Team Plan**: $20/month for team collaboration

## Security Best Practices

1. Never commit `.env` files to Git
2. Use Railway's built-in secret management
3. Regularly rotate API keys
4. Monitor access logs
5. Use non-root user in Docker containers

## Next Steps

After successful deployment:

1. Test your bot's functionality
2. Monitor logs for any errors
3. Set up monitoring alerts
4. Configure auto-scaling if needed
5. Set up custom domain (optional)

## Support

If you encounter issues:
1. Check this guide first
2. Review Railway documentation
3. Check application logs
4. Contact Railway support
