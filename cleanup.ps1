# Identify processes locking directories
$directories = @(
    "C:\_1mybizz\paddle-plugin\.venv",
    "C:\_1mybizz\paddle-plugin\venv",
    "C:\_1mybizz\paddle-plugin\node_modules",
    "C:\_1mybizz\paddle-plugin\mcp_servers\node_modules"
)

foreach ($dir in $directories) {
    # Find processes locking this directory
    $lockedProcesses = (Get-Process | Where-Object {
        $_.Path -like "$dir*"
    }).Id

    # Terminate any locking processes
    if ($lockedProcesses) {
        Stop-Process -Id $lockedProcesses -Force
        Write-Host "Terminated $($lockedProcesses.Count) processes locking $dir"
    }

    # Remove directory if exists
    if (Test-Path $dir) {
        Remove-Item -Recurse -Force $dir
        if (-not (Test-Path $dir)) {
            Write-Host "Successfully removed $dir"
        } else {
            Write-Error "Failed to remove $dir"
        }
    } else {
        Write-Host "$dir not found"
    }
}
