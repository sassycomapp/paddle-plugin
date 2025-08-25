const { use_mcp_tool } = require('../../agent_tools');

async function testPostgresIntegration() {
  console.log('Testing Postgres MCP integration...');
  
  try {
    // Test simple query
    const testQuery = await use_mcp_tool('postgres', 'query', {
      sql: 'SELECT 1 AS test_value'
    });
    console.log('✅ Simple query test passed:', testQuery);

    // Test table operations
    const createResult = await use_mcp_tool('postgres', 'query', {
      sql: `CREATE TABLE IF NOT EXISTS kilo_test (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        created_at TIMESTAMP DEFAULT NOW()
      )`
    });
    console.log('✅ Table creation test passed');

    const insertResult = await use_mcp_tool('postgres', 'query', {
      sql: `INSERT INTO kilo_test (name) VALUES ('test1'), ('test2') RETURNING *`
    });
    console.log('✅ Data insertion test passed:', insertResult);

    const selectResult = await use_mcp_tool('postgres', 'query', {
      sql: 'SELECT * FROM kilo_test ORDER BY id'
    });
    console.log('✅ Data selection test passed:', selectResult);

    const dropResult = await use_mcp_tool('postgres', 'query', {
      sql: 'DROP TABLE IF EXISTS kilo_test'
    });
    console.log('✅ Cleanup test passed');

    console.log('🎉 All Postgres MCP integration tests passed successfully!');
    return true;
  } catch (error) {
    console.error('❌ Test failed:', error);
    return false;
  }
}

testPostgresIntegration().catch(console.error);
