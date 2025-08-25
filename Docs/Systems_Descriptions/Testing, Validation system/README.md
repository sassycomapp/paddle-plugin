# Testing and Validation System

A comprehensive testing and validation system for the Paddle Plugin project, providing automated testing, security scanning, and AI-powered test orchestration.

## 🚀 Features

- **Automated Testing**: Unit, integration, end-to-end, and performance tests
- **Security Scanning**: Static code analysis with Semgrep
- **AI-Powered Orchestration**: KiloCode's Test MCP for intelligent test management
- **Browser Automation**: Playwright MCP for UI and E2E testing
- **Containerized Environment**: Podman-based isolated testing
- **Database Testing**: PostgreSQL integration with test data management
- **Comprehensive Reporting**: JSON, HTML, and Markdown test reports
- **CI/CD Ready**: GitHub Actions integration

## 📋 Prerequisites

- **Node.js** 18 or higher
- **PostgreSQL** 12 or higher
- **Podman** 4.0 or higher
- **Python 3** (for Semgrep)
- **VS Code** with KiloCode extension

## 🏗️ System Architecture

### Core Components

1. **Testing Framework**:
   - **Jest**: For JavaScript/Node.js unit and integration tests
   - **Pytest**: For Python backend and logic tests
   - **Playwright**: For browser-based end-to-end (E2E) and UI tests

2. **Containerization**:
   - **Podman**: Primary container runtime for isolated environments
   - **Podman Compose**: For orchestrating multi-container setups

3. **AI Orchestration**:
   - **KiloCode Test MCP**: AI-powered test orchestrator
   - **Playwright MCP**: Browser automation interface

4. **Database**:
   - **PostgreSQL**: Stores test definitions, results, and historical data

5. **Security**:
   - **Semgrep**: Static analysis for vulnerabilities and code quality

### MCP Servers

| Server | Purpose | Status |
|--------|---------|--------|
| **Testing Validation MCP** | Core test orchestration and management | ✅ Active |
| **Playwright MCP** | Browser automation and UI testing | ✅ Configured |
| **PostgreSQL MCP** | Database operations and test data | ✅ Active |
| **Semgrep MCP** | Security scanning and static analysis | ✅ Active |

## 🛠️ Installation

### Quick Setup (Windows)
```bash
# Navigate to testing-validation-system
cd testing-validation-system

# Run Windows setup
scripts\setup-podman.bat
```

### Manual Setup (Linux/macOS)
```bash
# Navigate to testing-validation-system
cd testing-validation-system

# Make scripts executable
chmod +x scripts/*.sh

# Run installation
./install.sh

# Setup Podman environment
./scripts/setup-podman.sh
```

### MCP Server Configuration
Ensure the following MCP servers are configured in `.vscode/mcp.json`:

```json
{
  "testing-validation": {
    "command": "node",
    "args": [
      "testing-validation-system/src/mcp/test-mcp-server.js"
    ],
    "env": {
      "DATABASE_URL": "postgresql://postgres:2001@localhost:5432/postgres"
    }
  },
  "playwright": {
    "command": "npx",
    "args": [
      "-y",
      "@executeautomation/playwright-mcp-server"
    ],
    "env": {}
  }
}
```

## 🚀 Usage

### Starting the System

#### Automatic Start (Recommended)
Use the system-wide MCP server startup script to start all MCP servers including the Testing Validation System:

```bash
# Start all MCP servers including Testing Validation and Playwright
mcp_servers/start-mcp-servers.bat
```

#### Manual Start
```bash
# Start Testing Validation MCP server
node testing-validation-system/src/mcp/test-mcp-server.js

# Start Playwright MCP server (in separate terminal)
npx -y @executeautomation/playwright-mcp-server

# Start Podman services (optional)
podman-compose -f testing-validation-system/podman-compose.yml up -d
```

### Running Tests

```bash
# Navigate to testing-validation-system
cd testing-validation-system

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
- **Tools**: Jest

### 2. Integration Tests
- **Location**: `src/tests/integration/`
- **Purpose**: Test database operations and API endpoints
- **Command**: `npm run test:integration`
- **Tools**: Jest, PostgreSQL

### 3. End-to-End Tests (E2E)
- **Location**: `tests/e2e/`
- **Purpose**: Test complete user workflows
- **Command**: `npm run test:e2e`
- **Tools**: Playwright MCP

### 4. Security Tests
- **Tool**: Semgrep
- **Purpose**: Static code analysis for security vulnerabilities
- **Command**: `npm run security-scan`
- **Integration**: Semgrep MCP

## 🎭 Playwright MCP Integration

### Overview
The Playwright MCP server (`@executeautomation/playwright-mcp-server`) provides browser automation capabilities for UI and end-to-end testing.

### Configuration
- **Package**: `@executeautomation/playwright-mcp-server`
- **Command**: `npx -y @executeautomation/playwright-mcp-server`
- **Status**: Configured in `.vscode/mcp.json`

### Capabilities
- **Browser Automation**: Control Chrome, Firefox, and Safari
- **UI Testing**: Interact with web pages through clicks, typing, and navigation
- **E2E Testing**: Simulate real user workflows
- **Cross-Browser Testing**: Validate across multiple browsers
- **Headless/Headed Modes**: Run tests with or without visible browser windows
- **Screenshot & Video Capture**: Visual evidence of test execution
- **Network Interception**: Monitor and mock network requests
- **Mobile Emulation**: Test responsive designs on various devices

### Usage Examples
```javascript
// Example Playwright test (conceptual)
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  await page.goto('https://example.com');
  await page.click('#login-button');
  await page.fill('#username', 'testuser');
  await page.fill('#password', 'password');
  await page.click('#submit');
  
  await expect(page.locator('#welcome-message')).toBeVisible();
  
  await browser.close();
})();
```

### Integration with KiloCode
- Access Playwright tools through KiloCode's MCP interface
- Generate Playwright tests using natural language prompts
- Debug test failures interactively
- Combine with other MCP servers for comprehensive testing

### Limitations
- Documentation for the specific MCP server is limited
- Some advanced features may require direct Playwright API usage
- Browser dependencies must be installed separately

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

#### Playwright Issues
```bash
# Install Playwright browsers
npx playwright install

# Check Playwright installation
npx playwright --version
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

## 🤝 Best Practices

### Testing Strategy
1. **Feature-Oriented Testing**: Write tests for features, not just files
2. **BDD with Pytest**: Use `.feature` files for high-level behaviors
3. **Playwright Best Practices**:
   - Use stable selectors (data-testid, role, text)
   - Test multiple browsers and viewports
   - Implement proper waits for dynamic content
   - Use page fixtures for setup/teardown
4. **Test Data Management**: Use fixtures and factories for clean data
5. **Documentation**: Auto-generate test reports and coverage metrics

### Code Quality
1. **Static Analysis**: Run Semgrep scans regularly
2. **Code Coverage**: Maintain high coverage for critical paths
3. **Error Handling**: Test both success and failure scenarios
4. **Performance**: Include performance benchmarks for critical operations

### Security
1. **Regular Scans**: Schedule frequent security scans
2. **Vulnerability Management**: Track and remediate findings
3. **Dependency Checks**: Audit third-party packages
4. **Secrets Detection**: Prevent accidental credential exposure

## 📊 MCP Server Details

### Testing Validation MCP
- **Location**: `testing-validation-system/src/mcp/test-mcp-server.js`
- **Database**: PostgreSQL for storing test data
- **Capabilities**:
  - Create and manage test suites
  - Define test cases with metadata
  - Execute tests in various environments
  - Run security scans
  - Generate comprehensive reports

### Playwright MCP
- **Package**: `@executeautomation/playwright-mcp-server`
- **Purpose**: Browser automation and UI testing
- **Integration**: Configured in `.vscode/mcp.json`
- **Features**:
  - Multi-browser support
  - Cross-platform compatibility
  - Network interception
  - Mobile emulation
  - Visual testing

## 🆘 Support

For support, please:
1. Check the troubleshooting section
2. Review the logs in `reports/`
3. Check Podman container logs: `podman-compose logs -f`
4. Verify MCP server status: `node mcp_servers/manage-mcp-servers.js status`
5. Open an issue on GitHub
6. Contact the development team

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔄 Version History

- **v1.0.0**: Initial release with comprehensive testing framework
- **v1.1.0**: Added Playwright MCP integration
- **v1.2.0**: Enhanced security scanning and reporting
- **v1.3.0**: Improved CI/CD integration and documentation

## 🚀 Future Enhancements

- [ ] Enhanced AI-powered test generation
- [ ] Performance testing integration
- [ ] Visual regression testing
- [ ] Advanced reporting dashboards
- [ ] Multi-environment testing support
- [ ] Automated test maintenance
