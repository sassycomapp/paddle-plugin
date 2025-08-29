# Environment Variables

## Required Variables
- `GITHUB_PERSONAL_ACCESS_TOKEN`: For GitHub API integration
- `DATABASE_URL`: PostgreSQL connection string (format: `postgresql://user:password@host:port/dbname`)
- `BRAVE_API_KEY`: For Brave Search API access
- `PGvector_HOST`: PGvector server host (default: `localhost`)
- `PGvector_PORT`: PGvector server port (default: `8000`)

## Configuration Guidelines
1. **Create `.env` file** from `.env.example` template
2. **Set variables** according to your environment
3. **Restart VSCode** after changes to apply new configuration

## Reference Files
- [.env.example](.env.example) - Template with all required variables
- [MCP Setup Summary](MCP_SETUP_SUMMARY.md) - Detailed configuration requirements
- [Podman Configuration](IDE Notes/Podman.md) - Container environment setup
- [PostgreSQL Setup](IDE Notes/Postgres DB.md) - Database connection details

## Best Practices
- Never commit actual credentials to version control
- Use different `.env` files for development and production
- Validate environment variables using `verify-installation.js`
- Keep sensitive variables in system-specific `.env` files
