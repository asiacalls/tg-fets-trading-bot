# Oracle Cloud Deployment Guide for TG-Fets Trading Bot

## Overview
This guide will help you deploy your Telegram trading bot to Oracle Cloud Infrastructure (OCI), which offers a generous Always Free tier perfect for hosting bots.

## Oracle Cloud Always Free Tier Benefits
- 2 AMD-based Compute VMs (1/8 OCPU and 1 GB memory each)
- OR 4 Arm-based Ampere A1 cores and 24 GB of memory
- 200 GB of Block Volume Storage
- 10 TB of outbound data transfer per month
- **Always Free** - No credit card expiration worries

## Prerequisites
- Oracle Cloud account ([sign up here](https://www.oracle.com/cloud/free/))
- Local machine with Docker installed
- SSH key pair for accessing your instance

## Quick Deployment

### Step 1: Prepare Deployment Package Locally
```bash
# Make the deployment script executable
chmod +x deploy_oracle.sh

# Build and package your bot
./deploy_oracle.sh
```

This will create:
- Docker image of your bot
- `oracle-deploy/` directory with all necessary files
- `tg-fets-bot.tar` (Docker image archive)

### Step 2: Create Oracle Cloud Compute Instance

1. **Login to Oracle Cloud Console**
   - Go to https://cloud.oracle.com
   - Sign in to your account

2. **Create a Compute Instance**
   - Navigate to: **Menu → Compute → Instances**
   - Click **Create Instance**
   
3. **Configure Instance**
   - **Name**: `tg-fets-bot`
   - **Image**: Ubuntu 22.04 (recommended)
   - **Shape**: 
     - For Always Free: `VM.Standard.E2.1.Micro` (AMD)
     - OR: `VM.Standard.A1.Flex` (ARM, 4 OCPUs, 24GB RAM - better option!)
   - **Add SSH Keys**: Upload or paste your public SSH key
   - **Boot Volume**: 50 GB (within free tier)

4. **Configure Network**
   - Use default VCN and subnet
   - **Assign a public IP address**: Yes
   - Note down the public IP address once created

5. **Configure Security Rules**
   - Navigate to: **VCN → Security Lists → Default Security List**
   - Add Ingress Rule:
     - **Source CIDR**: `0.0.0.0/0`
     - **IP Protocol**: TCP
     - **Destination Port**: 8080
     - **Description**: Bot health check port

### Step 3: Configure Firewall on Instance

After instance is created, SSH into it:
```bash
ssh ubuntu@YOUR_INSTANCE_PUBLIC_IP
```

Open required ports:
```bash
# Open port 8080 for health checks
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8080 -j ACCEPT
sudo netfilter-persistent save

# Alternative: Use firewalld (if using Oracle Linux)
# sudo firewall-cmd --permanent --add-port=8080/tcp
# sudo firewall-cmd --reload
```

Exit the SSH session:
```bash
exit
```

### Step 4: Upload Deployment Package

From your local machine:
```bash
# Upload the deployment directory
scp -r oracle-deploy ubuntu@YOUR_INSTANCE_PUBLIC_IP:~/

# Verify upload
ssh ubuntu@YOUR_INSTANCE_PUBLIC_IP "ls -lh oracle-deploy/"
```

### Step 5: Deploy on Oracle Instance

SSH into your instance:
```bash
ssh ubuntu@YOUR_INSTANCE_PUBLIC_IP
```

Navigate to deployment directory and run:
```bash
cd oracle-deploy
chmod +x run_oracle.sh
./run_oracle.sh
```

The script will:
1. Install Docker (if not already installed)
2. Load your bot's Docker image
3. Start the container with your environment variables
4. Show logs (press Ctrl+C to exit logs, bot continues running)

## Managing Your Bot

### View Logs
```bash
docker logs -f tg-fets-bot
```

### Stop Bot
```bash
docker stop tg-fets-bot
```

### Start Bot
```bash
docker start tg-fets-bot
```

### Restart Bot
```bash
docker restart tg-fets-bot
```

### Check Bot Status
```bash
docker ps
```

### Update Bot
When you have new code:
```bash
# On your local machine, rebuild and repackage
./deploy_oracle.sh

# Upload new package
scp oracle-deploy/tg-fets-bot.tar ubuntu@YOUR_INSTANCE_IP:~/oracle-deploy/

# On Oracle instance
ssh ubuntu@YOUR_INSTANCE_IP
cd oracle-deploy
./run_oracle.sh
```

## Troubleshooting

### Issue: Docker permission denied
**Solution**: 
```bash
sudo usermod -aG docker $USER
# Log out and back in, or run:
newgrp docker
```

### Issue: Container won't start
**Solution**: Check logs
```bash
docker logs tg-fets-bot
```

Common causes:
- Missing environment variables in `env.production`
- Firebase credentials not properly formatted
- Invalid API tokens

### Issue: Cannot connect to instance
**Solution**: 
1. Check Security List has port 22 open for SSH
2. Verify you're using correct SSH key
3. Check if instance is running in OCI console

### Issue: Health check fails
**Solution**: 
1. Ensure port 8080 is open in both:
   - OCI Security List
   - Instance firewall (iptables/firewalld)
2. Verify bot is listening on 8080:
   ```bash
   docker exec tg-fets-bot netstat -tlnp
   ```

### Issue: Out of memory
**Solution**: 
- Use Ampere A1 shape (24GB RAM) instead of Micro (1GB RAM)
- Monitor memory usage: `docker stats`
- Consider upgrading to paid tier if needed

## Monitoring

### Resource Usage
```bash
# Container resource usage
docker stats tg-fets-bot

# System resources
htop  # Install with: sudo apt install htop
```

### Set Up Automatic Restart
The bot is configured with `--restart unless-stopped`, so it will:
- Restart automatically if it crashes
- Restart automatically when instance reboots
- Not restart if you manually stop it

### Enable Automatic Updates
Create a cron job to pull updates (optional):
```bash
# Edit crontab
crontab -e

# Add this line to check for updates daily at 3 AM
0 3 * * * cd ~/oracle-deploy && docker pull tg-fets-bot:latest && docker restart tg-fets-bot
```

## Security Best Practices

1. **Use SSH Keys Only**
   - Disable password authentication
   - Use strong SSH key passphrases

2. **Keep System Updated**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **Limit SSH Access**
   - In Security List, restrict SSH (port 22) to your IP only
   - Use bastion host for production

4. **Environment Variables**
   - Never commit `env.production` to Git
   - Use strong encryption keys
   - Rotate API keys regularly

5. **Firewall Configuration**
   - Only open necessary ports
   - Use security groups effectively

6. **Monitor Logs**
   - Regularly check bot logs for suspicious activity
   - Set up log rotation to save disk space

## Cost Considerations

### Always Free Resources
Your bot fits well within Always Free tier:
- 1 Compute instance (Ampere A1 recommended)
- 50-100 GB boot volume
- Minimal network traffic

### Paid Upgrades (if needed)
- More compute power: ~$0.01/hour for additional cores
- More storage: ~$0.0255/GB/month
- Load balancer: ~$10/month

## Advanced Configuration

### Custom Domain Setup
1. Point your domain's A record to instance IP
2. Set up nginx reverse proxy:
   ```bash
   sudo apt install nginx
   # Configure nginx to proxy to port 8080
   ```

### SSL/TLS with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Backup Strategy
```bash
# Backup bot data
docker exec tg-fets-bot tar czf /tmp/bot-backup.tar.gz /app/data
docker cp tg-fets-bot:/tmp/bot-backup.tar.gz ~/backups/

# Automate with cron
0 4 * * * /home/ubuntu/backup-script.sh
```

## Comparison: Oracle vs Railway vs Fly.io

| Feature | Oracle Cloud | Railway | Fly.io |
|---------|-------------|---------|--------|
| Free Tier | Always Free (generous) | 500 hrs/month | Limited free tier |
| Setup Complexity | Moderate | Easy | Moderate |
| Control | Full VM access | Managed | Managed |
| Cost (after free) | Pay-as-you-go | $5/month base | Usage-based |
| Reliability | High | High | High |
| Best For | Long-term, cost-sensitive | Quick deploys | Global distribution |

## Next Steps

After successful deployment:

1. ✅ Test your bot's Telegram commands
2. ✅ Verify blockchain connections work
3. ✅ Test trading functionality (start with small amounts)
4. ✅ Monitor logs for 24 hours
5. ✅ Set up monitoring alerts (optional)
6. ✅ Configure automated backups
7. ✅ Document your instance IP and SSH details

## Support & Resources

- **Oracle Cloud Docs**: https://docs.oracle.com/en-us/iaas/
- **Oracle Cloud Free Tier**: https://www.oracle.com/cloud/free/
- **Docker Documentation**: https://docs.docker.com/
- **Community Forums**: https://community.oracle.com/

## Common Commands Reference

```bash
# Build deployment package
./deploy_oracle.sh

# Upload to Oracle instance
scp -r oracle-deploy ubuntu@IP:~/

# Deploy on instance
ssh ubuntu@IP
cd oracle-deploy && ./run_oracle.sh

# View logs
docker logs -f tg-fets-bot

# Restart bot
docker restart tg-fets-bot

# Check status
docker ps

# Update bot
./deploy_oracle.sh
scp oracle-deploy/tg-fets-bot.tar ubuntu@IP:~/oracle-deploy/
ssh ubuntu@IP "cd oracle-deploy && ./run_oracle.sh"
```

## Conclusion

Oracle Cloud offers an excellent, cost-effective platform for hosting your trading bot with:
- Generous Always Free tier
- Reliable infrastructure
- Full control over your environment
- No credit card expiration concerns

Follow this guide to deploy successfully, and enjoy your bot running 24/7 on Oracle Cloud!

