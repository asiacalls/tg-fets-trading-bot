# Firebase "Invalid JWT Signature" Fix

## Problem
You were getting this error:
```
google.auth.exceptions.RefreshError: ('invalid_grant: Invalid JWT Signature.')
```

This happens when Firebase private key newlines get corrupted during deployment.

## What Was Fixed

1. **Updated `firebase_manager.py`**:
   - Properly formats private key with correct line breaks
   - Supports 3 credential loading methods:
     - Environment variable (FIREBASE_CREDENTIALS - base64 encoded)
     - File (firebase_credentials.json)
     - Hardcoded fallback with proper formatting

2. **Created `encode_firebase_creds.py`**:
   - Helper script to properly encode credentials for deployment
   - Generates base64-encoded credentials for environment variables

3. **Updated Oracle deployment**:
   - Automatically encodes and includes Firebase credentials

## Quick Fix for Current Deployment

If you're currently deployed and getting this error:

### Option 1: Use Encoded Credentials (Recommended)

```bash
# Generate encoded credentials
python3 encode_firebase_creds.py

# This creates: firebase_creds_encoded.txt
# Copy the FIREBASE_CREDENTIALS value and add it to your deployment platform
```

**For Render/Railway/Fly.io:**
1. Go to your app's environment variables
2. Add: `FIREBASE_CREDENTIALS=<paste_the_encoded_value>`
3. Redeploy

### Option 2: Redeploy with Fixed Code

Simply redeploy with the updated `firebase_manager.py` - it now has the fix built in.

## Deploy to Oracle Cloud (Fresh Start)

Since Railway is limiting your account, here's how to deploy to Oracle Cloud:

```bash
# Step 1: Build deployment package
./deploy_oracle.sh

# This will:
# - Build Docker image
# - Encode Firebase credentials automatically
# - Package everything in oracle-deploy/

# Step 2: Set up Oracle Cloud instance (see ORACLE_DEPLOYMENT.md)
# - Create free tier account
# - Launch Ampere A1 instance (4 CPU, 24GB RAM - FREE!)
# - Note the public IP

# Step 3: Upload to Oracle
scp -r oracle-deploy ubuntu@YOUR_INSTANCE_IP:~/

# Step 4: Deploy on Oracle
ssh ubuntu@YOUR_INSTANCE_IP
cd oracle-deploy
./run_oracle.sh
```

## Testing the Fix Locally

```bash
# Test if Firebase works now
python3 -c "from firebase_manager import FirebaseManager; fm = FirebaseManager(); print('✅ Firebase connected!')"
```

## Environment Variable Format

Your environment should have:

```bash
# Either this (for local/file-based):
FIREBASE_CREDENTIALS_PATH=firebase_credentials.json
FIREBASE_DATABASE_URL=https://parivar-50ef1-default-rtdb.firebaseio.com/

# OR this (for cloud deployment):
FIREBASE_CREDENTIALS=<base64_encoded_json>
FIREBASE_DATABASE_URL=https://parivar-50ef1-default-rtdb.firebaseio.com/
```

## Why This Happened

The Firebase private key contains:
```
-----BEGIN PRIVATE KEY-----
...multiple lines of encoded data...
-----END PRIVATE KEY-----
```

When stored as a single-line string with `\n` characters, deployment platforms sometimes:
- Remove the `\n` characters
- Escape them as `\\n`
- Convert them to spaces

This breaks the JWT signature validation. The fix ensures the private key is properly formatted regardless of how it's stored.

## Next Steps

1. ✅ Fix applied to `firebase_manager.py`
2. ✅ Helper script created for encoding credentials
3. ✅ Oracle deployment scripts updated
4. 🚀 Ready to deploy to Oracle Cloud!

Choose your deployment platform:
- **Oracle Cloud** - Free forever, powerful (recommended)
- **Render** - Easy to use, free tier available
- **Fly.io** - Good for global distribution
- **Railway** - Currently limiting your account

See `ORACLE_DEPLOYMENT.md` for complete Oracle Cloud setup guide.

