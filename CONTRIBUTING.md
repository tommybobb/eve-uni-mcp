# Contributing to EVE University Wiki MCP Server

Thank you for considering contributing to this project! This MCP server helps bring current EVE Online information to Claude users, and we welcome improvements.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. Check the [GitHub Issues](https://github.com/YOUR_USERNAME/eve-wiki-mcp/issues) to see if it's already reported
2. If not, create a new issue with:
   - Clear, descriptive title
   - Detailed description of the problem or feature
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Your environment (OS, Docker version, Python version, etc.)
   - Relevant logs or error messages

### Development Setup

#### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Git
- A code editor (VS Code recommended)

#### Local Development

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/eve-wiki-mcp.git
   cd eve-wiki-mcp
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

5. **Run locally for testing:**
   ```bash
   # Run in stdio mode for local testing
   python eve_wiki_mcp_server_docker.py
   ```

6. **Test with Docker:**
   ```bash
   docker-compose up
   ```

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes:**
   - Write clear, readable code
   - Follow existing code style
   - Add comments for complex logic
   - Update documentation if needed

3. **Test your changes:**
   ```bash
   # Test locally
   python eve_wiki_mcp_server_docker.py

   # Test with Docker
   docker-compose up --build

   # Check health endpoint
   curl http://localhost:8000/health
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add: Brief description of your changes"
   ```

   Use conventional commit prefixes:
   - `Add:` - New features
   - `Fix:` - Bug fixes
   - `Update:` - Updates to existing features
   - `Docs:` - Documentation changes
   - `Refactor:` - Code refactoring
   - `Test:` - Adding or updating tests

5. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request:**
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill out the PR template with:
     - Description of changes
     - Related issue numbers
     - Testing performed
     - Screenshots (if UI changes)

### Code Style Guidelines

- **Python:**
  - Follow PEP 8 style guide
  - Use type hints where appropriate
  - Keep functions focused and single-purpose
  - Use descriptive variable names
  - Add docstrings for functions and classes

- **Example:**
  ```python
  async def fetch_wiki_page(title: str) -> dict[str, Any]:
      """
      Fetch a wiki page by title.

      Args:
          title: The exact page title to fetch

      Returns:
          Dictionary containing page content and metadata
      """
      # Implementation
  ```

- **Docker:**
  - Keep Dockerfile layers minimal
  - Use specific image tags, not `latest`
  - Document custom configurations

- **Shell scripts:**
  - Use `#!/bin/bash`
  - Add comments for complex commands
  - Check for errors with `set -e`
  - Quote variables properly

### Areas for Contribution

We welcome contributions in these areas:

#### High Priority

- **Performance optimization** - Reduce memory usage, faster response times
- **Error handling** - Better error messages, retry logic
- **Caching** - Add Redis caching layer for frequent queries
- **Rate limiting** - Protect against excessive API calls
- **Testing** - Unit tests, integration tests

#### Medium Priority

- **Monitoring** - Prometheus metrics, health checks
- **Authentication** - Optional auth for external exposure
- **Multiple wikis** - Support other EVE wikis or game wikis
- **Documentation** - More examples, tutorials, guides

#### Feature Ideas

- Ship comparison tool
- Fitting analysis tools
- Market data integration (if appropriate)
- Skill planning information
- Corporation/alliance info

### Testing Guidelines

While we don't have automated tests yet (contributions welcome!), please manually test:

1. **Basic functionality:**
   - Search works and returns results
   - Page fetching works
   - Summary extraction works
   - Category browsing works
   - Related pages work

2. **Error handling:**
   - Non-existent pages return helpful errors
   - Network timeouts are handled gracefully
   - Invalid input is validated

3. **Docker deployment:**
   - Container builds successfully
   - Health check passes
   - Service restarts properly
   - Logs are informative

4. **Cross-platform:**
   - Test on both amd64 and arm64 if possible
   - Verify on Linux, macOS, Windows (in Docker)

### Documentation

When adding features or making changes:

- Update [README.md](README.md) if user-facing
- Update [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) if deployment-related
- Add comments in code for complex logic
- Update [CHANGELOG.md](CHANGELOG.md)

### Pull Request Review Process

1. **Automated checks** - GitHub Actions will run builds
2. **Code review** - Maintainers will review your code
3. **Testing** - We'll test the changes
4. **Feedback** - We may request changes
5. **Merge** - Once approved, we'll merge your PR

### Community Guidelines

- Be respectful and constructive
- Help others in issues and discussions
- Share knowledge and learn together
- Focus on the project goals
- Have fun and fly safe! o7

## Questions?

- Open an issue for bugs or features
- Start a discussion for questions or ideas
- Check existing issues and PRs first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the EVE University Wiki MCP Server!
