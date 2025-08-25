# Podman Setup Guide for RAG System

This guide provides specific instructions for setting up the RAG system using Podman instead of Docker.

## Prerequisites

- Node.js 16+
- Podman 3.0+ and Podman Compose
- Windows: Podman Desktop or WSL2 with Podman
- macOS: Podman Desktop
- Linux: Podman from package manager

## Installing Podman

### Windows
1. Download [Podman Desktop](https://podman-desktop.io/)
2. Install Podman Desktop (includes Podman and Podman Compose)
3. Initialize Podman machine: `podman machine init`
4. Start Podman machine: `podman machine start`

### macOS
1. Download [Podman Desktop](https://podman-desktop.io/)
2. Install Podman Desktop
3. Initialize Podman machine: `podman machine init`
4. Start Podman machine: `podman machine start`

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install podman podman-compose
```

### Linux (RHEL/CentOS/Fedora)
```bash
sudo dnf install podman podman-compose
```

## Quick Start with Podman

### 1. Install RAG System
```bash
node install-rag-system.js install
```

### 2. Verify Podman Setup
```bash
node install-rag-system.js check
```

### 3. Start PGvector with Podman
```bash
# The system will automatically detect Podman
node setup-PGvector.js start
```

### 4. Manual Podman Commands
If you prefer to use Podman directly:

```bash
# Start PGvector
podman-compose -f docker-compose."Placeholder".yml up -d

# Stop PGvector
podman-compose -f docker-compose."Placeholder".yml down

# View logs
podman-compose -f docker-compose."Placeholder".yml logs -f

# Check status
podman ps
```

## Troubleshooting Podman Issues

### Podman Machine Issues (Windows/macOS)
```bash
# Check machine status
podman machine list

# Restart machine
podman machine stop
podman machine start

# Reset machine (if needed)
podman machine rm
podman machine init
```

### Permission Issues (Linux)
```bash
# Add user to podman group (if needed)
sudo usermod -aG podman $USER

# Or use sudo for podman commands
sudo podman-compose -f docker-compose."Placeholder".yml up -d
```

### Port Conflicts
```bash
# Check if port 8000 is in use
netstat -tulpn | grep 8000

# Stop conflicting services
podman stop PGvector-rag
```

### Network Issues
```bash
# Check podman networks
podman network ls

# Create custom network if needed
podman network create PGvector-network
```

## Podman-Specific Configuration

### Using Podman Socket (Linux)
If you want to use Docker-compatible commands:

```bash
# Enable podman socket
systemctl --user enable podman.socket
systemctl --user start podman.socket

# Set DOCKER_HOST
export DOCKER_HOST=unix:///run/user/$(id -u)/podman/podman.sock
```

### Rootless Podman
For rootless operation:

```bash
# Ensure subuid/subgid are configured
sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 $USER

# Enable lingering
sudo loginctl enable-linger $USER
```

## Verification Commands

```bash
# Check Podman installation
podman --version
podman-compose --version

# Test PGvector
curl http://localhost:8000/api/v1/heartbeat

# Check running containers
podman ps

# View logs
podman logs PGvector-rag
```

## Performance Tips

1. **Resource Allocation**: Increase Podman machine resources on Windows/macOS
2. **Storage**: Use podman volume for persistent data
3. **Networking**: Use podman network for better isolation
4. **Updates**: Regularly update Podman Desktop for latest features

## Common Issues and Solutions

### Issue: "Cannot connect to Podman socket"
**Solution**: Ensure Podman machine is running
```bash
podman machine start
```

### Issue: "Permission denied"
**Solution**: Check file permissions and user groups
```bash
# Linux: Add user to podman group
sudo usermod -aG podman $USER
# Then restart session
```

### Issue: "Port already in use"
**Solution**: Find and stop conflicting process
```bash
# Linux
sudo lsof -i :8000
# Windows
netstat -ano | findstr :8000
```

## Integration with RAG System

The RAG system automatically detects Podman and uses the appropriate commands. No additional configuration is needed.

### Environment Variables
```bash
# Optional: Set container runtime explicitly
export CONTAINER_RUNTIME=podman
```

### Testing Podman Integration
```bash
# Run system check
node test-rag-system.js status

# Verify container runtime
node install-rag-system.js check
