# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :x:                |

## Security Features

### Built-in Security Measures

This MCP server includes the following security features:

1. **Input Validation**
   - All user inputs are validated for type, length, and content
   - Maximum length limits prevent buffer overflow attacks
   - Null byte injection protection

2. **Rate Limiting**
   - Configurable per-client rate limiting (default: 60 requests/minute)
   - Prevents DoS attacks and API abuse
   - Based on client IP address

3. **Optional Authentication**
   - Bearer token authentication support
   - Disabled by default for local networks
   - Recommended for external exposure

4. **Secure Error Handling**
   - Detailed errors logged server-side only
   - Sanitized error messages returned to clients
   - No stack traces or internal paths exposed

5. **URL Encoding**
   - All URLs properly encoded to prevent injection
   - Safe handling of special characters

6. **Container Security**
   - Runs as non-root user (UID 1000)
   - Minimal base image (python:3.11-slim)
   - Resource limits configured
   - Health checks enabled

7. **Dependency Management**
   - All dependencies pinned to exact versions
   - Regular security audits recommended

## Configuration

### Authentication

To enable authentication, set the `MCP_AUTH_TOKEN` environment variable:

```bash
# In .env file
MCP_AUTH_TOKEN=your-secure-random-token-here
```

Clients must include the token in requests:
```
Authorization: Bearer your-secure-random-token-here
```

### Rate Limiting

Configure rate limits in `.env`:

```bash
RATE_LIMIT_REQUESTS=60  # requests per window
RATE_LIMIT_WINDOW=60    # seconds
```

### CORS

For web-based clients, configure allowed origins:

```bash
CORS_ORIGINS=https://example.com,https://app.example.com
```

## Deployment Security

### Local Network Deployment (Default)

- Server binds to `0.0.0.0:8000` (all interfaces)
- No authentication required by default
- Suitable for trusted local networks only
- **Do not expose directly to the internet**

### External/Public Deployment

If you must expose the server externally:

1. **Enable authentication**:
   ```bash
   MCP_AUTH_TOKEN=$(openssl rand -hex 32)
   ```

2. **Use a reverse proxy** (Nginx, Traefik, Caddy):
   - Terminate TLS/SSL at the proxy
   - Add additional authentication layers
   - Implement IP whitelisting
   - Add request logging

3. **Use a VPN** (recommended):
   - WireGuard, Tailscale, or similar
   - Keep the server on your private network
   - Access via VPN tunnel

4. **Firewall rules**:
   ```bash
   # Allow only specific IPs
   sudo ufw allow from 192.168.1.0/24 to any port 8000
   ```

## Known Limitations

1. **No TLS/HTTPS Support**
   - The server does not implement TLS directly
   - Use a reverse proxy for HTTPS
   - MCP protocol may not require encryption for local use

2. **In-Memory Rate Limiting**
   - Rate limits reset on server restart
   - Not shared across multiple instances
   - Consider Redis for production deployments

3. **No Request Logging**
   - Basic logging to stdout only
   - Consider adding structured logging for production

4. **No Audit Trail**
   - No persistent record of requests
   - Add logging middleware for compliance needs

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email the maintainer directly (see GitHub profile)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to:
- Confirm the vulnerability
- Develop a fix
- Release a security update
- Credit you in the release notes (if desired)

## Security Best Practices

### For Users

1. **Keep dependencies updated**:
   ```bash
   pip list --outdated
   ```

2. **Review logs regularly**:
   ```bash
   docker-compose logs -f
   ```

3. **Monitor resource usage**:
   ```bash
   docker stats eve-wiki-mcp
   ```

4. **Use strong authentication tokens**:
   ```bash
   # Generate a secure token
   openssl rand -hex 32
   ```

5. **Limit network exposure**:
   - Use firewall rules
   - Deploy behind VPN
   - Use reverse proxy with authentication

### For Developers

1. **Never commit secrets**:
   - `.env` is in `.gitignore`
   - Use environment variables
   - Rotate tokens regularly

2. **Validate all inputs**:
   - Check types and lengths
   - Sanitize before use
   - Use parameterized queries

3. **Handle errors securely**:
   - Log detailed errors server-side
   - Return generic errors to clients
   - Never expose stack traces

4. **Keep dependencies minimal**:
   - Only include necessary packages
   - Pin exact versions
   - Audit regularly

## Security Checklist

Before deploying to production:

- [ ] Authentication enabled (`MCP_AUTH_TOKEN` set)
- [ ] Rate limiting configured appropriately
- [ ] Firewall rules in place
- [ ] Reverse proxy configured (if external)
- [ ] TLS/HTTPS enabled (via proxy)
- [ ] Logs being collected and monitored
- [ ] Resource limits configured
- [ ] Health checks working
- [ ] Backup strategy in place
- [ ] Incident response plan documented

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)

## License

This security policy is part of the EVE University Wiki MCP Server project and is licensed under the MIT License.
