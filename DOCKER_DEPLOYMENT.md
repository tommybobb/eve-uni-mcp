# EVE University Wiki MCP Server - Docker Deployment Guide

Deploy the EVE University Wiki MCP server as a container on your Raspberry Pi, home lab, or any Docker host.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Raspberry Pi 3/4/5, or any x86_64/ARM64 system
- Network access to your Docker host from Claude Desktop

### 1. Clone the Repository

```bash
# Clone from GitHub
git clone https://github.com/YOUR_USERNAME/eve-wiki-mcp.git
cd eve-wiki-mcp
```

### 2. Deploy the Container

**Option A: Using Pre-built Images (Fastest - Recommended)**

```bash
# Pull pre-built multi-arch image from GHCR
docker pull ghcr.io/YOUR_USERNAME/eve-wiki-mcp:latest

# Copy environment template
cp .env.example .env

# Start with pre-built image
docker-compose -f docker-compose.ghcr.yml up -d

# Check health
curl http://localhost:8000/health
```

**Option B: Build Locally**

```bash
# Copy environment template
cp .env.example .env

# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f

# Check health
curl http://localhost:8000/health
```

Expected output:
```json
{"status":"healthy","service":"eve-university-wiki-mcp"}
```

### 2. Test the SSE Endpoint

```bash
curl http://localhost:8000/sse
```

You should see the SSE stream connect.

### 3. Configure Claude Desktop

Add this to your `claude_desktop_config.json`:

**Location:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "eve-university-wiki": {
      "url": "http://YOUR_PI_IP:8000/sse"
    }
  }
}
```

Replace `YOUR_PI_IP` with:
- Your Raspberry Pi's IP address (e.g., `192.168.1.100`)
- Or `localhost` if running on the same machine
- Or your home lab hostname

### 4. Restart Claude Desktop

Completely quit and restart Claude Desktop to pick up the config.

## 📁 Project Structure

```
eve-wiki-mcp-docker/
├── Dockerfile                    # Multi-arch container image
├── docker-compose.yml            # Service definition
├── requirements.txt              # Python dependencies
├── eve_wiki_mcp_server_docker.py # Server with SSE support
├── .env.example                  # Configuration template
└── DOCKER_DEPLOYMENT.md         # This file
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Available options:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `sse` | Transport mode (sse for Docker) |
| `MCP_HOST` | `0.0.0.0` | Bind address |
| `MCP_PORT` | `8000` | Server port |

### Resource Limits

The default compose file limits resources for Raspberry Pi:

- **CPU**: 50% limit, 25% reserved
- **Memory**: 256MB limit, 128MB reserved

Adjust in `docker-compose.yml` if needed:

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'      # Increase for more powerful hosts
      memory: 512M
```

### Port Mapping

Change the exposed port if 8000 is already in use:

```yaml
ports:
  - "8080:8000"  # Expose on port 8080 instead
```

Then use `http://YOUR_IP:8080/sse` in Claude config.

## 🏗️ Building the Image

### Using Pre-built Images (Recommended)

Pre-built multi-architecture images are automatically built via GitHub Actions and published to GitHub Container Registry (GHCR):

```bash
# Pull the latest image
docker pull ghcr.io/YOUR_USERNAME/eve-wiki-mcp:latest

# Or pull a specific version
docker pull ghcr.io/YOUR_USERNAME/eve-wiki-mcp:v1.0.0
```

**Available image tags:**
- `latest` - Latest build from main branch
- `v*.*.*` - Specific version releases (e.g., `v1.0.0`)
- `main-sha-*` - Specific commit builds

### Build Locally for Your Architecture

```bash
# Build locally
docker-compose build

# Or build directly
docker build -t eve-wiki-mcp .

# Or use the Makefile
make build
```

### Multi-Architecture Build

GitHub Actions automatically builds for both AMD64 and ARM64. For manual multi-arch builds:

```bash
# Setup buildx (one time)
docker buildx create --name multiarch --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t eve-wiki-mcp:latest \
  .

# Or use the Makefile
make multi-arch
```

## 🤖 GitHub Actions CI/CD

This project includes automated CI/CD via GitHub Actions:

**Workflow Triggers:**
- Push to `main` branch - Builds and publishes `latest` tag
- Version tags (`v*.*.*`) - Builds and publishes version-tagged images
- Pull requests - Builds (but doesn't publish) for testing

**Build Process:**
- Multi-architecture build (linux/amd64, linux/arm64)
- QEMU emulation for ARM64 on x86 runners
- Layer caching for faster builds
- Automatic publishing to GHCR

**Expected Build Time:**
- First build: 15-30 minutes
- Subsequent builds: 5-10 minutes (with cache)

**Accessing Images:**
```bash
# Latest from main branch
docker pull ghcr.io/YOUR_USERNAME/eve-wiki-mcp:latest

# Specific version
docker pull ghcr.io/YOUR_USERNAME/eve-wiki-mcp:v1.0.0
```

**Note:** GHCR package must be set to "public" in GitHub settings for unauthenticated pulls.

## 🔧 Management

### Start/Stop Service

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Update the Server

**If using pre-built images from GHCR:**

```bash
# Pull latest image
docker pull ghcr.io/YOUR_USERNAME/eve-wiki-mcp:latest

# Restart with new image
docker-compose -f docker-compose.ghcr.yml restart
```

**If building locally:**

```bash
# Pull latest changes from git
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Or use the Makefile
make update-from-git
```

### Monitor Resources

```bash
# Watch container stats
docker stats eve-wiki-mcp

# Check health
docker inspect eve-wiki-mcp --format='{{.State.Health.Status}}'
```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Check if port is in use
sudo netstat -tlnp | grep 8000

# Try running manually for debugging
docker run -it --rm -p 8000:8000 \
  -e MCP_TRANSPORT=sse \
  eve-wiki-mcp
```

### Can't Connect from Claude Desktop

1. **Check container is running:**
   ```bash
   docker-compose ps
   curl http://localhost:8000/health
   ```

2. **Verify network connectivity:**
   ```bash
   # From your desktop machine
   curl http://YOUR_PI_IP:8000/health
   ```

3. **Check firewall rules:**
   ```bash
   # On Raspberry Pi/host
   sudo ufw status
   sudo ufw allow 8000/tcp
   ```

4. **Verify Claude Desktop config:**
   - URL must be `http://` (not `https://`)
   - Include the `/sse` path
   - IP address must be reachable from your desktop

### Health Check Failing

```bash
# Check if the health endpoint responds
curl http://localhost:8000/health

# If not, check logs
docker-compose logs

# Try without healthcheck
docker-compose up -d --no-healthcheck
```

### Wiki API Timeouts

The EVE University Wiki can be slow. If you see timeout errors:

1. **Increase timeout in code** (edit `eve_wiki_mcp_server_docker.py`):
   ```python
   TIMEOUT = 60.0  # Increase from 30 to 60 seconds
   ```

2. **Rebuild and restart:**
   ```bash
   docker-compose up -d --build
   ```

### Memory Issues on Raspberry Pi

If the container keeps restarting:

```bash
# Check OOM kills
docker inspect eve-wiki-mcp | grep OOMKilled

# Reduce memory limit
# Edit docker-compose.yml:
memory: 128M  # Reduce from 256M
```

## 🌐 Network Configuration

### Expose to Internet (with Reverse Proxy)

**Using Nginx:**

```nginx
server {
    listen 80;
    server_name eve-mcp.yourdomain.com;

    location /sse {
        proxy_pass http://localhost:8000/sse;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://localhost:8000/health;
    }
}
```

**Using Traefik** (popular in home labs):

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.eve-mcp.rule=Host(`eve-mcp.local`)"
  - "traefik.http.services.eve-mcp.loadbalancer.server.port=8000"
```

### Running on Proxmox LXC

If deploying in a Proxmox LXC container:

1. **Create LXC container** (Ubuntu 22.04 or Debian 12)
2. **Install Docker in LXC:**
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```
3. **Deploy as normal:**
   ```bash
   docker-compose up -d
   ```

## 📊 Monitoring

### Grafana Dashboard (if you have Grafana)

Add Prometheus metrics by modifying the server:

```python
from prometheus_client import start_http_server, Counter, Histogram

# Track requests
wiki_requests = Counter('wiki_requests_total', 'Total wiki requests')
wiki_latency = Histogram('wiki_request_duration_seconds', 'Wiki request latency')
```

Then expose metrics:

```yaml
ports:
  - "8000:8000"
  - "9090:9090"  # Prometheus metrics
```

### InfluxDB + Grafana (Your Current Stack)

Since you use InfluxDB and Grafana, you can add logging:

```python
from influxdb_client import InfluxDBClient

# Log to your existing InfluxDB
client = InfluxDBClient(url="http://your-influx:8086", token="your-token")
```

## 🔐 Security Considerations

1. **Don't expose to internet without authentication**
2. **Use HTTPS if exposing externally** (via reverse proxy)
3. **Firewall rules** to limit access to your network
4. **Consider VPN** if accessing from outside your network

### Add Basic Auth (Optional)

Add authentication via Nginx:

```nginx
location /sse {
    auth_basic "MCP Server";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8000/sse;
}
```

## 🚀 Production Deployment

### Auto-Start on Boot

```bash
# Enable Docker service
sudo systemctl enable docker

# Compose will auto-restart unless-stopped
docker-compose up -d
```

### Automatic Updates (Watchtower)

Add Watchtower to auto-update containers:

```yaml
services:
  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 3600 eve-wiki-mcp
```

### Backup Strategy

Nothing to back up! The server is stateless. Just keep:
- `docker-compose.yml`
- `.env` file
- Any customizations

## 📈 Performance

### Expected Resource Usage

On Raspberry Pi 4 (4GB):
- **CPU**: 2-5% idle, 20-30% during wiki fetch
- **Memory**: 80-150MB
- **Network**: Minimal (only when fetching wiki)

### Scaling

Running multiple instances behind a load balancer:

```yaml
services:
  eve-wiki-mcp:
    scale: 3  # Run 3 instances
    ports:
      - "8000-8002:8000"
```

## 🧪 Testing

### Test SSE Connection

```bash
# Test with curl
curl -N http://localhost:8000/sse

# Test with httpie (prettier)
http --stream GET http://localhost:8000/sse
```

### Integration Test

```python
import httpx
import json

async def test_mcp():
    async with httpx.AsyncClient() as client:
        # Health check
        r = await client.get('http://localhost:8000/health')
        assert r.status_code == 200
        
        # SSE stream
        async with client.stream('GET', 'http://localhost:8000/sse') as response:
            async for line in response.aiter_lines():
                if line.startswith('data:'):
                    print(json.loads(line[5:]))
```

## 📚 Additional Resources

- [MCP Documentation](https://github.com/modelcontextprotocol)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Raspberry Pi Docker Guide](https://www.docker.com/blog/happy-pi-day-docker-raspberry-pi/)

## 🤝 Contributing

Improvements welcome! Common additions:
- Caching layer (Redis)
- Rate limiting
- Authentication
- Metrics/monitoring
- Additional wiki sources

## 📄 License

EVE University Wiki content is CC BY-SA 4.0. This server implementation is provided as-is.
