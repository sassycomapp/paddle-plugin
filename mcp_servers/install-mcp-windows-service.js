const { Service } = require('node-windows');

// Create services for each MCP server
const services = [
  {
    name: 'mcp-filesystem',
    script: 'npx',
    args: ['-y', '@modelcontextprotocol/server-filesystem', '.'],
    env: {
      PORT: 8010
    }
  },
  {
    name: 'mcp-github',
    script: 'npx',
    args: ['-y', '@modelcontextprotocol/server-github'],
    env: {
      PORT: 8011,
      GITHUB_PERSONAL_ACCESS_TOKEN: process.env.GITHUB_PERSONAL_ACCESS_TOKEN || ''
    }
  },
  {
    name: 'mcp-postgres',
    script: 'npx',
    args: ['-y', '@modelcontextprotocol/server-postgres'],
    env: {
      PORT: 8012,
      DATABASE_URL: process.env.DATABASE_URL || ''
    }
  },
  {
    name: 'mcp-brave-search',
    script: 'npx',
    args: ['-y', '@modelcontextprotocol/server-brave-search'],
    env: {
      PORT: 8013,
      BRAVE_API_KEY: process.env.BRAVE_API_KEY || ''
    }
  }
];

// Install each service
services.forEach(config => {
  const svc = new Service({
    name: config.name,
    description: `MCP Server - ${config.name}`,
    script: config.script,
    args: config.args,
    env: Object.keys(config.env).map(key => ({
      name: key,
      value: config.env[key]
    }))
  });

  svc.on('install', () => {
    console.log(`${config.name} service installed.`);
    svc.start();
  });

  svc.on('alreadyinstalled', () => {
    console.log(`${config.name} service already installed.`);
  });

  svc.on('start', () => {
    console.log(`${config.name} service started.`);
  });

  svc.install();
});
