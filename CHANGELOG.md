# Changelog

All notable changes to the EVE University Wiki MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-02-11

### Security
- **CRITICAL**: Added comprehensive input validation for all user inputs
  - Type checking, length limits, and null byte protection
  - Maximum length constraints: queries (500), titles (500), categories (200)
- **CRITICAL**: Implemented rate limiting to prevent DoS attacks
  - Configurable per-client limits (default: 60 requests/minute)
  - IP-based tracking with automatic cleanup
- **HIGH**: Added optional bearer token authentication
  - Configurable via `MCP_AUTH_TOKEN` environment variable
  - Recommended for external deployments
- **HIGH**: Improved error handling and logging
  - Detailed errors logged server-side only
  - Sanitized error messages returned to clients
  - No stack traces or internal paths exposed
- **MEDIUM**: Added proper URL encoding for all generated URLs
  - Prevents URL injection attacks
  - Uses `urllib.parse.quote()` for safe encoding
- **MEDIUM**: Pinned all dependencies to exact versions
  - Prevents supply chain attacks from compromised updates
  - Ensures reproducible builds
- **MEDIUM**: Added CORS configuration support
  - Restrictive by default
  - Configurable via `CORS_ORIGINS` environment variable
- **LOW**: Enhanced deploy-pi.sh with security warning
  - User confirmation required before running remote scripts
  - Manual installation instructions provided

### Added
- `SECURITY.md` - Comprehensive security documentation
  - Security features overview
  - Configuration guide
  - Deployment best practices
  - Vulnerability reporting process
- Structured logging with Python's logging module
- Health endpoint now returns version information
- Security configuration in `.env.example`
- GitHub Actions CI/CD for automated multi-architecture Docker builds
- Automated publishing to GitHub Container Registry (GHCR)
- Git-based deployment workflow with comprehensive documentation
- Pre-built image support for faster Raspberry Pi deployment
- `docker-compose.ghcr.yml` for using pre-built images
- New Makefile targets: `pull-ghcr`, `deploy-ghcr`, `update-from-git`
- Enhanced `deploy-pi.sh` with `--use-ghcr` flag for pulling pre-built images
- Comprehensive `CONTRIBUTING.md` with development guidelines
- `CHANGELOG.md` for tracking version history
- MIT LICENSE file
- `.gitignore` for proper git repository management

### Changed
- Updated `eve_wiki_mcp_server_docker.py` with security hardening
- Updated `requirements.txt` with pinned versions and comments
- Updated `.env.example` with security configuration options
- Updated `docker-compose.yml` with security environment variables
- Updated `docker-compose.ghcr.yml` with security environment variables
- Enhanced README.md with security section
- Reorganized documentation with new primary `README.md`
- Enhanced deployment documentation with git workflow information
- Updated `DOCKER_DEPLOYMENT.md` with GitHub and GHCR instructions

## [1.0.0] - 2026-02-11

### Added
- Initial release of EVE University Wiki MCP Server
- Python-based MCP server with SSE transport for containerized deployment
- Five wiki tools for Claude integration:
  - `search_eve_wiki` - Search the wiki for articles
  - `get_eve_wiki_page` - Fetch full page content in Markdown
  - `get_eve_wiki_summary` - Get brief page summaries
  - `browse_eve_wiki_category` - Browse pages by category
  - `get_related_pages` - Find pages linking to a specific page
- Dockerfile with multi-architecture support (amd64/arm64)
- Docker Compose configuration with resource limits
- Raspberry Pi optimization with CPU and memory constraints
- One-click deployment script (`deploy-pi.sh`) for Raspberry Pi
- Makefile with management commands
- Health check endpoint for monitoring
- Comprehensive documentation:
  - `README_DOCKER.md` - Docker-specific documentation
  - `DOCKER_DEPLOYMENT.md` - Detailed deployment guide
- Environment-based configuration via `.env` file
- HTML to Markdown conversion for clean output
- Error handling for timeouts and API failures
- Async/await implementation for efficient I/O

### Technical Details
- Python 3.11-slim base image
- Non-root user execution for security
- Dependencies: mcp>=1.0.0, httpx>=0.27.0, html2text>=2024.2.26, uvicorn>=0.30.0
- 30-second timeout for wiki API calls
- SSE transport on port 8000
- Resource limits: 0.5 CPU, 256MB RAM
- Auto-restart policy: unless-stopped
- Health check interval: 30s

### Supported Platforms
- Raspberry Pi 3/4/5 (ARM64)
- Linux AMD64
- Any Docker-compatible host
- Proxmox LXC containers

---

## Version Format

Versions follow Semantic Versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

## Categories

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

---

[Unreleased]: https://github.com/tommybobb/eve-wiki-mcp/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/tommybobb/eve-wiki-mcp/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/tommybobb/eve-wiki-mcp/releases/tag/v1.0.0
