# HealthUp Scripts

This directory contains all deployment, setup, and utility scripts for the HealthUp application.

## 📁 Script Files

### 🚀 **Production Deployment Scripts**
- `ec2-production-setup.sh` - **Main production setup script** for EC2 deployment
- `deploy-ec2.sh` - EC2 deployment automation script
- `deploy-tailscale.sh` - Tailscale VPN deployment script
- `quick-tailscale-setup.sh` - Quick Tailscale setup for development

### 🔧 **Setup & Configuration Scripts**
- `ec2-quick-setup.sh` - Quick EC2 instance setup
- `ec2-troubleshoot.sh` - EC2 troubleshooting and diagnostics
- `network-setup.sh` - Network configuration setup
- `start.sh` - Application startup script
- `set-ip.sh` - IP address configuration script

### 👤 **Administration Scripts**
- `create-admin.sh` - Admin user creation script

## 🎯 **Quick Reference**

### **Production Deployment**
```bash
# Main production setup (recommended)
./scripts/ec2-production-setup.sh

# Alternative EC2 deployment
./scripts/deploy-ec2.sh

# Tailscale VPN deployment
./scripts/deploy-tailscale.sh
```

### **Development Setup**
```bash
# Quick Tailscale setup
./scripts/quick-tailscale-setup.sh

# Network configuration
./scripts/network-setup.sh

# Start application
./scripts/start.sh
```

### **Administration**
```bash
# Create admin user
./scripts/create-admin.sh

# Troubleshoot EC2 issues
./scripts/ec2-troubleshoot.sh
```

## 📋 **Script Categories**

### **Production Deployment**
- **EC2 Production Setup**: Comprehensive production deployment with testing
- **EC2 Deployment**: Automated EC2 instance deployment
- **Tailscale Deployment**: VPN setup for secure access

### **Development & Testing**
- **Quick Setup**: Fast development environment setup
- **Network Configuration**: Network and connectivity setup
- **Application Startup**: Service startup and management

### **Maintenance & Troubleshooting**
- **EC2 Troubleshooting**: Diagnostic tools for EC2 issues
- **IP Configuration**: Network address management
- **Admin Management**: User administration tools

## 🔧 **Script Usage**

### **ec2-production-setup.sh** (Main Script)
```bash
# Run from project root
./scripts/ec2-production-setup.sh

# Features:
# - Automatic EC2 IP detection
# - Environment variable generation
# - Service configuration
# - Comprehensive testing
# - Systemd service creation
# - Monitoring script generation
```

### **deploy-ec2.sh**
```bash
# EC2 deployment automation
./scripts/deploy-ec2.sh

# Features:
# - Instance setup
# - Docker installation
# - Service deployment
# - Configuration management
```

### **deploy-tailscale.sh**
```bash
# Tailscale VPN deployment
./scripts/deploy-tailscale.sh

# Features:
# - VPN setup
# - Network configuration
# - Security setup
# - Access management
```

## 🛡️ **Security Considerations**

### **Environment Variables**
- Scripts use secure environment variable handling
- Sensitive data is not hardcoded
- API keys are managed securely

### **Access Control**
- Scripts include proper permission checks
- Root access is required for system-level operations
- User creation follows security best practices

### **Network Security**
- VPN setup for secure remote access
- Firewall configuration included
- Secure communication protocols

## 📊 **Script Dependencies**

### **System Requirements**
- **Docker**: Required for containerized deployment
- **Docker Compose**: For multi-service orchestration
- **Bash**: All scripts are bash-compatible
- **curl**: For API calls and downloads
- **git**: For repository management

### **External Services**
- **AWS EC2**: For cloud deployment
- **Tailscale**: For VPN access
- **GitHub**: For code repository

## 🔗 **Related Resources**

- **Documentation**: Check `../docs/` for detailed guides
- **Tests**: Visit `../tests/` for testing scripts
- **Configuration**: See `../docker-compose.yml` for service config
- **Environment**: Check `../env.production.example` for environment setup

## 📝 **Script Standards**

All scripts follow these standards:
- **Error handling** with proper exit codes
- **Logging** with timestamps and status messages
- **Input validation** for user-provided data
- **Documentation** with clear usage instructions
- **Modularity** for easy maintenance and updates

## 🤝 **Contributing to Scripts**

When adding new scripts:
1. Include comprehensive error handling
2. Add usage documentation and examples
3. Follow consistent naming conventions
4. Update this README with new script entries
5. Test thoroughly before committing 