# Testing and Validation System

A comprehensive testing and validation system for the Paddle Plugin project, built with Node.js, PostgreSQL, and Podman containers.

## 🚀 Features

- **Automated Testing**: Unit, integration, and end-to-end tests
- **Security Scanning**: Static code analysis with Semgrep
- **Database Testing**: PostgreSQL integration with test data
- **MCP Server Testing**: Model Context Protocol server validation
- **Containerized Environment**: Podman-based container orchestration
- **Comprehensive Reporting**: JSON and HTML test reports
- **CI/CD Ready**: GitHub Actions integration

## 📋 Prerequisites

- **Node.js** 18 or higher
- **PostgreSQL** 12 or higher
- **Podman** 4.0 or higher
- **Python 3** (for Semgrep)

## 🛠️ Installation

### Quick Setup (Windows)
```bash
# Clone and navigate to the directory
cd testing-validation-system

# Run Windows setup
scripts\setup-podman.bat
```

### Manual Setup (Linux/macOS)
```bash
# Clone and navigate to the directory
cd testing-validation-system

# Make scripts executable
chmod +x scripts/*.sh

# Run installation
./install.sh

# Setup Podman environment
./scripts/setup-podman.sh
```

## 🏃‍♂️ Usage

### Running Tests

```bash
# Run all tests
npm test

# Run unit tests only
npm run test:unit

# Run integration tests
npm run test:integration

# Run security scan
npm run security-scan

# Run with Podman
podman-compose up test-runner
```

### Database Operations

```bash
# Initialize database
npm run db:init

# Reset test database
npm run db:reset

# Run migrations
npm run db:migrate
```

### Container Management

```bash
# Start all services
podman-compose up

# Start specific service
podman-compose up postgres

# View logs
podman-compose logs -f

# Stop services
podman-compose down

# Rebuild containers
podman-compose build
```

### Generate Reports

```bash
# Generate test reports
npm run report

# View reports
open reports/test-report.html
```

## 📊 Test Types

### 1. Unit Tests
- **Location**: `src/tests/unit/`
- **Purpose**: Test individual functions and modules
- **Command**: `npm run test:unit`

### 2. Integration Tests
- **Location**: `src/tests/integration/`
- **Purpose**: Test database operations and API endpoints
- **Command**: `npm run test:integration`

### 3. MCP Server Tests
- **Location**: `src/mcp/`
- **Purpose**: Test MCP server functionality
- **Command**: `npm run test:mcp`

### 4. Security Tests
- **Tool**: Semgrep
- **Purpose**: Static code analysis for security vulnerabilities
- **Command**: `npm run security-scan`

## 🗄️ Database Schema

### Test Suites
- **test_suites**: Test suite definitions
- **test_cases**: Individual test cases
- **test_executions**: Test run records
- **test_results**: Detailed test results

### Security Analysis
- **static_analysis_results**: Security scan findings
- **vulnerability_reports**: Vulnerability tracking

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/test_db

# Application
NODE_ENV=test
PORT=3000

# Testing
TEST_TIMEOUT=30000
MAX_CONCURRENT_TESTS=5
```

### Podman Configuration
- **File**: `podman-compose.yml`
- **Services**: PostgreSQL, Test Runner, Security Scanner
- **Volumes**: Persistent data storage

## 📈 Monitoring

### Health Checks
- PostgreSQL: `pg_isready`
- Test Runner: Process health check
- Security Scanner: Semgrep availability

### Metrics
- Test execution time
- Pass/fail rates
- Security vulnerability counts
- Database performance metrics

## 🔄 CI/CD Integration

### GitHub Actions
- **File**: `.github/workflows/test.yml`
- **Triggers**: Push, Pull Request
- **Steps**: Install, Test, Security Scan, Report

### Local CI
```bash
# Run full CI pipeline locally
npm run ci
```

## 🐛 Troubleshooting

### Common Issues

#### Podman Not Found
```bash
# Install Podman
# Windows: Download from podman.io
# macOS: brew install podman
# Linux: sudo apt install podman
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
pg_isready -h localhost -p 5432

# Reset database
npm run db:reset
```

#### Permission Issues
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### Debug Mode
```bash
# Enable debug logging
DEBUG=* npm test

# Verbose Podman logs
podman-compose logs -f --tail=100
```

## 📁 Project Structure

```
testing-validation-system/
├── src/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── fixtures/
│   ├── mcp/
│   │   └── test-mcp-server.js
│   └── utils/
├── sql/
│   ├── init-test-db.sql
│   └── migrations/
├── scripts/
│   ├── setup-podman.sh
│   ├── setup-podman.bat
│   └── generate-report.js
├── reports/
│   ├── test-report.json
│   └── test-report.html
├── podman-compose.yml
├── Dockerfile.test
├── package.json
└── README.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support, please:
1. Check the troubleshooting section
2. Review the logs in `reports/`
3. Open an issue on GitHub
4. Contact the development team
