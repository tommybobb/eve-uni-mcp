# EVE University Wiki MCP Server

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![ARM](https://img.shields.io/badge/Raspberry%20Pi-A22846?style=flat&logo=raspberrypi&logoColor=white)](https://www.raspberrypi.org/)
[![MCP](https://img.shields.io/badge/MCP-1.0.0-purple.svg)](https://github.com/modelcontextprotocol)

Dockerized MCP server providing Claude with real-time access to EVE University Wiki. Optimized for Raspberry Pi and home labs with automated multi-architecture builds.

## What This Does

Gives Claude up-to-date EVE Online information from the community-maintained EVE University Wiki. When you ask about ships, mechanics, or guides, Claude can fetch current information instead of relying on outdated training data.

**Available Tools:**
- **search_eve_wiki** - Search for articles about ships, mechanics, guides
- **get_eve_wiki_page** - Fetch full page content in Markdown
- **get_eve_wiki_summary** - Get brief page introduction
- **browse_eve_wiki_category** - Browse pages by category (Ships, Mining, PvP, etc.)
- **get_related_pages** - Find pages linking to a specific page
- **generate_newbro_mining_plan** - Build a conservative mining-only onboarding plan for brand-new Alpha players

## Quick Start

### Raspberry Pi Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/tommybobb/eve-wiki-mcp.git
cd eve-wiki-mcp

# Run one-click deployment
chmod +x deploy-pi.sh
./deploy-pi.sh
```

The script will automatically:
- ✅ Install Docker if needed
- ✅ Build the container locally
- ✅ Start the service
- ✅ Show you the configuration for Claude Desktop

### Using Pre-built Images (Fastest)

```bash
# Clone for configuration files
git clone https://github.com/tommybobb/eve-wiki-mcp.git
cd eve-wiki-mcp

# Copy environment template
cp .env.example .env

# Pull pre-built multi-arch image from GHCR
docker pull ghcr.io/tommybobb/eve-wiki-mcp:latest

# Start with pre-built image
docker-compose -f docker-compose.ghcr.yml up -d

# Check health
curl http://localhost:8000/health
```

### Manual Docker Compose

```bash
git clone https://github.com/tommybobb/eve-wiki-mcp.git
cd eve-wiki-mcp
cp .env.example .env
docker-compose up -d
```

## Claude Desktop Configuration

Add this to your Claude Desktop config file:

**Config file location:**
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Configuration (using mcp-remote):**
```json
{
  "mcpServers": {
    "eve-wiki": {
      "command": "npx",
      "args": ["mcp-remote", "http://YOUR_IP:8000/sse", "--allow-http", "--transport", "sse-only"]
    }
  }
}
```

> **Note:** This requires Node.js installed on your system. The `mcp-remote` package bridges Claude Desktop to the remote SSE server.

Replace `YOUR_IP` with:
- Your Raspberry Pi's IP address (e.g., `192.168.1.100`)
- `localhost` if running on the same machine
- Your server hostname

**Restart Claude Desktop** completely after adding the configuration.

### Recommended System Prompt

To get Claude to **automatically** use the wiki tools when you ask about EVE Online (instead of requiring you to explicitly request it), add this to your Claude Desktop custom instructions under **Settings > Custom Instructions**:

> When I ask about EVE Online — ships, fittings, modules, skills, game mechanics, exploration, PvP, PvE, industry, mining, wormholes, nullsec, sovereignty, fleet operations, or any other in-game topic — always use the EVE University Wiki MCP tools to look up accurate, current information before answering. Search the wiki first, then fetch relevant pages for details. Do not rely solely on training data for EVE-specific information, as game mechanics and ship stats change frequently with patches.

## Configuration

### Environment Variables

The `.env` file controls server behavior. Copy from template:

```bash
cp .env.example .env
```

Available settings:

```bash
MCP_TRANSPORT=sse        # Keep as 'sse' for Docker deployment
MCP_HOST=0.0.0.0         # Listen on all network interfaces
MCP_PORT=8000            # Server port
```

### Resource Limits

Default limits optimized for Raspberry Pi:
- **CPU**: 50% of one core max, 25% reserved
- **Memory**: 256MB max, 128MB reserved

Adjust in [docker-compose.yml](docker-compose.yml) if needed.

## Usage Examples

Once connected, ask Claude:

**Ship Information:**
- "What's the Drake good for?"
- "Compare Caldari and Gallente frigates"
- "Best exploration ship for beginners?"

**Game Mechanics:**
- "How does wormhole spawning work?"
- "Explain the fitting window"
- "What are abyssal deadspaces?"

**Guides:**
- "Mining guide for beginners"
- "PvP basics"
- "How to make ISK as a new player?"

**Mining Copilot (Newbro):**
- "Generate a mining-only Day 1 and Week 1 plan for a brand-new Alpha with 1.5h sessions, 4 sessions/week, and 0 starting ISK."
- "Update my mining plan: I got ganked last session and lost my ship."
- "Refine my mining plan with this question: what should I buy first if I only have 500k ISK?"

Example usage loop:
1. Ask for your initial mining plan with time budget + starting ISK.
2. Play one session and note what happened (losses, ISK earned, blockers).
3. Paste `recent_outcome` and rerun `generate_newbro_mining_plan`.
4. Repeat each session to keep the plan adaptive and conservative.

## Management Commands

### Using Makefile (Recommended)

```bash
make help          # Show all available commands
make up            # Start service
make down          # Stop service
make logs          # View logs
make restart       # Restart service
make health        # Check health status
make stats         # Show resource usage
make rebuild       # Rebuild and restart
make pull-ghcr     # Pull pre-built image from GHCR
make update-from-git  # Update from git and rebuild
```

### Using Docker Compose

```bash
docker-compose up -d           # Start
docker-compose down            # Stop
docker-compose logs -f         # View logs
docker-compose restart         # Restart
docker-compose ps              # Check status
docker stats eve-wiki-mcp      # Monitor resources
```

## Updating

### From Git (Local Build)

```bash
cd eve-wiki-mcp
git pull origin main
make rebuild
```

### Using Pre-built Images

```bash
docker pull ghcr.io/tommybobb/eve-wiki-mcp:latest
docker-compose -f docker-compose.ghcr.yml restart
```

## Continuous Integration

This project uses **GitHub Actions** for automated builds:

- ✅ Multi-architecture Docker images (amd64/arm64)
- ✅ Published to GitHub Container Registry (GHCR)
- ✅ Automatic builds on push to main branch
- ✅ Tagged releases for stable versions

**Pre-built images available at:**
```
ghcr.io/tommybobb/eve-wiki-mcp:latest
```

### Build Status

![Build and Push Docker Images](https://github.com/tommybobb/eve-wiki-mcp/workflows/Build%20and%20Push%20Docker%20Images/badge.svg)

Multi-arch images are automatically built for:
- `linux/amd64` - Intel/AMD systems
- `linux/arm64` - Raspberry Pi 3/4/5, ARM servers

## Resource Usage

**Raspberry Pi 4 (4GB):**
- **Idle**: 2-5% CPU, 80-100MB RAM
- **Active**: 20-30% CPU, 120-150MB RAM
- **Network**: Minimal (only during wiki fetches)

Perfect for 24/7 operation on a Raspberry Pi!

## Home Lab Integration

### Proxmox LXC Container

1. Create Ubuntu 22.04 LXC container
2. Install Docker: `curl -fsSL https://get.docker.com | sh`
3. Clone and deploy: `./deploy-pi.sh`

### With Existing Monitoring

**InfluxDB + Grafana:**
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

**Nginx:**
```nginx
location /eve-mcp/ {
    proxy_pass http://localhost:8000/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
}
```

**Traefik labels:**
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.eve-mcp.rule=Host(`eve-mcp.local`)"
  - "traefik.http.services.eve-mcp.loadbalancer.server.port=8000"
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Check if port is in use
sudo netstat -tlnp | grep 8000

# Try manual run for debugging
docker run -it --rm -p 8000:8000 -e MCP_TRANSPORT=sse eve-wiki-mcp
```

### Can't Connect from Claude

1. **Verify service is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check from your desktop:**
   ```bash
   curl http://PI_IP:8000/health
   ```

3. **Open firewall port:**
   ```bash
   sudo ufw allow 8000/tcp
   ```

4. **Verify Claude config:**
   - URL must be `http://` (not `https://`)
   - Must include `/sse` path
   - IP must be reachable from desktop

### Wiki Timeouts

The wiki can be slow. If you see timeouts:
- Check your internet connection
- Increase timeout in [eve_wiki_mcp_server_docker.py](eve_wiki_mcp_server_docker.py) (change `TIMEOUT = 30.0` to `60.0`)
- Rebuild: `make rebuild`

## Security

This server includes multiple security features for safe deployment:

### Built-in Security Features

- ✅ **Input Validation** - All user inputs validated for type, length, and content
- ✅ **Rate Limiting** - Configurable per-client rate limiting (default: 60 req/min)
- ✅ **Optional Authentication** - Bearer token authentication support
- ✅ **Secure Error Handling** - Sanitized errors, detailed logging server-side only
- ✅ **URL Encoding** - Proper encoding prevents injection attacks
- ✅ **Non-root Container** - Runs as unprivileged user (UID 1000)
- ✅ **Pinned Dependencies** - Exact versions for reproducible, secure builds

### Security Configuration

**Enable Authentication** (recommended for external access):
```bash
# In .env file
MCP_AUTH_TOKEN=your-secure-random-token-here

# Generate a secure token:
openssl rand -hex 32
```

**Configure Rate Limiting**:
```bash
RATE_LIMIT_REQUESTS=60  # requests per window
RATE_LIMIT_WINDOW=60    # seconds
```

**Enable CORS** (for web clients):
```bash
CORS_ORIGINS=https://example.com,https://app.example.com
```

### Deployment Recommendations

- **Local network only** by default (0.0.0.0 binding allows LAN access)
- **Enable authentication** if exposing externally
- **Use reverse proxy** (Nginx/Traefik) for TLS/HTTPS
- **Firewall recommended** to limit access to trusted networks
- **VPN preferred** for external access instead of direct internet exposure

See [SECURITY.md](SECURITY.md) for complete security documentation and best practices

## Project Structure

```
eve-wiki-mcp/
├── eve_wiki_mcp_server_docker.py  # Main MCP server implementation
├── Dockerfile                      # Multi-arch container image
├── docker-compose.yml              # Local build service config
├── docker-compose.ghcr.yml         # Pre-built image service config
├── requirements.txt                # Python dependencies
├── .env.example                    # Configuration template
├── .dockerignore                   # Docker build exclusions
├── Makefile                        # Management commands
├── deploy-pi.sh                    # Raspberry Pi deployment script
├── README.md                       # This file
├── README_DOCKER.md                # Detailed Docker documentation
├── DOCKER_DEPLOYMENT.md            # Comprehensive deployment guide
├── SECURITY.md                     # Security documentation and best practices
├── LICENSE                         # MIT license
├── CONTRIBUTING.md                 # Contribution guidelines
├── CHANGELOG.md                    # Version history
└── .github/
    └── workflows/
        └── docker-build.yml        # CI/CD pipeline
```

## Documentation

- **[README.md](README.md)** - This file, quick start and overview
- **[SECURITY.md](SECURITY.md)** - Security features and best practices
- **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** - Comprehensive deployment guide
- **[README_DOCKER.md](README_DOCKER.md)** - Detailed Docker documentation
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

## Development

### Building Multi-Architecture Images

The GitHub Actions workflow handles this automatically, but you can build locally:

```bash
# Setup buildx (one time)
docker buildx create --name multiarch --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t eve-wiki-mcp:latest \
  .
```

### Testing Locally

```bash
# Run in development mode
docker-compose up

# Watch logs
docker-compose logs -f

# Test health endpoint
curl http://localhost:8000/health

# Test SSE connection
curl -N http://localhost:8000/sse
```

### Python Unit Tests (pytest)

```bash
# Install test runner (if not already installed)
pip install pytest

# Run unit tests for mining copilot tool
python -m pytest -q
```

## Contributing

Improvements welcome! Areas of interest:
- Performance optimization
- Additional wiki features
- Better error handling
- More comprehensive documentation
- Caching layer (Redis)
- Rate limiting
- Metrics/monitoring (Prometheus)

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.


## License

**Server code:** MIT License - see [LICENSE](LICENSE)

**EVE University Wiki content:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

**EVE Online:** © CCP Games - All EVE related materials are property of CCP Games

## Credits

- **EVE University** - Amazing wiki and community resources
- **CCP Games** - EVE Online
- **Anthropic** - MCP protocol and Claude
- **Community** - All contributors and users

## Support

- **Issues:** Report bugs and request features on [GitHub Issues](https://github.com/tommybobb/eve-wiki-mcp/issues)
- **Discussions:** Join conversations on [GitHub Discussions](https://github.com/tommybobb/eve-wiki-mcp/discussions)
- **EVE University:** Visit [wiki.eveuniversity.org](https://wiki.eveuniversity.org) for EVE Online content

---

**Ready to fly?** Clone the repo, run `./deploy-pi.sh`, and ask Claude about EVE! o7

Made with ❤️ for the EVE Online and home lab communities.
