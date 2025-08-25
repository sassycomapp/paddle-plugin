# Simple MCP Server Test
Write-Host "Testing MCP Servers..."

# Check if Node.js is available
Write-Host "`nChecking Node.js..."
node --version
npm --version

# Test filesystem server
Write-Host "`nTesting filesystem server..."
npx -y @modelcontextprotocol/server-filesystem . --help 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ filesystem: Available" -ForegroundColor Green
} else {
    Write-Host "❌ filesystem: Not available" -ForegroundColor Red
}

# Test fetch server
Write-Host "`nTesting fetch server..."
npx -y @modelcontextprotocol/server-fetch --help 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ fetch: Available" -ForegroundColor Green
} else {
    Write-Host "❌ fetch: Not available" -ForegroundColor Red
}

# Check environment variables
Write-Host "`nEnvironment Variables:"
Write-Host "====================="
if ($env:GITHUB_PERSONAL_ACCESS_TOKEN) {
    Write-Host "✅ GITHUB_PERSONAL_ACCESS_TOKEN: Set" -ForegroundColor Green
} else {
    Write-Host "❌ GITHUB_PERSONAL_ACCESS_TOKEN: Not set" -ForegroundColor Red
}

if ($env:DATABASE_URL) {
    Write-Host "✅ DATABASE_URL: Set" -ForegroundColor Green
} else {
    Write-Host "❌ DATABASE_URL: Not set" -ForegroundColor Red
}

if ($env:BRAVE_API_KEY) {
    Write-Host "✅ BRAVE_API_KEY: Set" -ForegroundColor Green
} else {
    Write-Host "❌ BRAVE_API_KEY: Not set" -ForegroundColor Red
}

Write-Host "`nTest complete!"
