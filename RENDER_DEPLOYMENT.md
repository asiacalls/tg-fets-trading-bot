# Render Deployment Guide for TG-Fets Trading Bot

## Overview
Deploy your Telegram trading bot to Render - a modern cloud platform with generous free tier and easy setup.

## Why Render?
- ✅ **Free Tier**: 750 hours/month free
- ✅ **Easy Setup**: Deploy from Git in minutes
- ✅ **Auto-Deploy**: Automatic deployments from GitHub
- ✅ **Built-in SSL**: HTTPS out of the box
- ✅ **Better than Railway**: No account limitations
- ✅ **Simple Management**: Great UI and monitoring

## Quick Deployment (Recommended)

### Option 1: Deploy from GitHub (Easiest)

1. **Push your code to GitHub** (if not already):
   ```bash
   git add .
   git commit -m "Add Render deployment config"
   git push origin main
   ```

2. **Sign up for Render**:
   - Go to https://render.com
   - Sign up with GitHub

3. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `tg-fets-bot` repository

4. **Configure Service**:
   - **Name**: `tg-fets-bot`
   - **Environment**: `Docker`
   - **Region**: Choose closest to you
   - **Branch**: `main` (or your default branch)
   - **Dockerfile Path**: `Dockerfile.render`
   - **Plan**: `Free`

5. **Add Environment Variables** (see section below)

6. **Deploy**: Click "Create Web Service"

### Option 2: Deploy with render.yaml (Blueprint)

1. **Push code to GitHub** (including `render.yaml`)

2. **Create from Blueprint**:
   - Go to Render Dashboard
   - Click "New +" → "Blueprint"
   - Connect your repository
   - Render will read `render.yaml` and set everything up
   - You'll just need to fill in environment variable values

## Required Environment Variables

Add these in Render Dashboard → Environment:

### 1. Telegram Configuration
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

### 2. Firebase Configuration
```bash
FIREBASE_CREDENTIALS=<base64_encoded_json>
FIREBASE_DATABASE_URL=https://parivar-50ef1-default-rtdb.firebaseio.com/
```

**To get FIREBASE_CREDENTIALS:**
```bash
python3 encode_firebase_creds.py
# Copy the output value
```

### 3. X (Twitter) API Configuration (Optional)
```bash
X_BEARER_TOKEN=your_x_bearer_token_here
X_API_KEY=your_x_api_key_here
X_API_SECRET=your_x_api_secret_here
X_ACCESS_TOKEN=your_x_access_token_here
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret_here
```

### 4. Blockchain RPC Configuration
```bash
ETH_RPC_URL=https://mainnet.infura.io/v3/7294966a87974f75ae25d7835d2eb8bb
BSC_RPC_URL=https://bsc-dataseed.binance.org/
BSC_TEST_RPC_URL=https://data-seed-prebsc-1-s1.binance.org:8545/
```

### 5. Security Configuration
```bash
ENCRYPTION_KEY=your-32-character-encryption-key-here-now
DEMO_MODE=false
```

## Step-by-Step Environment Variables Setup

1. **In Render Dashboard**:
   - Go to your service
   - Click "Environment" tab
   - Click "Add Environment Variable"

2. **Generate Firebase Credentials**:
   ```bash
   python3 encode_firebase_creds.py
   ```
   
3. **Copy each variable**:
   - Add `FIREBASE_CREDENTIALS` with the encoded value
   - Add other variables from your `.env` file

4. **Save Changes**: Click "Save Changes"

5. **Render will auto-deploy** with new variables

## Health Check Configuration

Render will automatically check `/health` endpoint:
- **Path**: `/health`
- **Initial Delay**: 30 seconds
- **Interval**: 30 seconds
- **Timeout**: 10 seconds

Your bot already has this endpoint configured.

## Monitoring Your Bot

### View Logs
1. Go to Render Dashboard
2. Select your service
3. Click "Logs" tab
4. View real-time logs

### Check Status
- **Events** tab shows deployment history
- **Metrics** tab shows resource usage
- **Shell** tab gives command line access

## Managing Your Deployment

### Redeploy
- Push to GitHub → Auto-deploys
- Or: Click "Manual Deploy" → "Deploy latest commit"

### Update Environment Variables
1. Go to "Environment" tab
2. Edit variables
3. Click "Save Changes"
4. Service auto-restarts

### Restart Service
- Click "Manual Deploy" → "Clear build cache & deploy"
- Or: Settings → Suspend → Resume

## Cost and Limits

### Free Tier Includes:
- 750 hours/month (enough for 24/7 operation)
- 512 MB RAM
- 0.5 CPU
- Free SSL
- Automatic scaling

### If You Need More:
- **Starter**: $7/month (1GB RAM, 1 CPU)
- **Standard**: $25/month (2GB RAM, 2 CPU)

For a bot, **Free tier is usually sufficient**.

## Troubleshooting

### Deployment Fails

**Check Build Logs:**
1. Go to "Events" tab
2. Click on failed deployment
3. Review error messages

**Common Issues:**
- Missing dependencies in `requirements.txt`
- Incorrect Dockerfile path
- Missing environment variables

### Firebase Connection Errors

**If you see "Invalid JWT Signature":**
```bash
# Regenerate credentials
python3 encode_firebase_creds.py

# Update FIREBASE_CREDENTIALS in Render
# Save and redeploy
```

### Bot Not Responding

**Check if bot is running:**
1. View Logs
2. Look for "Bot started successfully" message
3. Check for error messages

**Common fixes:**
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check all environment variables are set
- Review logs for specific errors

### Out of Memory

**Free tier has 512MB RAM:**
- Monitor in Metrics tab
- If consistently hitting limit, upgrade to Starter plan
- Or optimize your code/reduce memory usage

## Advantages Over Railway

| Feature | Render | Railway |
|---------|--------|---------|
| Free Tier | 750 hrs/month | Limited (your account blocked) |
| Account Issues | None | Account limitations |
| Setup | Very easy | Easy |
| Monitoring | Excellent dashboard | Good |
| Auto-deploy | Yes (from Git) | Yes |
| Pricing | $7/mo starter | $5/mo base |

## Security Best Practices

1. **Never commit `.env` files**
   ```bash
   # Ensure .env is in .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use Render's secret management**
   - All env vars are encrypted at rest
   - Not visible in logs

3. **Rotate keys regularly**
   - Update Telegram bot token periodically
   - Rotate Firebase credentials
   - Update encryption keys

4. **Monitor logs**
   - Check for unauthorized access attempts
   - Watch for unusual activity

## Advanced Configuration

### Custom Domain
1. Go to Settings → Custom Domain
2. Add your domain
3. Configure DNS records
4. Render handles SSL automatically

### Persistent Disk (if needed)
1. Settings → Disks
2. Add persistent disk
3. Mount at `/app/data`
4. Store persistent data here

### Scheduled Tasks (Cron Jobs)
1. Create a new "Cron Job" service
2. Use same Docker image
3. Set schedule (e.g., `0 0 * * *` for daily)
4. Specify command to run

### Environment-specific Configs
```bash
# Add to Render env vars
ENVIRONMENT=production

# In your code:
if os.getenv('ENVIRONMENT') == 'production':
    # Production settings
```

## Deployment Checklist

Before deploying, ensure:

- [ ] Code pushed to GitHub
- [ ] `render.yaml` is in repository root
- [ ] `Dockerfile.render` exists
- [ ] Firebase credentials encoded
- [ ] All environment variables ready
- [ ] `.env` not committed to Git
- [ ] Bot token is valid
- [ ] Firebase project is active

## Post-Deployment Testing

After deployment:

1. **Check deployment status** in Render Dashboard
2. **View logs** to ensure bot started successfully
3. **Test Telegram bot** with `/start` command
4. **Verify wallet creation** works
5. **Test token scanning** with a known token
6. **Check Firebase** data is being saved
7. **Monitor for errors** in first hour

## Comparison with Other Platforms

### Render vs Oracle Cloud
- **Render**: Managed, easier, automatic scaling
- **Oracle**: More control, more powerful free tier (24GB RAM)

### Render vs Fly.io
- **Render**: Better free tier, easier setup
- **Fly.io**: Better for global distribution

### Render vs Railway (Your Case)
- **Render**: No account limitations ✅
- **Railway**: Your account is blocked ❌

## Getting Help

### Render Support
- Documentation: https://render.com/docs
- Community: https://community.render.com
- Status: https://status.render.com

### Bot Issues
- Check logs in Render Dashboard
- Review `FIREBASE_FIX.md` for Firebase issues
- Test locally first: `python3 new_bot.py`

## Next Steps

1. ✅ Create Render account
2. ✅ Connect GitHub repository
3. ✅ Generate Firebase credentials
4. ✅ Add environment variables
5. ✅ Deploy!
6. ✅ Test your bot
7. ✅ Monitor logs

## Quick Commands Reference

```bash
# Generate Firebase credentials
python3 encode_firebase_creds.py

# Test bot locally
python3 new_bot.py

# Push to GitHub (triggers auto-deploy)
git add .
git commit -m "Update bot"
git push origin main

# Check requirements are up to date
pip freeze > requirements.txt
```

## Conclusion

Render is the perfect choice for your bot because:
- ✅ Easy setup (5 minutes to deploy)
- ✅ No account limitations (unlike Railway)
- ✅ Free tier is generous
- ✅ Auto-deploys from Git
- ✅ Great monitoring and logs
- ✅ Production-ready infrastructure

Follow this guide and you'll have your bot running on Render in minutes!

---

**Ready to deploy? Let's go! 🚀**

