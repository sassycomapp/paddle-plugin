#!/usr/bin/env node

const fs = require('fs').promises;
const path = require('path');
const { Pool } = require('pg');

async function generateReport() {
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL || 'postgresql://postgres:2001@localhost:5432/postgres'
  });

  try {
    // Get test summary
    const summaryQuery = `
      SELECT 
        s.name as suite_name,
        s.type,
        e.execution_name,
        e.status,
        e.started_at,
        e.completed_at,
        COUNT(r.id) as total_tests,
        COUNT(CASE WHEN r.status = 'passed' THEN 1 END) as passed,
        COUNT(CASE WHEN r.status = 'failed' THEN 1 END) as failed,
        COUNT(CASE WHEN r.status = 'skipped' THEN 1 END) as skipped,
        AVG(r.duration_ms) as avg_duration
      FROM test_executions e
      JOIN test_suites s ON e.suite_id = s.id
      LEFT JOIN test_results r ON e.id = r.execution_id
      GROUP BY s.id, s.name, s.type, e.id, e.execution_name, e.status, e.started_at, e.completed_at
      ORDER BY e.started_at DESC
    `;

    const summaryResult = await pool.query(summaryQuery);
    
    // Get security scan results
    const securityQuery = `
      SELECT 
        rule_id,
        severity,
        file_path,
        line_number,
        message,
        created_at
      FROM static_analysis_results
      ORDER BY created_at DESC
      LIMIT 100
    `;

    const securityResult = await pool.query(securityQuery);

    const report = {
      generated_at: new Date().toISOString(),
      summary: summaryResult.rows,
      security_findings: securityResult.rows,
      total_suites: summaryResult.rows.length,
      total_tests: summaryResult.rows.reduce((sum, row) => sum + parseInt(row.total_tests), 0),
      total_passed: summaryResult.rows.reduce((sum, row) => sum + parseInt(row.passed), 0),
      total_failed: summaryResult.rows.reduce((sum, row) => sum + parseInt(row.failed), 0)
    };

    // Write JSON report
    await fs.writeFile(
      path.join(__dirname, '../reports/test-report.json'),
      JSON.stringify(report, null, 2)
    );

    // Generate HTML report
    const htmlReport = generateHTMLReport(report);
    await fs.writeFile(
      path.join(__dirname, '../reports/test-report.html'),
      htmlReport
    );

    console.log('✅ Reports generated successfully!');
    console.log(`📊 JSON Report: reports/test-report.json`);
    console.log(`🌐 HTML Report: reports/test-report.html`);

  } catch (error) {
    console.error('❌ Error generating report:', error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

function generateHTMLReport(report) {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Testing & Validation Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .section {
            padding: 30px;
        }
        .section h2 {
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .status-passed { color: #28a745; }
        .status-failed { color: #dc3545; }
        .status-running { color: #ffc107; }
        .severity-high { color: #dc3545; }
        .severity-medium { color: #ffc107; }
        .severity-low { color: #28a745; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Testing & Validation Report</h1>
            <p>Generated: ${new Date(report.generated_at).toLocaleString()}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">${report.total_suites}</div>
                <div class="stat-label">Test Suites</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${report.total_tests}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${report.total_passed}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${report.total_failed}</div>
                <div class="stat-label">Failed</div>
            </div>
        </div>

        <div class="section">
            <h2>Test Suite Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Suite Name</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Total</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>Skipped</th>
                        <th>Avg Duration (ms)</th>
                    </tr>
                </thead>
                <tbody>
                    ${report.summary.map(row => `
                        <tr>
                            <td>${row.suite_name}</td>
                            <td>${row.type}</td>
                            <td class="status-${row.status}">${row.status}</td>
                            <td>${row.total_tests}</td>
                            <td>${row.passed}</td>
                            <td>${row.failed}</td>
                            <td>${row.skipped || 0}</td>
                            <td>${Math.round(row.avg_duration || 0)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Security Findings</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rule ID</th>
                        <th>Severity</th>
                        <th>File Path</th>
                        <th>Line</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody>
                    ${report.security_findings.map(finding => `
                        <tr>
                            <td>${finding.rule_id}</td>
                            <td class="severity-${finding.severity}">${finding.severity}</td>
                            <td>${finding.file_path}</td>
                            <td>${finding.line_number}</td>
                            <td>${finding.message}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>`;
}

// Create reports directory if it doesn't exist
const reportsDir = path.join(__dirname, '../reports');
fs.mkdir(reportsDir, { recursive: true }).then(() => {
  generateReport();
});
