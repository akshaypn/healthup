# HealthUp Tailscale Server Deployment Guide

## Overview

This guide will help you deploy the HealthUp application on your Tailscale server (`100.123.199.100`) with proper session management using httpOnly cookies.

## Prerequisites

### On Your Tailscale Server

1. **Docker and Docker Compose**
   ```bash
   # Install Docker (Ubuntu/Debian)
   sudo apt update
   sudo apt install docker.io docker-compose-plugin
   sudo systemctl enable docker
   sudo systemctl start docker
   sudo usermod -aG docker $USER
   ```

2. **Git**
   ```bash
   sudo apt install git
   ```

3. **Curl and JQ (for testing)**
   ```bash
   sudo apt install curl jq
   ```

### Tailscale Setup

Ensure your Tailscale server is properly configured:
```bash
# Check Tailscale status
sudo tailscale status

# Your server should show as online:
# 100.123.199.100 akshaythinkpad akshay.nambiar7@ linux -
```

## Deployment Steps

### Step 1: Clone and Prepare the Repository

```bash
# Clone the repository on your Tailscale server
git clone <your-repo-url>
cd healthup

# Make deployment scripts executable
chmod +x deploy-tailscale.sh
chmod +x test-tailscale-session.sh
```

### Step 2: Deploy the Application

```bash
# Run the deployment script
./deploy-tailscale.sh
```

This script will:
- ✅ Check prerequisites (Docker, connectivity)
- ✅ Create production environment configuration
- ✅ Update Docker Compose for Tailscale
- ✅ Build and start all services
- ✅ Create admin user (admin@admin.com / 123456)
- ✅ Test session management and cookies
- ✅ Display access information

### Step 3: Verify Deployment

```bash
# Test session management and cookies
./test-tailscale-session.sh
```

This comprehensive test will verify:
- ✅ Health check
- ✅ User registration and login
- ✅ Cookie setting and management
- ✅ Token refresh functionality
- ✅ Logout and cookie clearing
- ✅ Security properties

## Access Information

After successful deployment, you can access:

- **Frontend**: http://100.123.199.100:3000
- **Backend API**: http://100.123.199.100:8000
- **Health Check**: http://100.123.199.100:8000/health

### Admin Credentials
- **Email**: admin@admin.com
- **Password**: 123456

## Session Management Features

### Cookie-Based Authentication
- **httpOnly Cookies**: Tokens stored in secure httpOnly cookies
- **2-Week Sessions**: Long-lasting login sessions (20,160 minutes)
- **30-Day Refresh**: Extended refresh tokens for trusted devices
- **Automatic Refresh**: Seamless token renewal without user intervention

### Security Features
- **XSS Protection**: httpOnly cookies prevent JavaScript access
- **CSRF Protection**: SameSite attribute prevents cross-site requests
- **Secure Configuration**: Properly configured for Tailscale HTTP environment

## Configuration Details

### Environment Variables (Auto-generated)

The deployment script creates a `.env` file with:

```bash
# Database
POSTGRES_PASSWORD=healthup_secure_password_[random]
DATABASE_URL=postgresql://healthup:healthup@postgres/healthup

# Security
SECRET_KEY=[random-32-byte-key]
ACCESS_TOKEN_EXPIRE_MINUTES=20160  # 2 weeks
REFRESH_TOKEN_EXPIRE_DAYS=30

# Cookie Configuration (HTTP for Tailscale)
COOKIE_SECURE=false
COOKIE_DOMAIN=
COOKIE_SAMESITE=lax

# CORS Configuration
CORS_ORIGINS=http://100.123.199.100:3000

# API Configuration
API_URL=http://100.123.199.100:8000
VITE_API_URL=http://100.123.199.100:8000
```

### Docker Services

The deployment includes:
- **PostgreSQL**: Database (port 5433)
- **Redis**: Cache and Celery broker (port 6380)
- **Backend**: FastAPI application (port 8000)
- **Frontend**: React PWA (port 3000)
- **Celery Worker**: Background task processing
- **Celery Beat**: Scheduled task scheduler

## Management Commands

### Service Management
```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f

# Restart services
docker compose restart

# Stop services
docker compose down

# Update and restart
docker compose up -d --build
```

### Testing Commands
```bash
# Test session management
./test-tailscale-session.sh

# Test specific functionality
curl -X POST http://100.123.199.100:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@admin.com","password":"123456"}' \
  -c cookies.txt

# Test authenticated access
curl -X GET http://100.123.199.100:8000/auth/me \
  -b cookies.txt
```

## Troubleshooting

### Common Issues

#### 1. Services Not Starting
```bash
# Check Docker status
sudo systemctl status docker

# Check container logs
docker compose logs backend
docker compose logs frontend
```

#### 2. Cookie Issues
```bash
# Verify cookie configuration
grep -E "(COOKIE_SECURE|COOKIE_DOMAIN)" .env

# Test cookie setting
curl -v -X POST http://100.123.199.100:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@admin.com","password":"123456"}' \
  -c cookies.txt
```

#### 3. CORS Issues
```bash
# Check CORS configuration
grep CORS_ORIGINS .env

# Test from browser console
fetch('http://100.123.199.100:8000/auth/me', {
  credentials: 'include'
})
```

#### 4. Database Issues
```bash
# Check database connectivity
docker compose exec postgres psql -U healthup -d healthup -c "SELECT 1;"

# Reset database (if needed)
docker compose down -v
docker compose up -d
```

### Debug Commands

#### Check Cookie Properties
```bash
# In browser console
document.cookie

# Check specific cookies
curl -v -b cookies.txt http://100.123.199.100:8000/auth/me
```

#### Monitor Authentication Flow
```bash
# Watch authentication logs
docker compose logs -f backend | grep -E "(login|auth|token)"
```

## Security Considerations

### Tailscale Security
- ✅ **Private Network**: All traffic stays within Tailscale network
- ✅ **No Public Exposure**: Services not exposed to internet
- ✅ **Encrypted Traffic**: Tailscale provides end-to-end encryption

### Application Security
- ✅ **httpOnly Cookies**: Prevents XSS attacks
- ✅ **Secure Token Storage**: Tokens not accessible via JavaScript
- ✅ **Automatic Refresh**: Reduces token exposure window
- ✅ **Proper CORS**: Configured for Tailscale domain

### Production Recommendations
- 🔒 **Regular Updates**: Keep Docker images updated
- 🔒 **Monitor Logs**: Watch for suspicious authentication patterns
- 🔒 **Backup Database**: Regular PostgreSQL backups
- 🔒 **Rotate Secrets**: Periodically update SECRET_KEY

## Monitoring and Maintenance

### Health Checks
```bash
# Application health
curl http://100.123.199.100:8000/health

# Database health
docker-compose exec postgres pg_isready -U healthup

# Redis health
docker-compose exec redis redis-cli ping
```

### Log Monitoring
```bash
# Real-time logs
docker compose logs -f

# Authentication logs
docker compose logs backend | grep -E "(login|logout|refresh)"

# Error logs
docker compose logs backend | grep -E "(ERROR|WARNING)"
```

### Performance Monitoring
```bash
# Container resource usage
docker stats

# Database performance
docker compose exec postgres psql -U healthup -d healthup -c "
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'public';"
```

## Backup and Recovery

### Database Backup
```bash
# Create backup
docker compose exec postgres pg_dump -U healthup healthup > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker compose exec -T postgres psql -U healthup healthup < backup_file.sql
```

### Configuration Backup
```bash
# Backup configuration
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup
```

## Support and Updates

### Updating the Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose down
docker compose up -d --build
```

### Getting Help
- Check logs: `docker compose logs -f`
- Run tests: `./test-tailscale-session.sh`
- Review configuration: `cat .env`

## Conclusion

Your HealthUp application is now deployed on your Tailscale server with:
- ✅ Secure session management using httpOnly cookies
- ✅ 2-week login sessions with automatic refresh
- ✅ Proper security configuration for Tailscale environment
- ✅ Comprehensive testing and monitoring tools
- ✅ Easy management and maintenance commands

The application is accessible at:
- **Frontend**: http://100.123.199.100:3000
- **Backend**: http://100.123.199.100:8000

Login with admin@admin.com / 123456 to start using the application! 