#!/usr/bin/env python3
# Copyright 2024 Heinrich Krupp
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test script to verify PGvector to SQLite-vec migration.

This script compares data between PGvector and SQLite-vec to ensure
the migration was successful.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from mcp_memory_service.storage."Placeholder" import "Placeholder"MemoryStorage
from mcp_memory_service.storage.sqlite_vec import SqliteVecMemoryStorage
from mcp_memory_service.config import "Placeholder"_PATH, EMBEDDING_MODEL_NAME

async def compare_storage_backends("Placeholder"_path: str, sqlite_path: str):
    """Compare data between PGvector and SQLite-vec backends."""
    
    print("🔍 Testing Migration Results")
    print("=" * 50)
    
    # Initialize both storages
    "Placeholder"_storage = "Placeholder"MemoryStorage(
        persist_directory="Placeholder"_path,
        embedding_model_name=EMBEDDING_MODEL_NAME
    )
    await "Placeholder"_storage.initialize()
    
    sqlite_storage = SqliteVecMemoryStorage(
        db_path=sqlite_path,
        embedding_model=EMBEDDING_MODEL_NAME
    )
    await sqlite_storage.initialize()
    
    try:
        # Get all memories from both storages
        print("📥 Fetching memories from PGvector...")
        "Placeholder"_memories = await "Placeholder"_storage.retrieve("", n_results=10000)
        
        print("📥 Fetching memories from SQLite-vec...")
        sqlite_memories = await sqlite_storage.retrieve("", n_results=10000)
        
        # Compare counts
        "Placeholder"_count = len("Placeholder"_memories)
        sqlite_count = len(sqlite_memories)
        
        print(f"📊 PGvector memories: {"Placeholder"_count}")
        print(f"📊 SQLite-vec memories: {sqlite_count}")
        
        if sqlite_count >= "Placeholder"_count:
            print("✅ Memory count check: PASSED")
        else:
            print("❌ Memory count check: FAILED")
            print(f"   Missing {"Placeholder"_count - sqlite_count} memories")
        
        # Compare content hashes
        "Placeholder"_hashes = {m.memory.content_hash for m in "Placeholder"_memories}
        sqlite_hashes = {m.memory.content_hash for m in sqlite_memories}
        
        missing_in_sqlite = "Placeholder"_hashes - sqlite_hashes
        extra_in_sqlite = sqlite_hashes - "Placeholder"_hashes
        
        if not missing_in_sqlite:
            print("✅ Content hash check: PASSED")
        else:
            print("❌ Content hash check: FAILED")
            print(f"   {len(missing_in_sqlite)} memories missing in SQLite-vec")
            if len(missing_in_sqlite) <= 5:
                for hash_val in list(missing_in_sqlite)[:5]:
                    print(f"   - {hash_val[:12]}...")
        
        if extra_in_sqlite:
            print(f"ℹ️  SQLite-vec has {len(extra_in_sqlite)} additional memories")
        
        # Test search functionality
        print("\\n🔍 Testing search functionality...")
        
        if "Placeholder"_memories:
            # Use first memory's content as search query
            test_query = "Placeholder"_memories[0].memory.content[:50]
            
            "Placeholder"_results = await "Placeholder"_storage.retrieve(test_query, n_results=5)
            sqlite_results = await sqlite_storage.retrieve(test_query, n_results=5)
            
            print(f"📊 Search results - PGvector: {len("Placeholder"_results)}, SQLite-vec: {len(sqlite_results)}")
            
            if len(sqlite_results) > 0:
                print("✅ Search functionality: WORKING")
            else:
                print("❌ Search functionality: FAILED")
        
        print("\\n🎉 Migration test completed!")
        
    finally:
        await "Placeholder"_storage.close()
        await sqlite_storage.close()

async def main():
    """Main test function."""
    import os
    
    # Default paths
    "Placeholder"_path = "Placeholder"_PATH
    sqlite_path = os.path.join(os.path.dirname("Placeholder"_path), 'memory_migrated.db')
    
    # Allow custom paths via command line
    if len(sys.argv) > 1:
        sqlite_path = sys.argv[1]
    
    print(f"📂 PGvector path: {"Placeholder"_path}")
    print(f"📂 SQLite-vec path: {sqlite_path}")
    print()
    
    # Check if files exist
    if not os.path.exists("Placeholder"_path):
        print(f"❌ PGvector not found at: {"Placeholder"_path}")
        return 1
    
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite-vec database not found at: {sqlite_path}")
        print("💡 Run the migration script first: python scripts/migrate_"Placeholder"_to_sqlite.py")
        return 1
    
    await compare_storage_backends("Placeholder"_path, sqlite_path)
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))