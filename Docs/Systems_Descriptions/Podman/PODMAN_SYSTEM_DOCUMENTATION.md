# Podman System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Configuration Files](#configuration-files)
4. [Storage Configuration](#storage-configuration)
5. [Network Configuration](#network-configuration)
6. [Registry Management](#registry-management)
7. [Security Configuration](#security-configuration)
8. [Performance Optimization](#performance-optimization)
9. [Backup and Recovery](#backup-and-recovery)
10. [Monitoring and Logging](#monitoring-and-logging)
11. [Troubleshooting](#troubleshooting)
12. [Best Practices](#best-practices)
13. [Integration Guidelines](#integration-guidelines)

## System Overview

This document provides comprehensive documentation for the Podman containerization system deployed in our environment. Podman (Pod Manager) is a daemonless container engine for developing, managing, and running OCI Containers on your Linux System.

### Key Features
- **Daemonless Architecture**: No central daemon required
- **Rootless Containers**: Supports running containers as a regular user
- **Pod Support**: Native pod management for multi-container applications
- **Docker Compatibility**: Docker-compatible CLI and API
- **Systemd Integration**: Native systemd integration for container lifecycle management

### System Information
- **Podman Version**: 5.5.2
- **Runtime**: crun (OCI runtime)
- **Storage Driver**: VFS (Virtual File System)
- **Network Backend**: netavark
- **CNI Plugin**: aardvark-dns
- **Operating System**: Windows 11 (WSL2 backend)

## Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    User Applications                         │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Podman CLI                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   podman run    │  │   podman build  │  │ podman pull │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 Container Runtime Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │      crun       │  │      conmon     │  │   netavark  │ │
│  │  (OCI Runtime)  │  │  (Container    │  │ (Network    │ │
│  │                 │  │  Monitor)      │  │  Manager)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 System Layer                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   WSL2 Kernel   │  │   File System   │  │   Network   │ │
│  │                 │  │     (VFS)       │  │   Stack     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Container Lifecycle
1. **Image Pull**: Download container images from registries
2. **Container Creation**: Create container from image with specified configuration
3. **Container Start**: Initialize and start the container
4. **Container Run**: Execute the container's main process
5. **Container Stop**: Gracefully stop the container
6. **Container Cleanup**: Remove stopped containers and associated resources

## Configuration Files

### Primary Configuration Structure
```
C:\Users\salib\.config\podman\
├── daemon.json                    # Main daemon configuration
└── containers\
    └── registries.conf            # Registry configuration
```

### daemon.json Configuration

```json
{
  "events": true,
  "log_level": "info",
  "log_size_max": 10000000,
  "storage": {
    "driver": "vfs",
    "graphroot": "C:\\Users\\salib\\.local\\share\\containers\\storage",
    "runroot": "C:\\Users\\salib\\.local\\share\\containers\\run",
    "options": {
      "size": "50G",
      "vfs": {
        "ignore_chown_errors": false,
        "mount_program": ""
      }
    }
  },
  "network": {
    "dns_enabled": true,
    "slirp4netns": {
      "enable_ipv6": true,
      "mtu": 1500,
      "netns": "",
      "cidr": "10.88.0.0/16",
      "enable_host_loopback": false,
      "outbound_addr": "",
      "outbound_addr6": "",
      "port_handler": "slirp4netns",
      "allow_host_loopback": false
    },
    "cni_plugin_dir": "C:\\Program Files\\Podman\\cni-plugins",
    "cni_config_dir": "C:\\Program Files\\Podman\\cni-conf.d",
    "default_network": "podman",
    "network_backend": "cni"
  },
  "containers": {
    "sigproxy": true,
    "interfaces": [],
    "hosts": ["localhost"],
    "keyring_path": "C:\\Users\\salib\\.local\\share\\containers\\keyring",
    "policy": {
      "default": [
        {
          "type": "insecureAcceptAnything"
        }
      ],
      "transports": {
        "docker-daemon": {
          "": [{"type": "insecureAcceptAnything"}]
        }
      }
    }
  },
  "engine": {
    "cgroup_manager": "cgroupfs",
    "service_timeout": 5,
    "events_logger": "file",
    "active_service_timeout": 1800,
    "conmon": "C:\\Program Files\\Podman\\conmon.exe",
    "runtime": "crun",
    "runtime_supports_json": true,
    "runtime_supports_noclear": true,
    "runtime_supports_kvm": true,
    "machine_enabled": true,
    "machine_ssh_check_host_ip": true,
    "machine_no_interactive": false,
    "podmansh": false,
    "time_format": "RFC3339Nano",
    "image_default_transport": "docker://",
    "image_parallel_copies": 0,
    "image_volume_mode": "bind",
    "insecure_registry": [],
    "registries": [
      "docker.io",
      "registry.access.redhat.com",
      "registry.redhat.io",
      "quay.io"
    ],
    "seccomp_profile": "C:\\Program Files\\Podman\\seccomp.json",
    "signature": {
      "default": [
        {
          "type": "insecureAcceptAnything"
        }
      ],
      "new_signatures": []
    }
  }
}
```

### Configuration Parameters

#### Logging Configuration
- **events**: Enable event logging
- **log_level**: Set logging level (debug, info, warn, error, fatal)
- **log_size_max**: Maximum log size in bytes (10MB default)

#### Storage Configuration
- **driver**: Storage driver (vfs for Windows compatibility)
- **graphroot**: Directory for container images and metadata
- **runroot**: Directory for runtime data
- **size**: Storage size limit (50GB)
- **vfs.ignore_chown_errors**: Ignore file ownership errors

#### Network Configuration
- **dns_enabled**: Enable DNS resolution
- **slirp4netns**: Network configuration for rootless containers
  - **enable_ipv6**: Enable IPv6 support
  - **mtu**: Maximum Transmission Unit (1500 bytes)
  - **cidr**: Container IP address range (10.88.0.0/16)
- **cni_plugin_dir**: CNI plugins directory
- **cni_config_dir**: CNI configuration directory
- **network_backend**: Network backend (cni)

#### Container Configuration
- **sigproxy**: Enable signal proxying
- **hosts**: Hostname resolution configuration
- **keyring_path**: Path for container keyring
- **policy**: Image signature policy

#### Engine Configuration
- **cgroup_manager**: Cgroup manager (cgroupfs)
- **service_timeout**: Service timeout in seconds
- **events_logger**: Event logger type (file)
- **conmon**: Container monitor path
- **runtime**: Container runtime (crun)
- **registries**: Default image registries
- **seccomp_profile**: Seccomp security profile

## Storage Configuration

### Storage Architecture
```
C:\Users\salib\.local\share\containers\
├── storage\                    # Graph root (images, containers, volumes)
│   ├── images\                 # Container images
│   ├── containers\             # Container metadata
│   ├── volumes\                # Named volumes
│   └── overlay2\               # OverlayFS layers (if using overlay)
└── run\                        # Runtime data
    └── containers\             # Temporary runtime files
```

### Storage Management
- **Graph Root**: `C:\Users\salib\.local\share\containers\storage`
- **Run Root**: `C:\Users\salib\.local\share\containers\run`
- **Storage Driver**: VFS (Virtual File System)
- **Storage Limit**: 50GB

### Volume Management
```bash
# Create a named volume
podman volume create my_volume

# List volumes
podman volume ls

# Inspect volume
podman volume inspect my_volume

# Remove volume
podman volume rm my_volume
```

### Storage Optimization
1. **Regular Cleanup**: Remove unused images and containers
2. **Volume Management**: Clean up unused volumes
3. **Image Pruning**: Remove dangling images
4. **Storage Monitoring**: Monitor storage usage

## Network Configuration

### Network Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Host Machine                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   WSL2 Network  │  │   Podman        │  │   Container │ │
│  │   Bridge        │  │   Network       │  │   Network   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Network Types
1. **Bridge Network**: Default network type for containers
2. **Host Network**: Direct access to host network
3. **Overlay Network**: Multi-host container networking
4. **Macvlan Network**: Container MAC address assignment
5. **IPvlan Network**: Container IP address assignment

### Network Configuration
- **Default Network**: `podman`
- **Network Backend**: CNI (Container Network Interface)
- **DNS Enabled**: Yes
- **IPv6 Support**: Enabled
- **MTU**: 1500 bytes
- **CIDR**: 10.88.0.0/16

### Network Management
```bash
# List networks
podman network ls

# Inspect network
podman network inspect podman

# Create custom network
podman network create --driver bridge my_network

# Connect container to network
podman run --network my_network nginx
```

### Port Mapping
```bash
# Publish port from container to host
podman run -p 8080:80 nginx

# Publish all ports
podman run -P nginx

# Publish with specific protocol
podman run -p 8080:80/tcp nginx
```

## Registry Management

### Registry Configuration
```ini
# C:\Users\salib\.config\podman\containers\registries.conf
unqualified-search-registries = ["docker.io", "registry.access.redhat.com", "registry.redhat.io", "quay.io"]

# insecure-registries = ["localhost:5000", "127.0.0.1:5000"]
# blocked-registries = ["example.com:5000"]
```

### Registry Types
1. **Public Registries**: Docker Hub, Quay.io, Red Hat Registry
2. **Private Registries**: Self-hosted registries
3. **Mirror Registries**: Registry mirrors for caching

### Registry Management Commands
```bash
# Pull image from registry
podman pull nginx:latest

# Push image to registry
podman push my-image:latest

# Search for images
podman search nginx

# List images
podman images

# Remove image
podman rmi nginx:latest
```

### Registry Authentication
```bash
# Login to registry
podman login docker.io

# Logout from registry
podman logout docker.io

# Show registry credentials
podman login --get-login docker.io
```

## Security Configuration

### Security Features
1. **Seccomp Profiles**: Restrict system calls
2. **AppArmor**: Mandatory access control
3. **SELinux**: Security-enhanced Linux
4. **Capabilities**: Fine-grained privilege control
5. **Rootless Containers**: Run containers as non-root

### Security Configuration
```json
{
  "seccomp_profile": "C:\\Program Files\\Podman\\seccomp.json",
  "signature": {
    "default": [
      {
        "type": "insecureAcceptAnything"
      }
    ],
    "new_signatures": []
  }
}
```

### Security Best Practices
1. **Run as Non-Root**: Use rootless containers when possible
2. **Minimal Images**: Use minimal base images
3. **Read-Only Filesystems**: Mount containers as read-only when possible
4. **Resource Limits**: Set CPU and memory limits
5. **Network Isolation**: Use custom networks for isolation

### Security Commands
```bash
# Run container as non-root
podman run -u 1000 nginx

# Set resource limits
podman run --memory=512m --cpus=1 nginx

# Read-only filesystem
podman run --read-only nginx

# Drop capabilities
podman run --cap-drop=ALL nginx
```

## Performance Optimization

### Performance Tuning
1. **Storage Optimization**: Use appropriate storage drivers
2. **Network Optimization**: Configure network settings
3. **Resource Management**: Set proper resource limits
4. **Caching**: Use image and build caching
5. **Parallel Processing**: Enable parallel operations

### Performance Configuration
```json
{
  "image_parallel_copies": 0,
  "service_timeout": 5,
  "active_service_timeout": 1800
}
```

### Performance Monitoring
```bash
# Monitor container performance
podman stats

# Monitor system resources
htop

# Monitor disk usage
df -h
```

## Backup and Recovery

### Backup Strategy
1. **Configuration Backup**: Backup configuration files
2. **Image Backup**: Backup container images
3. **Volume Backup**: Backup named volumes
4. **System Backup**: Complete system backup

### Backup Commands
```bash
# Backup configuration
tar -czf podman-config-backup.tar.gz ~/.config/podman/

# Backup images
podman save -o images-backup.tar.gz $(podman images -q)

# Backup volumes
podman run --rm -v my_volume:/data -v $(pwd):/backup alpine tar -czf /backup/volume-backup.tar.gz -C /data .
```

### Recovery Commands
```bash
# Restore configuration
tar -xzf podman-config-backup.tar.gz -C ~/

# Restore images
podman load -i images-backup.tar.gz

# Restore volumes
podman run --rm -v my_volume:/data -v $(pwd):/backup alpine tar -xzf /backup/volume-backup.tar.gz -C /data
```

## Monitoring and Logging

### Logging Configuration
- **Log Level**: info
- **Log Size**: 10MB maximum
- **Log Format**: JSON
- **Log Location**: File-based logging

### Monitoring Commands
```bash
# View container logs
podman logs container_name

# Follow container logs
podman logs -f container_name

# View system information
podman info

# View container statistics
podman stats

# View events
podman events
```

### Log Management
```bash
# Rotate logs
podman logs --since 1h container_name

# Filter logs
podman logs --tail 100 container_name

# Export logs
podman logs container_name > logs.txt
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Podman Machine Issues
```bash
# Check machine status
podman machine list

# Restart machine
podman machine stop
podman machine start

# Reset machine
podman machine rm
podman machine init
```

#### 2. Network Issues
```bash
# Check networks
podman network ls

# Inspect network
podman network inspect podman

# Restart network
podman network restart podman
```

#### 3. Storage Issues
```bash
# Clean up unused resources
podman system prune -a

# Check storage usage
podman system df

# Reset storage
podman system reset
```

#### 4. Permission Issues
```bash
# Check user permissions
id

# Add user to groups (Linux)
sudo usermod -aG podman $USER

# Set proper permissions
chmod -R 755 ~/.config/podman/
```

### Debug Commands
```bash
# Debug container
podman run --rm --entrypoint /bin/sh nginx

# Debug network
podman run --rm --network=host alpine ping google.com

# Debug storage
podman run --rm -v /var/lib/containers:/data alpine ls -la /data
```

## Best Practices

### Container Best Practices
1. **Use Minimal Images**: Use Alpine or other minimal base images
2. **Multi-Stage Builds**: Use multi-stage builds for smaller images
3. **Layer Optimization**: Minimize layers in Dockerfiles
4. **Health Checks**: Implement health checks for containers
5. **Resource Limits**: Set appropriate resource limits

### Security Best Practices
1. **Run as Non-Root**: Use non-root users when possible
2. **Scan Images**: Regularly scan images for vulnerabilities
3. **Use Secrets**: Use secrets management for sensitive data
4. **Network Isolation**: Use custom networks for isolation
5. **Regular Updates**: Keep images and base systems updated

### Performance Best Practices
1. **Use Caching**: Leverage build and runtime caching
2. **Optimize Layers**: Minimize Dockerfile layers
3. **Use .dockerignore**: Exclude unnecessary files
4. **Monitor Resources**: Monitor and optimize resource usage
5. **Use Compose**: Use Podman Compose for multi-container apps

## Integration Guidelines

### Integration with Development Tools
1. **IDE Integration**: Configure IDEs to use Podman
2. **CI/CD Integration**: Integrate Podman with CI/CD pipelines
3. **Monitoring Integration**: Integrate with monitoring systems
4. **Logging Integration**: Integrate with logging systems

### Integration Commands
```bash
# IDE Configuration (VS Code)
# Add to settings.json
{
  "docker.enableExperimental": true,
  "docker.machine": "podman-machine-default"
}

# CI/CD Integration
podman build -t my-app .
podman push my-app:latest
podman run -d --name my-app-container my-app:latest
```

### Environment Variables
```bash
# Set Podman environment variables
export PODMAN_SYSTEMD_UNIT=user@1000.service
export CONTAINER_RUNTIME=podman
export DOCKER_HOST=unix:///run/user/1000/podman/podman.sock
```

## Maintenance

### Regular Maintenance Tasks
1. **Update Podman**: Regularly update Podman to latest version
2. **Clean Up Resources**: Remove unused containers, images, and volumes
3. **Monitor Logs**: Regularly review and rotate logs
4. **Update Images**: Update base images regularly
5. **Security Scans**: Perform regular security scans

### Maintenance Commands
```bash
# Update Podman
podman machine stop
podman machine rm
podman machine init
podman machine start

# Clean up resources
podman system prune -a

# Update images
podman images | grep -v "latest" | awk '{print $1":"$2}' | xargs -I {} podman pull {}

# Security scan
podman scan my-image:latest
```

## Conclusion

This document provides comprehensive documentation for the Podman system deployed in our environment. By following the guidelines and best practices outlined in this document, you can effectively manage, secure, and optimize your containerized applications.

For additional information and support, refer to the official Podman documentation:
- [Podman Documentation](https://podman.io/)
- [Podman GitHub Repository](https://github.com/containers/podman)
- [Podman Desktop](https://podman-desktop.io/)

---

*This documentation was last updated on 2025-08-19*
*Version: 1.0*
*Author: System Administrator*