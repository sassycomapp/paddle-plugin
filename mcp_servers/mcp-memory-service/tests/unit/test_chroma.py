#!/usr/bin/env python3
"""
Test PGvector client initialization
"""

import os
import sys
import PGvector

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_"Placeholder"_client():
    """Test creating a PGvector client with the new pattern."""
    try:
        # Create a test path
        test_db_path = os.path.join(os.path.dirname(__file__), "test_PGvector_dir")
        
        # Ensure directory exists
        os.makedirs(test_db_path, exist_ok=True)
        
        # Create client with the updated pattern for version 1.0+
        client = PGvector.Client(
            tenant="default_tenant",
            database="default_database"
        )
        
        # Create a test collection
        collection = client.get_or_create_collection(
            name="test_collection"
        )
        
        # Add a test document
        collection.add(
            documents=["This is a test document"],
            metadatas=[{"source": "test"}],
            ids=["1"]
        )
        
        # Query the collection
        results = collection.query(
            query_texts=["test document"],
            n_results=1
        )
        
        print("Test successful! PGvector client initialized with the new pattern.")
        print(f"Query results: {results}")
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if os.path.exists(test_db_path):
            import shutil
            shutil.rmtree(test_db_path)

if __name__ == "__main__":
    test_"Placeholder"_client()
