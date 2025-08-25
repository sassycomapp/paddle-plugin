# Test MCP Servers Directly

Write-Host "🔍 Testing MCP Servers..." -ForegroundColor Green

# Test filesystem server
Write-Host "`n🧪 Testing filesystem server..." -ForegroundColor Yellow
try {
    $process = Start-Process -FilePath "npx" -ArgumentList "-y", "@modelcontextprotocol/server-filesystem", "." -NoNewWindow -PassThru -Wait -Timeout 5
    if ($process.ExitCode -eq 0) {
        Write-Host "✅ filesystem: OK" -ForegroundColor Green
    } else {
        Write-Host "⚠️  filesystem: Exit code $($process.ExitCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ filesystem: Error - $($_.Exception.Message)" -ForegroundColor Red
}

# Test fetch server
Write-Host "`n🧪 Testing fetch server..." -ForegroundColor Yellow
try {
    $process = Start-Process -FilePath "npx" -ArgumentList "-y", "@modelcontextprotocol/server-fetch" -NoNewWindow -PassThru -Wait -Timeout 5
    if ($process.ExitCode -eq 0) {
        Write-Host "✅ fetch: OK" -ForegroundColor Green
    } else {
        Write-Host "⚠️  fetch: Exit code $($process.ExitCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ fetch: Error - $($_.Exception.Message)" -ForegroundColor Red
}

# Test github server (requires token)
Write-Host "`n🧪 Testing github server..." -ForegroundColor Yellow
if ($env:GITHUB_PERSONAL_ACCESS_TOKEN) {
    try {
        $process = Start-Process -FilePath "npx" -ArgumentList "-y", "@modelcontextprotocol/server-github" -NoNewWindow -PassThru -Wait -Timeout 5
        if ($process.ExitCode -eq 0) {
            Write-Host "✅ github: OK" -ForegroundColor Green
        } else {
            Write-Host "⚠️  github: Exit code $($process.ExitCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ github: Error - $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️  github: Skipped (GITHUB_PERSONAL_ACCESS_TOKEN not set)" -ForegroundColor Yellow
}

# Test postgres server (requires DATABASE_URL)
Write-Host "`n🧪 Testing postgres server..." -ForegroundColor Yellow
if ($env:DATABASE_URL) {
    try {
        $process = Start-Process -FilePath "npx" -ArgumentList "-y", "@modelcontextprotocol/server-postgres" -NoNewWindow -PassThru -Wait -Timeout 5
        if ($process.ExitCode -eq 0) {
            Write-Host "✅ postgres: OK" -ForegroundColor Green
        } else {
            Write-Host "⚠️  postgres: Exit code $($process.ExitCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ postgres: Error - $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️  postgres: Skipped (DATABASE_URL not set)" -ForegroundColor Yellow
}

# Test brave-search server (requires BRAVE_API_KEY)
Write-Host "`n🧪 Testing brave-search server..." -ForegroundColor Yellow
if ($env:BRAVE_API_KEY) {
    try {
        $process = Start-Process -FilePath "npx" -ArgumentList "-y", "@modelcontextprotocol/server-brave-search" -NoNewWindow -PassThru -Wait -Timeout 5
        if ($process.ExitCode -eq 0) {
            Write-Host "✅ brave-search: OK" -ForegroundColor Green
        } else {
            Write-Host "⚠️  brave-search: Exit code $($process.ExitCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ brave-search: Error - $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️  brave-search: Skipped (BRAVE_API_KEY not set)" -ForegroundColor Yellow
}

# Environment variables check
Write-Host "`n🔐 Environment Variables Status:" -ForegroundColor Cyan
Write-Host "================================"

$envVars = @(
    @{Name="GITHUB_PERSONAL_ACCESS_TOKEN"; Description="GitHub MCP server"},
    @{Name="DATABASE_URL"; Description="PostgreSQL MCP server"},
    @{Name="BRAVE_API_KEY"; Description="Brave Search MCP server"}
)

foreach ($var in $envVars) {
    $value = [Environment]::GetEnvironmentVariable($var.Name)
    if ($value) {
        Write-Host "✅ $($var.Name): Set ($($var.Description))" -ForegroundColor Green
    } else {
        Write-Host "❌ $($var.Name): Not set ($($var.Description))" -ForegroundColor Red
    }
}

Write-Host "`n📋 MCP Server Test Complete!" -ForegroundColor Green
