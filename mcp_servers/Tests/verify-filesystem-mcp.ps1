# MCP Filesystem Server Verification Test
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "MCP Filesystem Server Verification Test" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Write-Host ""

# 1. Check Node.js installation
Write-Host "1. Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js version: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found" -ForegroundColor Red
    exit 1
}

# 2. Check npm/npx installation
Write-Host ""
Write-Host "2. Checking npm/npx installation..." -ForegroundColor Yellow
try {
    $npmVersion = npm --version
    Write-Host "✅ npm version: $npmVersion" -ForegroundColor Green
    
    $npxVersion = npx --version
    Write-Host "✅ npx version: $npxVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ npm/npx not found" -ForegroundColor Red
    exit 1
}

# 3. Test MCP Filesystem Server
Write-Host ""
Write-Host "3. Testing MCP Filesystem Server..." -ForegroundColor Yellow
Write-Host "   Starting server with allowed paths: . and C:\tmp" -ForegroundColor Gray
Write-Host "   Server should display: 'Secure MCP Filesystem Server running on stdio'" -ForegroundColor Gray
Write-Host ""

# Create test directory if it doesn't exist
if (-not (Test-Path "C:\tmp")) {
    New-Item -ItemType Directory -Path "C:\tmp" -Force | Out-Null
    Write-Host "✅ Created C:\tmp directory" -ForegroundColor Green
}

# Test the server startup
try {
    Write-Host "Starting MCP Filesystem Server..." -ForegroundColor Yellow
    $process = Start-Process -FilePath "npx" -ArgumentList "-y", "@modelcontextprotocol/server-filesystem", ".", "C:\tmp" -NoNewWindow -PassThru
    
    Start-Sleep -Seconds 3
    
    if (-not $process.HasExited) {
        Write-Host "✅ MCP Filesystem Server started successfully!" -ForegroundColor Green
        Write-Host "   Process ID: $($process.Id)" -ForegroundColor Gray
        Write-Host "   Allowed directories: . and C:\tmp" -ForegroundColor Gray
        
        # Clean shutdown
        Stop-Process -Id $process.Id -Force
        Write-Host "✅ Server stopped gracefully" -ForegroundColor Green
    } else {
        Write-Host "❌ Server exited unexpectedly" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error testing server: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test completed" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
