#!/usr/bin/env node

/**
 * Test script for MCP Compliance Server
 * This script tests the basic functionality of the compliance server
 */

const { spawn } = require('child_process');
const path = require('path');

async function testServer() {
    console.log('🧪 Testing MCP Compliance Server...\n');

    try {
        // Test 1: Check if server can start
        console.log('📋 Test 1: Server startup');
        const serverProcess = spawn('node', ['dist/server.js'], {
            cwd: __dirname,
            stdio: 'pipe'
        });

        let serverOutput = '';
        let serverError = '';

        serverProcess.stdout?.on('data', (data) => {
            serverOutput += data.toString();
        });

        serverProcess.stderr?.on('data', (data) => {
            serverError += data.toString();
        });

        // Wait a bit for server to start
        await new Promise(resolve => setTimeout(resolve, 3000));

        if (serverProcess.exitCode !== null && serverProcess.exitCode !== 0) {
            throw new Error(`Server failed to start: ${serverError}`);
        }

        console.log('✅ Server started successfully');
        console.log(`📝 Output: ${serverOutput.trim()}`);

        // Test 2: Check if dist directory was created
        console.log('\n📋 Test 2: Build output');
        const fs = require('fs');
        const distPath = path.join(__dirname, 'dist');

        if (fs.existsSync(distPath)) {
            const files = fs.readdirSync(distPath);
            console.log('✅ Dist directory created');
            console.log(`📁 Files: ${files.join(', ')}`);
        } else {
            throw new Error('Dist directory not found');
        }

        // Test 3: Check if main files were built
        console.log('\n📋 Test 3: Built files');
        const requiredFiles = ['server.js', 'types.js', 'logger.js'];
        let allFilesExist = true;

        for (const file of requiredFiles) {
            const filePath = path.join(distPath, file);
            if (fs.existsSync(filePath)) {
                console.log(`✅ ${file} exists`);
            } else {
                console.log(`❌ ${file} missing`);
                allFilesExist = false;
            }
        }

        if (!allFilesExist) {
            throw new Error('Some required files are missing');
        }

        console.log('\n🎉 All tests passed!');
        console.log('\n📖 MCP Compliance Server is ready to use.');
        console.log('\n🚀 To start the server:');
        console.log('   node dist/server.js');
        console.log('\n🔧 Available tools:');
        console.log('   - compliance_assessment');
        console.log('   - generate_remediation_proposal');
        console.log('   - execute_remediation');
        console.log('   - get_server_status');
        console.log('   - validate_configuration');
        console.log('   - get_execution_status');
        console.log('   - cancel_execution');

    } catch (error) {
        console.error('❌ Test failed:', error.message);
        process.exit(1);
    }
}

// Handle process termination
process.on('SIGINT', () => {
    console.log('\n🛑 Test interrupted');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Test interrupted');
    process.exit(0);
});

// Run the test
testServer().catch(console.error);