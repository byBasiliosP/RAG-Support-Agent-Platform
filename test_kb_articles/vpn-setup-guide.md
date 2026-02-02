# VPN Setup and Troubleshooting

## Summary
Complete guide for setting up and troubleshooting VPN connections for remote access to company resources.

## Overview
Our company uses Cisco AnyConnect VPN to provide secure remote access to internal systems. This guide covers installation, configuration, and common troubleshooting steps.

## VPN Client Installation

### Windows Installation
1. Download Cisco AnyConnect from https://vpn.company.com
2. Run the installer as Administrator
3. Accept the license agreement
4. Follow the installation wizard
5. Restart your computer when prompted

### macOS Installation
1. Download the macOS client from the VPN portal
2. Open the .dmg file
3. Drag AnyConnect to Applications folder
4. Launch from Applications
5. Enter admin password when prompted

### Mobile Installation
**iOS:**
1. Download "Cisco AnyConnect" from App Store
2. Install and open the app
3. Add server: vpn.company.com
4. Enter your company credentials

**Android:**
1. Download from Google Play Store
2. Open AnyConnect app
3. Tap "Add New VPN Connection"
4. Server: vpn.company.com

## Configuration Settings

### Server Information
- **Primary Server**: vpn.company.com
- **Backup Server**: vpn-backup.company.com
- **Port**: 443 (HTTPS)
- **Protocol**: SSL/TLS

### Authentication
- **Username**: Your company username
- **Password**: Your company password
- **Two-Factor**: Required (use authenticator app)

## Connection Steps
1. Open Cisco AnyConnect
2. Enter server address: vpn.company.com
3. Click "Connect"
4. Enter username and password
5. Enter 6-digit code from authenticator app
6. Wait for "Connected" status

## Troubleshooting Common Issues

### Issue: Cannot connect to VPN server
**Diagnostic Steps:**
1. Check internet connection
2. Verify server address spelling
3. Try backup server: vpn-backup.company.com
4. Disable firewall temporarily
5. Check with IT if server is operational

**Solutions:**
- Restart network adapter
- Flush DNS cache: `ipconfig /flushdns` (Windows)
- Reset network settings on mobile devices
- Contact IT: (555) 123-4567

### Issue: Connection drops frequently
**Causes:**
- Weak internet connection
- Power management settings
- Firewall interference
- Network congestion

**Solutions:**
1. Disable power management for network adapter
2. Change VPN protocol to IKEv2
3. Increase connection timeout
4. Move closer to WiFi router

### Issue: Slow connection speed
**Optimization Tips:**
1. Connect to nearest VPN server
2. Use wired connection instead of WiFi
3. Close unnecessary applications
4. Check bandwidth usage: https://speedtest.company.com

### Issue: Cannot access internal resources
**Troubleshooting:**
1. Verify VPN connection is active
2. Check IP address: Should start with 10.0.x.x
3. Try accessing by IP instead of hostname
4. Ping internal server: `ping 10.0.1.100`
5. Check DNS settings

## Split Tunneling Configuration
For advanced users who need local and VPN traffic:

1. Open AnyConnect
2. Click gear icon → Preferences
3. Enable "Allow local LAN access"
4. Configure specific routes if needed

## Security Best Practices
- Always disconnect when not needed
- Use strong passwords
- Keep client software updated
- Report suspicious activity
- Don't share VPN credentials

## Performance Optimization
- **Best server locations**: 
  - East Coast: vpn-east.company.com
  - West Coast: vpn-west.company.com
  - Central: vpn-central.company.com
- **Recommended protocols**: IKEv2 for mobile, SSL for desktop
- **Bandwidth allocation**: Reserve 20% for VPN overhead

## Contact Information
- **VPN Support**: (555) 123-4567 ext. 2
- **Email**: vpn-support@company.com
- **24/7 Emergency**: (555) 987-6543
- **Hours**: Monday-Sunday 24/7
- **Self-Service Portal**: https://vpn.company.com/support

## FAQ

**Q: Can I use VPN on multiple devices?**
A: Yes, up to 3 simultaneous connections per user.

**Q: Does VPN work internationally?**
A: Yes, but performance may vary by location.

**Q: What ports need to be open?**
A: TCP 443 (HTTPS) and UDP 443 (DTLS)

## Related Articles
- Multi-Factor Authentication Setup
- Remote Desktop Connection Guide
- Network Drive Mapping
- Email Client Configuration

## Last Updated
Created: June 8, 2025
Updated: June 8, 2025
Category: Network & Connectivity
Priority: High