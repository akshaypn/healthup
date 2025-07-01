# HealthUp EC2 Deployment Guide

This guide will walk you through deploying HealthUp to an AWS EC2 instance for production use.

## Prerequisites

- AWS Account
- Google Gemini API Key
- Basic knowledge of AWS EC2 and SSH

## Step 1: Launch EC2 Instance

### 1.1 Create EC2 Instance
1. Log into AWS Console
2. Go to EC2 Dashboard
3. Click "Launch Instance"
4. Configure the instance:
   - **Name**: `healthup-production`
   - **AMI**: Ubuntu Server 22.04 LTS (HVM)
   - **Instance Type**: `t3.medium` (2 vCPU, 4 GB RAM) or larger
   - **Key Pair**: Create or select an existing key pair
   - **Security Group**: Create new security group with these rules:
     - SSH (22): Your IP
     - HTTP (80): 0.0.0.0/0
     - HTTPS (443): 0.0.0.0/0
     - Custom TCP (3000): 0.0.0.0/0 (Frontend)
     - Custom TCP (8000): 0.0.0.0/0 (Backend API)
   - **Storage**: 20 GB GP3 (minimum)

### 1.2 Connect to Instance
```bash
# Replace with your key file and instance IP
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

## Step 2: Deploy Application

### 2.1 Clone Repository
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Git
sudo apt install git -y

# Clone the repository
git clone https://github.com/your-username/healthup.git
cd healthup
```

### 2.2 Run Deployment Script
```bash
# Make script executable
chmod +x deploy-ec2.sh

# Run deployment
./deploy-ec2.sh
```

The script will:
- Install Docker and Docker Compose
- Configure firewall
- Generate secure passwords
- Create environment file
- Start all services

### 2.3 Configure Environment
When prompted, edit the `.env` file:
```bash
nano .env
```

Add your Google Gemini API key:
```
GEMINI_API_KEY=your-actual-api-key-here
```

## Step 3: Verify Deployment

### 3.1 Check Service Status
```bash
# Check if all services are running
docker compose ps

# View logs
docker compose logs -f
```

### 3.2 Access Application
- **Frontend**: `http://your-ec2-public-ip:3000`
- **Backend API**: `http://your-ec2-public-ip:8000`
- **API Documentation**: `http://your-ec2-public-ip:8000/docs`

### 3.3 Test Mobile Access
Open `http://your-ec2-public-ip:3000` on your mobile device to test the mobile interface.

## Step 4: Production Enhancements (Optional)

### 4.1 Domain Name and SSL
1. Register a domain name (e.g., `yourhealthup.com`)
2. Point DNS to your EC2 instance
3. Install Certbot for SSL:
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourhealthup.com
```

### 4.2 Database Backups
Create automated backups:
```bash
# Create backup script
cat > backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker compose exec -T postgres pg_dump -U healthup healthup > $BACKUP_DIR/healthup_$DATE.sql
gzip $BACKUP_DIR/healthup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x backup-db.sh

# Add to crontab (daily backup at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/healthup/backup-db.sh") | crontab -
```

### 4.3 Monitoring
Install basic monitoring:
```bash
# Install htop for system monitoring
sudo apt install htop -y

# Monitor Docker containers
docker stats
```

## Step 5: Management Commands

### 5.1 Service Management
```bash
# View logs
docker compose logs -f

# Restart services
docker compose restart

# Stop services
docker compose down

# Update application
git pull
docker compose up -d --build
```

### 5.2 Database Management
```bash
# Access PostgreSQL
docker compose exec postgres psql -U healthup -d healthup

# Backup database
docker compose exec postgres pg_dump -U healthup healthup > backup.sql

# Restore database
docker compose exec -T postgres psql -U healthup -d healthup < backup.sql
```

## Step 6: Security Best Practices

### 6.1 Update Security Group
- Restrict SSH access to your IP only
- Consider using AWS Systems Manager Session Manager instead of SSH

### 6.2 Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker compose pull
docker compose up -d
```

### 6.3 Environment Variables
- Never commit `.env` files to version control
- Use AWS Secrets Manager for production secrets
- Rotate passwords regularly

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   sudo lsof -i :3000
   sudo lsof -i :8000
   
   # Kill process if needed
   sudo kill -9 <PID>
   ```

2. **Docker Permission Issues**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

3. **Database Connection Issues**
   ```bash
   # Check database logs
   docker compose logs postgres
   
   # Restart database
   docker compose restart postgres
   ```

4. **Memory Issues**
   ```bash
   # Check memory usage
   free -h
   
   # Increase swap if needed
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### Getting Help
- Check logs: `docker compose logs -f`
- Check system resources: `htop`
- Check network connectivity: `curl -I http://localhost:3000`

## Cost Optimization

### EC2 Instance Sizing
- **Development**: t3.micro (free tier)
- **Production**: t3.medium or t3.large
- **High Traffic**: t3.xlarge or larger

### Storage Optimization
- Use GP3 volumes for better performance
- Enable EBS optimization for larger instances
- Consider using EFS for shared storage

### Backup Strategy
- Use S3 for database backups
- Enable EBS snapshots
- Consider AWS Backup for automated backups

## Next Steps

1. **Set up monitoring** with CloudWatch
2. **Configure alerts** for system health
3. **Set up CI/CD** pipeline for automated deployments
4. **Implement load balancing** for high availability
5. **Add CDN** for better global performance

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs
3. Check AWS CloudWatch metrics
4. Create an issue in the GitHub repository 