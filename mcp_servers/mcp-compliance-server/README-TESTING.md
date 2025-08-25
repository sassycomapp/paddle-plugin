# KiloCode MCP Compliance Server - Testing Guide

## Overview

This guide provides comprehensive instructions for testing the KiloCode MCP Compliance Server, following the KiloCode philosophy: **Simple, Robust, Secure**. The testing framework ensures that all MCP servers within the KiloCode ecosystem meet essential functionality requirements while maintaining security, performance, and reliability standards.

## Quick Start

### Running Tests

```bash
# Run all tests with default configuration
node scripts/test-executor.js

# Run specific test categories
node scripts/test-executor.js --unit --integration --compliance
node scripts/test-executor.js --performance --concurrency 8

# Generate JSON reports
node scripts/test-executor.js --format json

# Custom output directory
node scripts/test-executor.js --output ./test-results
```

### Test Categories

1. **Unit Tests**: Validate individual components and functions
2. **Integration Tests**: Test interactions between components
3. **Compliance Tests**: Validate against KiloCode standards
4. **Performance Tests**: Validate performance benchmarks

## Testing Philosophy

### Simple, Robust, Secure Approach

- **Simple**: Focus on essential functionality only, avoid excessive "bells and whistles"
- **Robust**: Build resilient systems with proper error handling and retry mechanisms
- **Secure**: Implement security by default with comprehensive validation

### Key Principles

1. **Essential Functionality Only**: Test what matters most
2. **Comprehensive Coverage**: Cover all critical scenarios
3. **Automated Execution**: Minimize manual intervention
4. **Clear Reporting**: Provide actionable insights
5. **Continuous Testing**: Integrate testing into development workflow

## Test Configuration

### Command Line Options

```bash
node scripts/test-executor.js [options]

Options:
  --help, -h              Show this help message
  --unit                  Enable unit tests (default: true)
  --no-unit               Disable unit tests
  --integration           Enable integration tests (default: true)
  --no-integration        Disable integration tests
  --compliance            Enable compliance tests (default: true)
  --no-compliance         Disable compliance tests
  --performance           Enable performance tests (default: true)
  --no-performance        Disable performance tests
  --concurrency <num>     Set test concurrency level (default: 4)
  --format <format>       Set output format: json, html, markdown (default: markdown)
  --output <dir>          Set output directory for reports (default: ./reports)
  --no-reports            Disable report generation
  --verbose               Enable verbose output
  --debug                 Enable debug mode
```

### Environment Variables

```bash
# Test environment
NODE_ENV=test
KILOCODE_ENV=test
KILOCODE_PROJECT_PATH=/test/project

# Performance testing
TEST_CONCURRENCY=4
TEST_DURATION=30
TEST_REQUESTS=100

# Debug mode
DEBUG=true
VERBOSE=true
```

## Test Categories

### 1. Unit Tests

**Purpose**: Validate individual components and functions in isolation.

**Coverage**:
- Validation Engine core functionality
- Rule validation logic
- Auto-fix mechanisms
- Error handling
- Configuration parsing

**Example**:
```bash
# Run unit tests only
node scripts/test-executor.js --unit --no-integration --no-compliance --no-performance

# Run with verbose output
node scripts/test-executor.js --unit --verbose
```

### 2. Integration Tests

**Purpose**: Validate interactions between components and external systems.

**Coverage**:
- Server communication protocols
- MCP protocol adherence
- Cross-server communication
- Configuration management
- Error handling across boundaries

**Example**:
```bash
# Run integration tests only
node scripts/test-executor.js --no-unit --integration --no-compliance --no-performance

# Run with custom concurrency
node scripts/test-executor.js --integration --concurrency 8
```

### 3. Compliance Tests

**Purpose**: Validate compliance with KiloCode standards and requirements.

**Coverage**:
- Security benchmarks
- Performance benchmarks
- Configuration standards
- Naming conventions
- Environment-specific requirements

**Example**:
```bash
# Run compliance tests only
node scripts/test-executor.js --no-unit --no-integration --compliance --no-performance

# Run with HTML reports
node scripts/test-executor.js --compliance --format html
```

### 4. Performance Tests

**Purpose**: Validate performance benchmarks and load handling capabilities.

**Coverage**:
- Response time validation
- Resource usage monitoring
- Throughput testing
- Load testing
- Scalability validation

**Example**:
```bash
# Run performance tests only
node scripts/test-executor.js --no-unit --no-integration --no-compliance --performance

# Run with high concurrency
node scripts/test-executor.js --performance --concurrency 16
```

## Test Results and Reporting

### Report Formats

#### JSON Report
Machine-readable format suitable for automated processing.

```json
{
    "metadata": {
        "generatedAt": "2024-01-01T00:00:00.000Z",
        "generatedBy": "KiloCode MCP Compliance Server",
        "testType": "Comprehensive Test Suite"
    },
    "results": {
        "overallScore": 85,
        "unitTests": { "passed": 10, "failed": 2 },
        "integrationTests": { "passed": 8, "failed": 1 },
        "complianceTests": { "passed": 15, "failed": 3, "averageScore": 82 },
        "performanceTests": { "passed": 5, "failed": 1, "averagePerformanceScore": 78 }
    }
}
```

#### HTML Report
Interactive web-based report with visual charts and detailed breakdowns.

#### Markdown Report
Human-readable report suitable for documentation and review.

### Performance Metrics

#### Key Metrics
- **Requests per Second**: Throughput measurement
- **Response Time**: Average response time in milliseconds
- **Performance Score**: Overall performance rating (0-100)
- **Error Rate**: Percentage of failed requests
- **Resource Usage**: CPU, memory, and disk usage

#### Scoring System
- **90-100**: Excellent performance
- **80-89**: Good performance
- **70-79**: Acceptable performance
- **60-69**: Poor performance
- **0-59**: Critical performance issues

## Continuous Testing

### Automated Testing Pipeline

#### Pre-commit Hooks
```bash
# .git/hooks/pre-commit
#!/bin/bash
node scripts/test-executor.js --unit --integration --no-performance
```

#### GitHub Actions
```yaml
name: Automated Testing
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Tests
        run: node scripts/test-executor.js
      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: reports/
```

### Regression Testing

The testing framework includes automated regression detection:

```bash
# Run regression tests
node scripts/test-executor.js --unit --integration --compliance

# Compare with baseline
node scripts/test-executor.js --debug --format json
```

## Troubleshooting

### Common Issues

#### Test Failures
- **Issue**: Tests failing due to configuration errors
- **Solution**: Validate test configuration and environment setup
- **Command**: `node scripts/test-executor.js --debug`

#### Performance Issues
- **Issue**: Tests running slowly
- **Solution**: Reduce concurrency or optimize test data
- **Command**: `node scripts/test-executor.js --concurrency 2`

#### Compliance Failures
- **Issue**: Compliance tests failing
- **Solution**: Review KiloCode standards and update configurations
- **Command**: `node scripts/test-executor.js --compliance --verbose`

### Debug Mode

```bash
# Enable debug logging
node scripts/test-executor.js --debug

# Run with verbose output
node scripts/test-executor.js --verbose

# Generate debug reports
node scripts/test-executor.js --debug --format json
```

## Best Practices

### Testing Best Practices

1. **Keep Tests Simple**: Focus on essential functionality
2. **Use Mocks Wisely**: Mock external dependencies but test real interactions
3. **Test Edge Cases**: Include error scenarios and boundary conditions
4. **Maintain Test Coverage**: Aim for 80%+ test coverage
5. **Update Tests Regularly**: Keep tests in sync with code changes

### Performance Best Practices

1. **Monitor Resource Usage**: Set up alerts for performance thresholds
2. **Optimize Test Data**: Use realistic but minimal test data
3. **Parallelize Tests**: Use appropriate concurrency levels
4. **Cache Results**: Cache test results when possible
5. **Benchmark Against Baselines**: Compare with historical performance

### Security Best Practices

1. **Never Hardcode Credentials**: Use environment variables
2. **Validate All Inputs**: Test input validation thoroughly
3. **Test Security Scenarios**: Include security vulnerability tests
4. **Review Test Data**: Ensure test data doesn't contain sensitive information
5. **Secure Test Environment**: Keep test environments isolated

## Examples

### Example 1: Daily Testing

```bash
# Run comprehensive tests daily
node scripts/test-executor.js --unit --integration --compliance --performance --format html
```

### Example 2: Pre-commit Testing

```bash
# Run quick tests before committing
node scripts/test-executor.js --unit --integration --no-performance --no-reports
```

### Example 3: Performance Validation

```bash
# Validate performance before deployment
node scripts/test-executor.js --performance --concurrency 8 --format json
```

### Example 4: Compliance Audit

```bash
# Run compliance audit
node scripts/test-executor.js --compliance --verbose --format markdown
```

## Support

For issues and questions:
- **Documentation**: [KiloCode Documentation](https://kilocode.com/docs)
- **Issues**: [GitHub Issues](https://github.com/kilocode/kilocode/issues)
- **Community**: [KiloCode Community](https://community.kilocode.com)

## Version History

- **v1.0.0** - Initial release
  - Basic unit testing framework
  - Integration testing capabilities
  - Compliance validation tests
  - Performance testing with Apache Bench
  - Comprehensive reporting system
  - Continuous testing pipeline

**Built with ❤️ by the KiloCode Team**