# Security Quick Reference

Quick guide to the security features in EVE University Wiki MCP Server v1.1.0+

## 🔒 Security Features at a Glance

| Feature | Status | Default | Configurable |
|---------|--------|---------|--------------|
| Input Validation | ✅ Always On | Enabled | No |
| Rate Limiting | ✅ Always On | 60 req/min | Yes |
| Authentication | ⚙️ Optional | Disabled | Yes |
| CORS | ⚙️ Optional | Disabled | Yes |
| URL Encoding | ✅ Always On | Enabled | No |
| Error Sanitization | ✅ Always On | Enabled | No |
| Non-root Container | ✅ Always On | Enabled | No |

## ⚡ Quick Setup

### Minimal (Local Network Only)
```bash
# No additional configuration needed
docker-compose up -d
```

### Recommended (With Authentication)
```bash
# Generate a secure token
openssl rand -hex 32

# Add to .env
echo "MCP_AUTH_TOKEN=<your-token-here>" >> .env

# Start server
docker-compose up -d
```

### Maximum Security (External Access)
```bash
# In .env file:
MCP_AUTH_TOKEN=<secure-token>
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_WINDOW=60
CORS_ORIGINS=https://your-domain.com

# Use with reverse proxy for HTTPS
# See SECURITY.md for proxy configuration
```

## 🔑 Authentication

### Enable Authentication
```bash
# In .env
MCP_AUTH_TOKEN=your-secret-token-here
```

### Client Usage
```bash
# Include in request headers
Authorization: Bearer your-secret-token-here
```

### Generate Secure Token
```bash
# Linux/Mac
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"

# PowerShell
-join ((48..57) + (97..102) | Get-Random -Count 64 | % {[char]$_})
```

## ⏱️ Rate Limiting

### Default Settings
- 60 requests per minute per client IP
- Automatic cleanup of old entries
- Health endpoint exempt

### Custom Configuration
```bash
# In .env
RATE_LIMIT_REQUESTS=100  # Max requests
RATE_LIMIT_WINDOW=60     # Time window in seconds
```

### Response When Limited
```json
{
  "error": "Rate limit exceeded. Please try again later."
}
```
HTTP Status: 429 Too Many Requests

## 🌐 CORS Configuration

### Enable CORS
```bash
# In .env - comma-separated list
CORS_ORIGINS=https://app.example.com,https://web.example.com
```

### Disable CORS (Default)
```bash
# Leave empty or omit
CORS_ORIGINS=
```

## 📊 Monitoring

### Check Server Status
```bash
curl http://localhost:8000/health
```

### View Logs
```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

### Watch for Security Events
```bash
# Look for these in logs:
# - "Unauthorized access attempt"
# - "Rate limit exceeded"
# - "Invalid input"
```

## 🚨 Common Issues

### "Unauthorized" Error
**Cause:** Authentication enabled but no/wrong token provided

**Fix:**
```bash
# Check if auth is enabled
docker-compose exec eve-wiki-mcp env | grep MCP_AUTH_TOKEN

# Provide correct token in Authorization header
```

### "Rate limit exceeded"
**Cause:** Too many requests from same IP

**Fix:**
- Wait for rate limit window to expire
- Increase limits in .env if legitimate traffic
- Check for runaway client scripts

### Connection Refused
**Cause:** Firewall blocking port 8000

**Fix:**
```bash
# Allow port through firewall
sudo ufw allow 8000/tcp

# Or use specific IP range
sudo ufw allow from 192.168.1.0/24 to any port 8000
```

## 📝 Security Checklist

### Before Deploying

- [ ] Review `.env.example` and create `.env`
- [ ] Set `MCP_AUTH_TOKEN` if exposing externally
- [ ] Configure rate limits for your use case
- [ ] Set up firewall rules
- [ ] Configure reverse proxy if using HTTPS
- [ ] Test health endpoint
- [ ] Review logs for errors

### Regular Maintenance

- [ ] Monitor logs weekly
- [ ] Check for dependency updates monthly
- [ ] Rotate auth tokens quarterly
- [ ] Review access patterns
- [ ] Update firewall rules as needed

## 🔗 More Information

- **Full Security Guide:** [SECURITY.md](SECURITY.md)
- **Deployment Guide:** [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- **Main README:** [README.md](README.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)

## 💡 Pro Tips

1. **Use Strong Tokens:** Minimum 32 characters, random hex
2. **Enable Auth for External Access:** Always use authentication if accessible from internet
3. **Use Reverse Proxy:** Nginx/Traefik for HTTPS and additional security
4. **Monitor Logs:** Set up log aggregation for production
5. **Regular Updates:** Keep dependencies updated for security patches
6. **Backup Config:** Keep `.env` backed up securely (not in git!)
7. **Test Changes:** Always test in development before production

---

**Version:** 1.1.0  
**Last Updated:** 2026-02-11
