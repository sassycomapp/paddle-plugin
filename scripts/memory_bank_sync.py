#!/usr/bin/env python3
"""
Memory Bank Synchronization Script

This script handles synchronization between the cache system and Memory Bank files,
ensuring bidirectional data flow and conflict resolution.

Author: KiloCode
License: Apache 2.0
"""

import asyncio
import logging
import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import hashlib
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemoryBankSync:
    """Handles synchronization between cache system and Memory Bank."""
    
    def __init__(self, config_path: str = "src/orchestration/mcp_servers_config.yaml"):
        self.config_path = config_path
        self.memory_bank_path = Path("./memorybank")
        self.cache_storage_path = Path("./cache_storage")
        self.sync_metadata_path = Path("./sync_metadata.json")
        
        # Sync configuration
        self.sync_config = {
            "enabled": True,
            "sync_interval": 300,  # 5 minutes
            "bidirectional": True,
            "conflict_resolution": "timestamp",
            "max_sync_attempts": 3,
            "backup_before_sync": True,
            "cleanup_old_syncs": True,
            "max_sync_backups": 5
        }
        
        # Sync metadata
        self.sync_metadata = {
            "last_sync": None,
            "sync_count": 0,
            "conflicts_resolved": 0,
            "errors": [],
            "last_error": None
        }
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize directories
        self._initialize_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _initialize_directories(self):
        """Initialize required directories."""
        self.memory_bank_path.mkdir(parents=True, exist_ok=True)
        self.cache_storage_path.mkdir(parents=True, exist_ok=True)
        self.sync_metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup directory
        backup_dir = self.memory_bank_path / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def sync_all(self) -> Dict[str, Any]:
        """Perform complete synchronization between cache and memory bank."""
        logger.info("Starting memory bank synchronization...")
        
        sync_result = {
            "sync_id": f"sync_{int(time.time())}",
            "start_time": datetime.utcnow().isoformat(),
            "status": "completed",
            "operations": {},
            "conflicts": [],
            "errors": [],
            "summary": {}
        }
        
        try:
            # Create backup before sync
            if self.sync_config["backup_before_sync"]:
                backup_result = await self._create_backup()
                sync_result["operations"]["backup"] = backup_result
            
            # Sync from memory bank to cache
            if self.sync_config["bidirectional"]:
                cache_sync_result = await self._sync_memory_to_cache()
                sync_result["operations"]["memory_to_cache"] = cache_sync_result
            
            # Sync from cache to memory bank
            if self.sync_config["bidirectional"]:
                memory_sync_result = await self._sync_cache_to_memory()
                sync_result["operations"]["cache_to_memory"] = memory_sync_result
            
            # Resolve conflicts
            conflicts_result = await self._resolve_conflicts()
            sync_result["operations"]["conflict_resolution"] = conflicts_result
            sync_result["conflicts"] = conflicts_result.get("conflicts", [])
            
            # Update metadata
            self._update_sync_metadata(sync_result)
            
            # Cleanup old syncs
            if self.sync_config["cleanup_old_syncs"]:
                cleanup_result = await self._cleanup_old_syncs()
                sync_result["operations"]["cleanup"] = cleanup_result
            
            # Generate summary
            sync_result["summary"] = self._generate_sync_summary(sync_result)
            
            logger.info("Memory bank synchronization completed successfully")
            
        except Exception as e:
            error_msg = f"Synchronization failed: {str(e)}"
            logger.error(error_msg)
            sync_result["status"] = "failed"
            sync_result["errors"].append(error_msg)
            self.sync_metadata["last_error"] = error_msg
            self.sync_metadata["errors"].append(error_msg)
        
        sync_result["end_time"] = datetime.utcnow().isoformat()
        return sync_result
    
    async def _create_backup(self) -> Dict[str, Any]:
        """Create backup of memory bank before synchronization."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.memory_bank_path / "backups" / f"backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy all memory bank files
            for file_path in self.memory_bank_path.glob("*"):
                if file_path.is_file() and not file_path.name.startswith("backup_"):
                    shutil.copy2(file_path, backup_dir / file_path.name)
            
            # Update sync metadata
            self.sync_metadata["last_backup"] = timestamp
            
            return {
                "success": True,
                "backup_path": str(backup_dir),
                "timestamp": timestamp,
                "files_copied": len(list(backup_dir.glob("*")))
            }
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _sync_memory_to_cache(self) -> Dict[str, Any]:
        """Synchronize data from memory bank to cache system."""
        logger.info("Syncing memory bank to cache...")
        
        result = {
            "success": True,
            "files_processed": 0,
            "items_synced": 0,
            "errors": []
        }
        
        try:
            # Process memory bank files
            memory_files = list(self.memory_bank_path.glob("*.md"))
            
            for file_path in memory_files:
                try:
                    file_sync_result = await self._sync_memory_file_to_cache(file_path)
                    result["files_processed"] += 1
                    result["items_synced"] += file_sync_result.get("items_synced", 0)
                    
                    if not file_sync_result["success"]:
                        result["errors"].append(file_sync_result.get("error", "Unknown error"))
                        result["success"] = False
                    
                except Exception as e:
                    error_msg = f"Error syncing file {file_path}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    result["success"] = False
            
            logger.info(f"Memory to cache sync completed: {result['items_synced']} items synced")
            
        except Exception as e:
            error_msg = f"Memory to cache sync failed: {str(e)}"
            logger.error(error_msg)
            result["success"] = False
            result["errors"].append(error_msg)
        
        return result
    
    async def _sync_memory_file_to_cache(self, file_path: Path) -> Dict[str, Any]:
        """Sync a single memory bank file to cache."""
        try:
            # Read memory bank file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Generate cache key from file name
            cache_key = f"memory_bank_{file_path.stem}"
            
            # Prepare cache data
            cache_data = {
                "content": content,
                "source_file": str(file_path),
                "sync_timestamp": datetime.utcnow().isoformat(),
                "file_metadata": {
                    "size": len(content),
                    "modified": file_path.stat().st_mtime,
                    "hash": hashlib.md5(content.encode()).hexdigest()
                }
            }
            
            # Determine cache layer based on file type
            cache_layer = self._determine_cache_layer(file_path.stem)
            
            # Sync to cache
            sync_result = await self._sync_to_cache_layer(cache_key, cache_data, cache_layer)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "cache_key": cache_key,
                "cache_layer": cache_layer,
                "items_synced": 1,
                "sync_result": sync_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "file_path": str(file_path),
                "error": str(e)
            }
    
    async def _sync_cache_to_memory(self) -> Dict[str, Any]:
        """Synchronize data from cache system to memory bank."""
        logger.info("Syncing cache to memory bank...")
        
        result = {
            "success": True,
            "cache_items_processed": 0,
            "memory_files_updated": 0,
            "errors": []
        }
        
        try:
            # Get cache data from all layers
            cache_layers = ["predictive", "semantic", "vector", "global", "vector_diary"]
            
            for layer in cache_layers:
                try:
                    layer_sync_result = await self._sync_cache_layer_to_memory(layer)
                    result["cache_items_processed"] += layer_sync_result.get("items_processed", 0)
                    result["memory_files_updated"] += layer_sync_result.get("files_updated", 0)
                    
                    if not layer_sync_result["success"]:
                        result["errors"].extend(layer_sync_result.get("errors", []))
                        result["success"] = False
                    
                except Exception as e:
                    error_msg = f"Error syncing cache layer {layer}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    result["success"] = False
            
            logger.info(f"Cache to memory sync completed: {result['memory_files_updated']} files updated")
            
        except Exception as e:
            error_msg = f"Cache to memory sync failed: {str(e)}"
            logger.error(error_msg)
            result["success"] = False
            result["errors"].append(error_msg)
        
        return result
    
    async def _sync_cache_layer_to_memory(self, layer: str) -> Dict[str, Any]:
        """Sync a specific cache layer to memory bank."""
        try:
            # This would connect to the actual cache MCP server
            # For now, we'll simulate the cache data retrieval
            cache_data = await self._get_cache_data_for_layer(layer)
            
            if not cache_data:
                return {
                    "success": True,
                    "items_processed": 0,
                    "files_updated": 0,
                    "message": "No cache data found for layer"
                }
            
            files_updated = 0
            items_processed = 0
            
            for cache_key, cache_value in cache_data.items():
                try:
                    # Determine memory bank file name
                    file_name = self._determine_memory_file_name(cache_key, layer)
                    file_path = self.memory_bank_path / file_name
                    
                    # Extract content from cache data
                    content = self._extract_content_from_cache_data(cache_value)
                    
                    # Write to memory bank file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    files_updated += 1
                    items_processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing cache item {cache_key}: {str(e)}")
                    continue
            
            return {
                "success": True,
                "layer": layer,
                "items_processed": items_processed,
                "files_updated": files_updated,
                "message": f"Synced {items_processed} items to {files_updated} files"
            }
            
        except Exception as e:
            return {
                "success": False,
                "layer": layer,
                "error": str(e),
                "items_processed": 0,
                "files_updated": 0
            }
    
    async def _resolve_conflicts(self) -> Dict[str, Any]:
        """Resolve conflicts between cache and memory bank data."""
        logger.info("Resolving synchronization conflicts...")
        
        result = {
            "success": True,
            "conflicts_found": 0,
            "conflicts_resolved": 0,
            "conflicts": []
        }
        
        try:
            # Find conflicting files
            conflicts = await self._find_conflicts()
            result["conflicts_found"] = len(conflicts)
            
            for conflict in conflicts:
                try:
                    resolution = await self._resolve_single_conflict(conflict)
                    result["conflicts_resolved"] += 1
                    result["conflicts"].append({
                        "conflict": conflict,
                        "resolution": resolution
                    })
                    
                except Exception as e:
                    logger.error(f"Error resolving conflict: {str(e)}")
                    result["conflicts"].append({
                        "conflict": conflict,
                        "error": str(e)
                    })
                    result["success"] = False
            
            self.sync_metadata["conflicts_resolved"] += result["conflicts_resolved"]
            
            logger.info(f"Conflict resolution completed: {result['conflicts_resolved']}/{result['conflicts_found']} resolved")
            
        except Exception as e:
            error_msg = f"Conflict resolution failed: {str(e)}"
            logger.error(error_msg)
            result["success"] = False
            result["error"] = error_msg
        
        return result
    
    async def _find_conflicts(self) -> List[Dict[str, Any]]:
        """Find conflicts between cache and memory bank data."""
        conflicts = []
        
        try:
            # Get all memory bank files
            memory_files = list(self.memory_bank_path.glob("*.md"))
            
            for file_path in memory_files:
                try:
                    # Check for conflicts in each cache layer
                    for layer in ["predictive", "semantic", "vector", "global", "vector_diary"]:
                        cache_key = f"memory_bank_{file_path.stem}"
                        conflict = await self._check_file_cache_conflict(file_path, cache_key, layer)
                        
                        if conflict:
                            conflicts.append(conflict)
                
                except Exception as e:
                    logger.error(f"Error checking conflicts for file {file_path}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error finding conflicts: {str(e)}")
        
        return conflicts
    
    async def _check_file_cache_conflict(self, file_path: Path, cache_key: str, layer: str) -> Optional[Dict[str, Any]]:
        """Check if a file has conflicts with cache data."""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Get cache data
            cache_data = await self._get_cache_data(cache_key, layer)
            
            if not cache_data:
                return None
            
            # Compare timestamps and content
            file_modified = file_path.stat().st_mtime
            cache_timestamp = cache_data.get("sync_timestamp")
            
            if cache_timestamp:
                cache_time = datetime.fromisoformat(cache_timestamp).timestamp()
                
                # Check if timestamps are close (within sync interval)
                if abs(file_modified - cache_time) > self.sync_config["sync_interval"]:
                    # Check content differences
                    file_hash = hashlib.md5(file_content.encode()).hexdigest()
                    cache_hash = cache_data.get("file_metadata", {}).get("hash")
                    
                    if file_hash != cache_hash:
                        return {
                            "file_path": str(file_path),
                            "cache_key": cache_key,
                            "cache_layer": layer,
                            "file_timestamp": file_modified,
                            "cache_timestamp": cache_time,
                            "file_hash": file_hash,
                            "cache_hash": cache_hash,
                            "conflict_type": "content_mismatch"
                        }
        
        except Exception as e:
            logger.error(f"Error checking conflict for {file_path}: {str(e)}")
        
        return None
    
    async def _resolve_single_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a single conflict based on conflict resolution strategy."""
        try:
            strategy = self.sync_config["conflict_resolution"]
            
            if strategy == "timestamp":
                return await self._resolve_by_timestamp(conflict)
            elif strategy == "content":
                return await self._resolve_by_content(conflict)
            elif strategy == "merge":
                return await self._resolve_by_merge(conflict)
            else:
                return await self._resolve_by_timestamp(conflict)
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "strategy": strategy
            }
    
    async def _resolve_by_timestamp(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict by timestamp (newer wins)."""
        try:
            file_timestamp = conflict["file_timestamp"]
            cache_timestamp = conflict["cache_timestamp"]
            
            if file_timestamp > cache_timestamp:
                # File is newer, update cache
                resolution = "file_wins"
                await self._update_cache_from_file(conflict)
            else:
                # Cache is newer, update file
                resolution = "cache_wins"
                await self._update_file_from_cache(conflict)
            
            return {
                "success": True,
                "resolution": resolution,
                "strategy": "timestamp"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "strategy": "timestamp"
            }
    
    async def _resolve_by_content(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict by content size (larger wins)."""
        try:
            file_path = Path(conflict["file_path"])
            cache_key = conflict["cache_key"]
            layer = conflict["cache_layer"]
            
            # Get file size
            file_size = file_path.stat().st_size
            
            # Get cache data size
            cache_data = await self._get_cache_data(cache_key, layer)
            cache_size = len(str(cache_data))
            
            if file_size > cache_size:
                # File is larger, update cache
                resolution = "file_wins"
                await self._update_cache_from_file(conflict)
            else:
                # Cache is larger, update file
                resolution = "cache_wins"
                await self._update_file_from_cache(conflict)
            
            return {
                "success": True,
                "resolution": resolution,
                "strategy": "content"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "strategy": "content"
            }
    
    async def _resolve_by_merge(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflict by merging content."""
        try:
            file_path = Path(conflict["file_path"])
            cache_key = conflict["cache_key"]
            layer = conflict["cache_layer"]
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Get cache data
            cache_data = await self._get_cache_data(cache_key, layer)
            cache_content = cache_data.get("content", "")
            
            # Merge content (simple concatenation for now)
            merged_content = f"=== File Content ===\n{file_content}\n\n=== Cache Content ===\n{cache_content}"
            
            # Update both file and cache
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(merged_content)
            
            # Update cache
            merged_cache_data = {
                "content": merged_content,
                "source_file": str(file_path),
                "sync_timestamp": datetime.utcnow().isoformat(),
                "file_metadata": {
                    "size": len(merged_content),
                    "modified": file_path.stat().st_mtime,
                    "hash": hashlib.md5(merged_content.encode()).hexdigest(),
                    "merged": True
                }
            }
            
            await self._sync_to_cache_layer(cache_key, merged_cache_data, layer)
            
            return {
                "success": True,
                "resolution": "merged",
                "strategy": "merge"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "strategy": "merge"
            }
    
    async def _update_cache_from_file(self, conflict: Dict[str, Any]):
        """Update cache data from file."""
        file_path = Path(conflict["file_path"])
        cache_key = conflict["cache_key"]
        layer = conflict["cache_layer"]
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cache_data = {
            "content": content,
            "source_file": str(file_path),
            "sync_timestamp": datetime.utcnow().isoformat(),
            "file_metadata": {
                "size": len(content),
                "modified": file_path.stat().st_mtime,
                "hash": hashlib.md5(content.encode()).hexdigest()
            }
        }
        
        await self._sync_to_cache_layer(cache_key, cache_data, layer)
    
    async def _update_file_from_cache(self, conflict: Dict[str, Any]):
        """Update file from cache data."""
        file_path = Path(conflict["file_path"])
        cache_key = conflict["cache_key"]
        layer = conflict["cache_layer"]
        
        cache_data = await self._get_cache_data(cache_key, layer)
        content = cache_data.get("content", "")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    async def _cleanup_old_syncs(self) -> Dict[str, Any]:
        """Clean up old sync backups."""
        try:
            backup_dir = self.memory_bank_path / "backups"
            if not backup_dir.exists():
                return {"success": True, "message": "No backup directory found"}
            
            # Get all backup directories
            backup_dirs = sorted([d for d in backup_dir.iterdir() if d.is_dir()], 
                               key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the most recent backups
            if len(backup_dirs) > self.sync_config["max_sync_backups"]:
                old_backups = backup_dirs[self.sync_config["max_sync_backups"]:]
                removed_count = 0
                
                for old_backup in old_backups:
                    try:
                        shutil.rmtree(old_backup)
                        removed_count += 1
                    except Exception as e:
                        logger.error(f"Error removing backup {old_backup}: {str(e)}")
                
                return {
                    "success": True,
                    "removed_backups": removed_count,
                    "total_backups": len(backup_dirs)
                }
            
            return {
                "success": True,
                "message": f"No cleanup needed, {len(backup_dirs)} backups within limit"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _update_sync_metadata(self, sync_result: Dict[str, Any]):
        """Update synchronization metadata."""
        self.sync_metadata["last_sync"] = sync_result["start_time"]
        self.sync_metadata["sync_count"] += 1
        self.sync_metadata["last_error"] = sync_result.get("last_error")
        
        # Save metadata
        with open(self.sync_metadata_path, 'w') as f:
            json.dump(self.sync_metadata, f, indent=2)
    
    def _generate_sync_summary(self, sync_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate synchronization summary."""
        operations = sync_result.get("operations", {})
        
        return {
            "sync_id": sync_result["sync_id"],
            "duration": (datetime.fromisoformat(sync_result["end_time"]) - 
                        datetime.fromisoformat(sync_result["start_time"])).total_seconds(),
            "status": sync_result["status"],
            "total_operations": len(operations),
            "successful_operations": sum(1 for op in operations.values() if op.get("success", False)),
            "conflicts_resolved": self.sync_metadata["conflicts_resolved"],
            "total_syncs": self.sync_metadata["sync_count"],
            "last_sync": self.sync_metadata["last_sync"]
        }
    
    # Helper methods
    def _determine_cache_layer(self, file_name: str) -> str:
        """Determine cache layer based on file name."""
        file_lower = file_name.lower()
        
        if "predict" in file_lower or "forecast" in file_lower:
            return "predictive"
        elif "semantic" in file_lower or "meaning" in file_lower:
            return "semantic"
        elif "vector" in file_lower or "embedding" in file_lower:
            return "vector"
        elif "global" in file_lower or "knowledge" in file_lower:
            return "global"
        elif "diary" in file_lower or "conversation" in file_lower:
            return "vector_diary"
        else:
            return "semantic"  # Default
    
    def _determine_memory_file_name(self, cache_key: str, layer: str) -> str:
        """Determine memory bank file name from cache key."""
        if cache_key.startswith("memory_bank_"):
            return f"{cache_key[12:]}.md"
        else:
            return f"{cache_key}_{layer}.md"
    
    def _extract_content_from_cache_data(self, cache_data: Dict[str, Any]) -> str:
        """Extract content from cache data."""
        if "content" in cache_data:
            return cache_data["content"]
        elif "value" in cache_data and isinstance(cache_data["value"], dict):
            return json.dumps(cache_data["value"], indent=2)
        else:
            return str(cache_data)
    
    async def _get_cache_data_for_layer(self, layer: str) -> Dict[str, Any]:
        """Get cache data for a specific layer (simulated)."""
        # This would connect to the actual cache MCP server
        # For now, we'll return sample data
        return {
            f"sample_key_{layer}": {
                "content": f"Sample content for {layer} layer",
                "sync_timestamp": datetime.utcnow().isoformat(),
                "file_metadata": {
                    "size": len(f"Sample content for {layer} layer"),
                    "modified": time.time(),
                    "hash": hashlib.md5(f"Sample content for {layer} layer".encode()).hexdigest()
                }
            }
        }
    
    async def _get_cache_data(self, key: str, layer: str) -> Optional[Dict[str, Any]]:
        """Get cache data for a specific key and layer (simulated)."""
        # This would connect to the actual cache MCP server
        # For now, we'll return sample data
        return {
            "content": f"Sample content for {key} in {layer} layer",
            "sync_timestamp": datetime.utcnow().isoformat(),
            "file_metadata": {
                "size": len(f"Sample content for {key} in {layer} layer"),
                "modified": time.time(),
                "hash": hashlib.md5(f"Sample content for {key} in {layer} layer".encode()).hexdigest()
            }
        }
    
    async def _sync_to_cache_layer(self, key: str, data: Dict[str, Any], layer: str) -> Dict[str, Any]:
        """Sync data to a specific cache layer (simulated)."""
        # This would connect to the actual cache MCP server
        # For now, we'll simulate success
        return {
            "success": True,
            "key": key,
            "layer": layer,
            "timestamp": datetime.utcnow().isoformat()
        }

async def main():
    """Main function for memory bank synchronization."""
    try:
        # Initialize sync manager
        sync_manager = MemoryBankSync()
        
        # Perform synchronization
        sync_result = await sync_manager.sync_all()
        
        # Print summary
        print("\n" + "="*50)
        print("MEMORY BANK SYNCHRONIZATION SUMMARY")
        print("="*50)
        print(f"Sync ID: {sync_result['sync_id']}")
        print(f"Status: {sync_result['status']}")
        print(f"Start Time: {sync_result['start_time']}")
        print(f"End Time: {sync_result['end_time']}")
        
        summary = sync_result.get("summary", {})
        print(f"Duration: {summary.get('duration', 0):.2f} seconds")
        print(f"Operations: {summary.get('successful_operations', 0)}/{summary.get('total_operations', 0)} successful")
        print(f"Conflicts Resolved: {summary.get('conflicts_resolved', 0)}")
        
        if sync_result.get("errors"):
            print("\nErrors:")
            for error in sync_result["errors"]:
                print(f"- {error}")
        
        if sync_result.get("conflicts"):
            print("\nConflicts:")
            for conflict in sync_result["conflicts"]:
                print(f"- {conflict['conflict']['file_path']}: {conflict['resolution']}")
        
        print("\nDetailed results saved to sync_metadata.json")
        
    except Exception as e:
        logger.error(f"Synchronization failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())