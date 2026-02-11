# EVE University Wiki MCP Server - Docker Edition

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![ARM](https://img.shields.io/badge/Raspberry%20Pi-A22846?style=flat&logo=raspberrypi&logoColor=white)](https://www.raspberrypi.org/)

Containerized MCP server providing Claude with up-to-date EVE Online information from the EVE University Wiki. Perfect for Raspberry Pi, home labs, or any Docker host.

## 🎯 What This Does

Gives Claude real-time access to EVE Online game information without relying on outdated training data. When you ask about ships, mechanics, or guides, Claude  can fetch current information from the community-maintained EVE University Wiki.

## 🚀 Super Quick Start

### Raspberry Pi / Linux
```bash
chmod +x deploy-pi.sh
./deploy-pi.sh
```

### Any Docker Host
```bash
curl http://localhost:8000/health
```

Then add to Claude Desktop:
```json
{
  "mcpServers": {
    "eve-university-wiki": {
      "url": "http://YOUR_IP:8000/sse"
    }
  }
}
```

## 📦 What's Included

```
eve-wiki-mcp-docker/
├── 🐳 Dockerfile                    # Multi-arch container
├── 🐙 docker-compose.yml            # Service orchestration
├── 🐍 eve_wiki_mcp_server_docker.py # Server with SSE
├── 📝 requirements.txt              # Dependencies
├── ⚙️  .env.example                  # Config template
├── 🎯 Makefile                      # Convenience commands
├── 🥧 deploy-pi.sh                  # One-click Pi deploy
├── 📚 README.md                     # This file
├── 📖 DOCKER_DEPLOYMENT.md         # Detailed guide
└── 🎮 QUICK_REFERENCE.md           # Query examples
```

## 📋 Prerequisites

- **Docker** & **Docker Compose** installed
- **Raspberry Pi 3/4/5** or any AMD64/ARM64 system
- **Network access** from your desktop to the Docker host

## 🏗️ Installation Methods

### Method 1: Raspberry Pi Quick Deploy (Easiest)

Perfect for your home lab setup:

```bash
# Download the project
git clone <repo> eve-wiki-mcp
cd eve-wiki-mcp

# Run the magic script
chmod +x deploy-pi.sh
./deploy-pi.sh
```

The script will:
- ✅ Install Docker if needed
- ✅ Build the container
- ✅ Start the service
- ✅ Show you the config to add to Claude

### Method 2: Manual Docker Compose

```bash
# Setup
cp .env.example .env

# Build and start
docker-compose up -d

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f
```

### Method 3: Using Makefile

```bash
# One command install
make install

# Or step by step
make build
make up
make health
```

## ⚙️ Configuration

### Claude Desktop Setup

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "eve-university-wiki": {
      "url": "http://192.168.1.100:8000/sse"
    }
  }
}
```

Replace `192.168.1.100` with your Docker host's IP.

### Environment Variables

Edit `.env` to customize:

```bash
MCP_TRANSPORT=sse        # Keep as 'sse' for Docker
MCP_HOST=0.0.0.0         # Listen on all interfaces
MCP_PORT=8000            # Default port
```

### Resource Limits

Default limits (good for Raspberry Pi):
- **CPU**: 50% of one core
- **Memory**: 256MB max

Adjust in `docker-compose.yml` if needed.

## 🎮 Usage Examples

Once connected, ask Claude:

**Ship Information:**
- "What's the Drake good for?"
- "Compare Caldari and Gallente frigates"
- "Best exploration ship for newbies?"

**Game Mechanics:**
- "How does wormhole spawning work?"
- "Explain the fitting window"
- "What are abyssal deadspaces?"

**Guides:**
- "Mining guide for beginners"
- "PvP basics"
- "How to make ISK as a new player?"

See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for more examples.

## 🛠️ Management Commands

### Using Make (Recommended)

```bash
make help      # Show all commands
make up        # Start service
make down      # Stop service
make logs      # View logs
make restart   # Restart service
make health    # Check health
make stats     # Resource usage
make rebuild   # Rebuild and restart
```

### Using Docker Compose

```bash
docker-compose up -d       # Start
docker-compose down        # Stop
docker-compose logs -f     # Logs
docker-compose restart     # Restart
docker-compose ps          # Status
docker stats eve-wiki-mcp  # Resources
```

## 🏠 Home Lab Integration

### Proxmox LXC Container

1. Create Ubuntu 22.04 LXC
2. Install Docker: `curl -fsSL https://get.docker.com | sh`
3. Deploy: `./deploy-pi.sh`

### With Existing Monitoring

**Your InfluxDB + Grafana setup:**
- Add container metrics to your existing stack
- Monitor wiki API latency
- Track request counts

**Example Telegraf config:**
```toml
[[inputs.docker]]
  endpoint = "unix:///var/run/docker.sock"
  container_names = ["eve-wiki-mcp"]
```

### Reverse Proxy (Nginx/Traefik)

For secure external access:

```nginx
location /eve-mcp/ {
    proxy_pass http://localhost:8000/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
}
```

## 📊 Resource Usage

**Raspberry Pi 4 (4GB):**
- **Idle**: 2-5% CPU, 80-100MB RAM
- **Active**: 20-30% CPU, 120-150MB RAM
- **Network**: Minimal (only during wiki fetches)

Perfect for 24/7 operation on a Pi!

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Check if port is in use
sudo netstat -tlnp | grep 8000

# Try manual run
docker run -it --rm -p 8000:8000 -e MCP_TRANSPORT=sse eve-wiki-mcp
```

### Can't Connect from Claude

1. **Verify service:** `curl http://localhost:8000/health`
2. **Check from desktop:** `curl http://PI_IP:8000/health`
3. **Firewall:** `sudo ufw allow 8000/tcp`
4. **Config:** Ensure URL has `/sse` path

### Wiki Timeouts

Wiki can be slow. If you see timeouts:
- Check your internet connection
- Increase timeout in code (60s instead of 30s)
- Rebuild: `make rebuild`

## 🔐 Security Notes

- **Local network only** by default (0.0.0.0 binding)
- **No authentication** (add via reverse proxy if exposing)
- **Firewall recommended** to limit access
- **VPN preferred** for external access

## 📈 Performance Tips

1. **Pin to one core** on Pi for stability
2. **Use tmpfs** for temporary files
3. **Add Redis** for caching (optional)
4. **Monitor with Grafana** (you already have this!)

## 🔄 Updates

```bash
# Pull changes
git pull

# Rebuild and restart
make rebuild

# Or manual
docker-compose down
docker-compose build
docker-compose up -d
```

## 📚 Advanced

### Multi-Instance Setup

Run multiple instances behind a load balancer:

```yaml
eve-wiki-mcp:
  scale: 3
  ports:
    - "8000-8002:8000"
```

### Custom Wiki Timeout

Edit `eve_wiki_mcp_server_docker.py`:
```python
TIMEOUT = 60.0  # Increase from 30
```

### Add Caching Layer

Deploy Redis:
```yaml
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

## 🎯 Roadmap

- [ ] Built-in caching (Redis)
- [ ] Rate limiting
- [ ] Metrics endpoint (Prometheus)
- [ ] Authentication support
- [ ] Multiple wiki sources
- [ ] Ship comparison tool

## 📖 Documentation

- [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - Comprehensive deployment guide
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Query examples
- [MCP Docs](https://github.com/modelcontextprotocol) - MCP protocol info

## 🤝 Contributing

Improvements welcome! Areas:
- Performance optimization
- Additional features
- Better error handling
- More documentation

## 📄 License

Server code: MIT  
EVE University Wiki content: CC BY-SA 4.0  
EVE Online: © CCP Games

## 🎮 Made For

Players who want Claude to know about:
- Current ship meta
- Latest game mechanics
- Up-to-date fitting guides
- Recent balance changes
- Community wisdom

Because outdated game info is worse than no info!

## 🙏 Credits

- **EVE University** - Amazing wiki and community
- **CCP Games** - EVE Online
- **Anthropic** - MCP protocol and Claude
- **You** - For building cool stuff in your home lab!

---

**Questions?** Check [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for detailed troubleshooting.

**Ready to fly?** `make install` and ask Claude about EVE! o7
