#!/usr/bin/env node

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

class RAGInstaller {
  constructor() {
    this.isWindows = process.platform === 'win32';
  }

  async install() {
console.log('🚀 Installing RAG System with PostgreSQL and pgvector...\n');

    try {
      // 1. Check Node.js version
      await this.checkNodeVersion();

      // 2. Install dependencies
      await this.installDependencies();

      // 3. Verify PostgreSQL setup
      await this.verifyPostgresSetup();

      // 4. Verify installation
      await this.verifyInstallation();

      console.log('\n✅ RAG System installation completed successfully!');
      console.log('\n📚 Next steps:');
      console.log('   1. Start RAG server: node mcp_servers/rag-mcp-server.js');
      console.log('   2. Test the system: node test-rag-system.js test');
      console.log('   3. Read the guide: cat RAG_SETUP_GUIDE.md');

    } catch (error) {
      console.error('❌ Installation failed:', error.message);
      process.exit(1);
    }
  }

  async checkNodeVersion() {
    console.log('🔍 Checking Node.js version...');
    const version = process.version;
    const majorVersion = parseInt(version.slice(1).split('.')[0]);
    
    if (majorVersion < 16) {
      throw new Error(`Node.js 16+ required. Current version: ${version}`);
    }
    
    console.log(`✅ Node.js ${version} is compatible`);
  }

  async installDependencies() {
    console.log('📦 Installing npm dependencies...');
    
    return new Promise((resolve, reject) => {
      const npm = spawn('npm', ['install'], {
        stdio: 'inherit',
        shell: this.isWindows
      });

      npm.on('close', (code) => {
        if (code === 0) {
          console.log('✅ Dependencies installed successfully');
          resolve();
        } else {
          reject(new Error(`npm install failed with code ${code}`));
        }
      });

      npm.on('error', (error) => {
        reject(error);
      });
    });
  }

  async verifyPostgresSetup() {
    console.log('🗄️  Verifying PostgreSQL setup...');
    
    // Check if DATABASE_URL is set
    if (!process.env.DATABASE_URL) {
      throw new Error('DATABASE_URL environment variable is not set');
    }
    
    console.log('✅ PostgreSQL environment configured');
  }

  async verifyInstallation() {
    console.log('🔍 Verifying installation...');
    
    // Check if required files exist
    const requiredFiles = [
      'mcp_servers/rag-mcp-server.js',
      'test-rag-system.js',
      'RAG_SETUP_GUIDE.md'
    ];

    for (const file of requiredFiles) {
      if (!fs.existsSync(file)) {
        throw new Error(`Required file missing: ${file}`);
      }
    }

    // Check if node_modules exists
    if (!fs.existsSync('node_modules')) {
      throw new Error('node_modules directory not found');
    }

    console.log('✅ All required files and dependencies are present');
  }

  async detectContainerRuntime() {
    console.log('🔍 Detecting container runtime...');
    
    try {
      // Check for podman
      require('child_process').execSync('podman --version', { stdio: 'ignore' });
      console.log('✅ Podman detected');
      return 'podman';
    } catch {
      try {
        // Check for docker
        require('child_process').execSync('docker --version', { stdio: 'ignore' });
        console.log('✅ Docker detected');
        return 'docker';
      } catch {
        throw new Error('Neither Podman nor Docker found. Please install one of them.');
      }
    }
  }
}

// CLI interface
if (require.main === module) {
  const installer = new RAGInstaller();
  const command = process.argv[2] || 'install';

  switch (command) {
    case 'install':
      installer.install().catch(console.error);
      break;
    case 'check':
      installer.detectContainerRuntime().catch(console.error);
      break;
    default:
      console.log('Usage: node install-rag-system.js [install|check]');
  }
}

module.exports = RAGInstaller;
