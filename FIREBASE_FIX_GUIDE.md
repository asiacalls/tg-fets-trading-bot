# 🔥 Firebase Authentication Fix Guide

## The Problem
Your Render deployment is showing this error:
```
google.auth.exceptions.RefreshError: ('invalid_grant: Invalid JWT Signature.', {'error': 'invalid_grant', 'error_description': 'Invalid JWT Signature.'})
```

## 🚀 Quick Fix

### Step 1: Generate Fresh Firebase Credentials

1. **Run the credential generator**:
   ```bash
   python fix_firebase_auth.py
   ```

2. **Copy the generated Base64 credentials**

### Step 2: Update Render Environment Variables

1. **Go to Render Dashboard**: https://render.com/dashboard
2. **Click on your service**: `tg-fets-trading-bot`
3. **Go to**: "Environment" tab
4. **Find**: `FIREBASE_CREDENTIALS` variable
5. **Replace with the generated credentials**
6. **Click**: "Save Changes"
7. **Wait 2-3 minutes** for automatic redeployment

## 🔍 Verify Other Environment Variables

Make sure these are also set correctly in Render:

| Variable | Value |
|----------|-------|
| `FIREBASE_DATABASE_URL` | `https://parivar-50ef1-default-rtdb.firebaseio.com/` |
| `TELEGRAM_BOT_TOKEN` | Your actual bot token |
| `ETH_RPC_URL` | `https://mainnet.infura.io/v3/7294966a87974f75ae25d7835d2eb8bb` |
| `BSC_RPC_URL` | `https://bsc-dataseed.binance.org/` |
| `BSC_TEST_RPC_URL` | `https://data-seed-prebsc-1-s1.binance.org:8545/` |
| `ENCRYPTION_KEY` | A 32-character string |
| `DEMO_MODE` | `false` |

## 🧪 Test Your Bot

After updating the environment variables:

1. **Health Check**: https://tg-fets-trading-bot.onrender.com/health
2. **Test Bot**: Send `/start` to your Telegram bot
3. **Check Logs**: Monitor Render logs for any remaining errors

## 🚨 If Still Not Working

### Option 1: Generate New Firebase Key
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `parivar-50ef1`
3. Go to Project Settings → Service Accounts
4. Click "Generate new private key"
5. Download the new JSON file
6. Replace `firebase_credentials.json` in your local project
7. Run `python fix_firebase_auth.py` again
8. Use the new generated credentials

### Option 2: Disable Firebase Temporarily
If you want to test the bot without Firebase:
1. Set `DEMO_MODE=true` in Render
2. This will disable Firebase operations temporarily

## 📊 Expected Results

After the fix, you should see:
- ✅ No more `RefreshError` in logs
- ✅ Bot responds to `/start` command
- ✅ Health check returns `200 OK`
- ✅ Firebase operations work correctly

## 🆘 Still Having Issues?

If you're still seeing errors:
1. Check Render logs for the exact error message
2. Verify all environment variables are set correctly
3. Make sure there are no extra spaces or characters in the credentials
4. Try regenerating the Firebase service account key

---

**Your bot is live at**: https://tg-fets-trading-bot.onrender.com
**Health check**: https://tg-fets-trading-bot.onrender.com/health
