#!/usr/bin/env python3
"""
Simple Search Test for Everything Search MCP Server

This is a simple and robust test that verifies the core functionality:
1. Can the server start and initialize?
2. Can it quickly find files?
3. Does it return expected results?

Author: Kilo Code
Version: 1.0.0
"""

import os
import sys
import time
import json
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def test_server_initialization():
    """Test if the server can be initialized."""
    print("Testing server initialization...")
    
    try:
        from everything_search_mcp_server import EverythingSearchMCPServer
        
        # Create server instance
        config_path = str(Path(__file__).parent.parent / "config" / "everything_search_mcp_config.json")
        server = EverythingSearchMCPServer(config_path)
        
        print("✓ Server initialized successfully")
        return True, server
        
    except Exception as e:
        print(f"✗ Server initialization failed: {e}")
        return False, None

def test_sdk_availability(server):
    """Test if the Everything SDK is available."""
    print("Testing SDK availability...")
    
    try:
        validation_result = server.validate_sdk_installation()
        
        if validation_result['valid']:
            print(f"✓ SDK is available at: {validation_result['sdk_info']['sdk_path']}")
            return True
        else:
            print(f"✗ SDK not available: {validation_result['sdk_info']['error_message']}")
            print("  This is expected if Everything Search is not installed")
            return False
            
    except Exception as e:
        print(f"✗ SDK validation failed: {e}")
        return False

def test_basic_search_functionality(server):
    """Test basic search functionality."""
    print("Testing basic search functionality...")
    
    try:
        # Test a simple search
        start_time = time.time()
        result = server.search_files("test", max_results=10)
        end_time = time.time()
        
        search_time = end_time - start_time
        
        print(f"✓ Search completed in {search_time:.3f} seconds")
        print(f"✓ Found {result['total_count']} results")
        
        # Check if results are properly formatted
        if result['results']:
            first_result = result['results'][0]
            required_fields = ['name', 'path', 'size', 'modified', 'extension', 'is_directory']
            
            for field in required_fields:
                if field not in first_result:
                    print(f"✗ Missing field in result: {field}")
                    return False
            
            print("✓ Results are properly formatted")
        
        return True
        
    except Exception as e:
        print(f"✗ Search functionality test failed: {e}")
        return False

def test_search_performance(server):
    """Test search performance with different queries."""
    print("Testing search performance...")
    
    test_queries = [
        "test",
        "document",
        "file",
        "txt",
        "py"
    ]
    
    performance_results = []
    
    for query in test_queries:
        try:
            start_time = time.time()
            result = server.search_files(query, max_results=50)
            end_time = time.time()
            
            search_time = end_time - start_time
            performance_results.append({
                'query': query,
                'time': search_time,
                'results': result['total_count']
            })
            
            print(f"  Query '{query}': {search_time:.3f}s, {result['total_count']} results")
            
        except Exception as e:
            print(f"  Query '{query}': Failed - {e}")
            performance_results.append({
                'query': query,
                'time': float('inf'),
                'results': 0,
                'error': str(e)
            })
    
    # Calculate average performance
    valid_results = [r for r in performance_results if r['time'] != float('inf')]
    
    if valid_results:
        avg_time = sum(r['time'] for r in valid_results) / len(valid_results)
        max_time = max(r['time'] for r in valid_results)
        min_time = min(r['time'] for r in valid_results)
        
        print(f"\nPerformance Summary:")
        print(f"  Average search time: {avg_time:.3f}s")
        print(f"  Maximum search time: {max_time:.3f}s")
        print(f"  Minimum search time: {min_time:.3f}s")
        
        # Performance criteria
        if avg_time < 1.0:  # Should complete in less than 1 second on average
            print("✓ Performance is good")
            return True
        elif avg_time < 5.0:  # Acceptable but could be better
            print("⚠ Performance is acceptable")
            return True
        else:  # Too slow
            print("✗ Performance is poor")
            return False
    else:
        print("✗ No valid performance results")
        return False

def test_advanced_search_options(server):
    """Test advanced search options."""
    print("Testing advanced search options...")
    
    try:
        # Test case sensitive search
        result = server.search_files_advanced("Test", max_results=10, case_sensitive=True)
        print(f"✓ Case sensitive search: {result['total_count']} results")
        
        # Test regex search
        result = server.search_files_advanced(r".*\.txt", max_results=10, regex=True)
        print(f"✓ Regex search: {result['total_count']} results")
        
        # Test whole word search
        result = server.search_files_advanced("test", max_results=10, whole_word=True)
        print(f"✓ Whole word search: {result['total_count']} results")
        
        return True
        
    except Exception as e:
        print(f"✗ Advanced search options test failed: {e}")
        return False

def test_file_extension_search(server):
    """Test file extension search."""
    print("Testing file extension search...")
    
    try:
        # Test extension search
        result = server.search_by_extension("txt", max_results=10)
        print(f"✓ Extension search (.txt): {result['total_count']} results")
        
        return True
        
    except Exception as e:
        print(f"✗ Extension search test failed: {e}")
        return False

def test_server_info(server):
    """Test server information."""
    print("Testing server information...")
    
    try:
        info = server.get_server_info()
        
        required_fields = ['server_name', 'version', 'description', 'author']
        
        for field in required_fields:
            if field not in info:
                print(f"✗ Missing server info field: {field}")
                return False
        
        print(f"✓ Server: {info['server_name']} v{info['version']}")
        print(f"✓ Description: {info['description']}")
        print(f"✓ Author: {info['author']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Server info test failed: {e}")
        return False

def main():
    """Run the simple test suite."""
    print("Everything Search MCP Server - Simple Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test 1: Server initialization
    success, server = test_server_initialization()
    results.append(("Server Initialization", success))
    
    if not success:
        print("\n❌ Cannot continue - server initialization failed")
        return 1
    
    # Test 2: SDK availability
    success = test_sdk_availability(server)
    results.append(("SDK Availability", success))
    
    # Test 3: Server info
    success = test_server_info(server)
    results.append(("Server Information", success))
    
    # Test 4: Basic search functionality
    success = test_basic_search_functionality(server)
    results.append(("Basic Search", success))
    
    # Test 5: Search performance
    success = test_search_performance(server)
    results.append(("Search Performance", success))
    
    # Test 6: Advanced search options
    success = test_advanced_search_options(server)
    results.append(("Advanced Search", success))
    
    # Test 7: File extension search
    success = test_file_extension_search(server)
    results.append(("Extension Search", success))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Everything Search MCP Server is working correctly.")
        print("\nThe server can quickly find files and is ready for use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed.")
        print("The server may have issues or may not be fully configured.")
        return 1

if __name__ == "__main__":
    sys.exit(main())