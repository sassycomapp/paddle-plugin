const { spawn } = require('child_process');
const path = require('path');

// Test configuration from test-mcp-servers.js
const mcpConfig = {
  postgres: {
    command: 'C:\\Users\\salib\\AppData\\Roaming\\npm\\npx.cmd',
    args: ['-y', '@modelcontextprotocol/server-postgres'],
    env: {
      DATABASE_URL: process.env.DATABASE_URL || ''
    }
  }
};

// Test queries
const testQueries = {
  createTestTable: `CREATE TABLE IF NOT EXISTS kilo_test (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    value INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
  )`,
  
  insertData: `INSERT INTO kilo_test (name, value)
    VALUES ('test1', 100), ('test2', 200) RETURNING *`,

  selectData: `SELECT * FROM kilo_test ORDER BY id`,

  updateData: `UPDATE kilo_test SET value = 300 WHERE name = 'test1' RETURNING *`,

  deleteData: `DELETE FROM kilo_test WHERE name = 'test2' RETURNING *`,

  dropTestTable: `DROP TABLE IF EXISTS kilo_test`
};

async function testMcpServer(serverName, config) {
  return new Promise((resolve) => {
    console.log(`\n🧪 Testing ${serverName} MCP server...`);
    
    const child = spawn(config.command, config.args, {
      env: { ...process.env, ...config.env },
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 10000
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('error', (error) => {
      console.log(`❌ ${serverName}: Failed to start - ${error.message}`);
      resolve({ name: serverName, status: 'error', error: error.message });
    });

    child.on('exit', (code) => {
      if (code === 0) {
        console.log(`✅ ${serverName}: Server started successfully`);
        resolve({ name: serverName, status: 'success', child, stdout, stderr });
      } else {
        console.log(`⚠️  ${serverName}: Exited with code ${code}`);
        resolve({ name: serverName, status: 'exit', code, stdout, stderr });
      }
    });

    // Send initialize request after 1 second
    setTimeout(() => {
      const initRequest = {
        jsonrpc: '2.0',
        id: 1,
        method: 'initialize',
        params: {
          protocolVersion: '2024-11-05',
          capabilities: {},
          clientInfo: { name: 'test-client', version: '1.0.0' }
        }
      };
      
      try {
        child.stdin.write(JSON.stringify(initRequest) + '\n');
      } catch (e) {
        // Ignore write errors
      }
    }, 1000);
  });
}

async function sendQuery(child, sql) {
  return new Promise((resolve) => {
    const requestId = Math.floor(Math.random() * 10000);
    const request = {
      jsonrpc: '2.0',
      id: requestId,
      method: 'query',
      params: { sql }
    };

    let responseHandler;
    const timeout = setTimeout(() => {
      child.stdout.off('data', responseHandler);
      resolve({ error: 'Timeout waiting for response' });
    }, 5000);

    responseHandler = (data) => {
      try {
        const response = JSON.parse(data.toString());
        if (response.id === requestId) {
          clearTimeout(timeout);
          child.stdout.off('data', responseHandler);
          resolve(response.result || response.error);
        }
      } catch (e) {
        // Ignore parse errors
      }
    };

    child.stdout.on('data', responseHandler);
    child.stdin.write(JSON.stringify(request) + '\n');
  });
}

async function runTests() {
  console.log('Starting Postgres MCP integration tests...');
  
  // Start Postgres MCP server
  const { child } = await testMcpServer('postgres', mcpConfig.postgres);
  if (!child) {
    console.error('❌ Failed to start Postgres MCP server');
    return false;
  }

  try {
    // Test table creation
    const createResult = await sendQuery(child, testQueries.createTestTable);
    if (createResult.error) throw createResult.error;
    console.log('✅ Table created successfully');

    // Test data insertion
    const insertResult = await sendQuery(child, testQueries.insertData);
    if (insertResult.error) throw insertResult.error;
    console.log('✅ Data inserted:', insertResult.rows);

    // Test data selection
    const selectResult = await sendQuery(child, testQueries.selectData);
    if (selectResult.error) throw selectResult.error;
    console.log('✅ Data selected:', selectResult.rows);

    // Test data update
    const updateResult = await sendQuery(child, testQueries.updateData);
    if (updateResult.error) throw updateResult.error;
    console.log('✅ Data updated:', updateResult.rows);

    // Test data deletion
    const deleteResult = await sendQuery(child, testQueries.deleteData);
    if (deleteResult.error) throw deleteResult.error;
    console.log('✅ Data deleted:', deleteResult.rows);

    // Clean up
    await sendQuery(child, testQueries.dropTestTable);
    console.log('✅ Test table dropped');

    console.log('🎉 All Postgres MCP integration tests passed!');
    return true;
  } catch (error) {
    console.error('❌ Test failed:', error);
    return false;
  } finally {
    child.kill();
  }
}

// Load environment variables
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

runTests().catch(console.error);
