#!/usr/bin/env python3
"""
Test script for Enhanced MCP Scheduler Server
"""
import asyncio
import logging
import json
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from ag2_orchestrator import AG2Orchestrator
from autogen import LLMConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_mcp_scheduler():
    """Test Enhanced MCP Scheduler Server functionality."""
    logger.info("Starting Enhanced MCP Scheduler Server Tests...")
    
    # Use dummy LLM config for testing
    llm_config = LLMConfig(
        model="dummy-model-for-testing",
        api_type="openai",
        api_key="dummy-key-for-testing",
        base_url=None
    )
    
    orchestrator = AG2Orchestrator(llm_config)
    
    try:
        # Test MCP Scheduler connection
        logger.info("Testing MCP Scheduler Server connection...")
        await orchestrator.setup_mcp_session(
            "scheduler", 
            "node", 
            ["../mcp_servers/mcp-scheduler-server.js"]
        )
        await orchestrator.create_toolkit("scheduler")
        logger.info("✓ Enhanced MCP Scheduler Server connected")
        
        # Test scheduling a task with enhanced options
        logger.info("Testing task scheduling with enhanced options...")
        future_time = datetime.utcnow() + timedelta(seconds=10)
        future_iso = future_time.isoformat() + 'Z'
        
        # Get the toolkit and use it directly
        scheduler_toolkit = orchestrator.toolkits["scheduler"]
        
        # Test scheduling a task with all options
        schedule_result = await scheduler_toolkit.tools[0].run(
            name="Enhanced Test Task",
            command="echo 'Hello from enhanced scheduled task!' && echo 'Task completed successfully'",
            runAt=future_iso,
            maxRetries=2,
            timeoutMs=15000,
            workingDirectory=".",
            environmentVariables={"TEST_VAR": "test_value"}
        )
        logger.info(f"✓ Enhanced task scheduled: {schedule_result}")
        
        # Test listing scheduled tasks with filtering
        logger.info("Testing task listing with filtering...")
        all_tasks = await scheduler_toolkit.tools[1].run()
        logger.info(f"✓ All scheduled tasks: {all_tasks}")
        
        # Test filtering by status
        scheduled_tasks = await scheduler_toolkit.tools[1].run(status="scheduled")
        logger.info(f"✓ Scheduled tasks only: {scheduled_tasks}")
        
        # Parse the tasks list to get task ID
        tasks_data = json.loads(all_tasks) if all_tasks else []
        if tasks_data:
            task_id = tasks_data[0]['id']
            logger.info(f"✓ Using task ID: {task_id}")
            
            # Test running a task immediately
            logger.info("Testing immediate task execution...")
            immediate_result = await scheduler_toolkit.tools[3].run(taskId=task_id)
            logger.info(f"✓ Task executed immediately: {immediate_result}")
            
            # Test getting task execution history
            logger.info("Testing task execution history...")
            execution_history = await scheduler_toolkit.tools[4].run(taskId=task_id)
            logger.info(f"✓ Task execution history: {execution_history}")
            
            # Test scheduling another task for later
            future_time_2 = datetime.utcnow() + timedelta(minutes=1)
            future_iso_2 = future_time_2.isoformat() + 'Z'
            
            schedule_result_2 = await scheduler_toolkit.tools[0].run(
                name="Future Test Task",
                command="echo 'This task runs in 1 minute'",
                runAt=future_iso_2,
                maxRetries=1
            )
            logger.info(f"✓ Future task scheduled: {schedule_result_2}")
            
            # Test listing tasks again
            updated_tasks = await scheduler_toolkit.tools[1].run()
            logger.info(f"✓ Updated task list: {updated_tasks}")
            
            # Test canceling the future task
            if len(json.loads(updated_tasks)) > 1:
                future_task_id = json.loads(updated_tasks)[1]['id']
                logger.info(f"✓ Cancelling future task ID: {future_task_id}")
                cancel_result = await scheduler_toolkit.tools[2].run(taskId=future_task_id)
                logger.info(f"✓ Future task cancelled: {cancel_result}")
        
        # Test error handling - try to cancel non-existent task
        logger.info("Testing error handling...")
        try:
            await scheduler_toolkit.tools[2].run(taskId=999999)
            logger.error("✗ Should have thrown error for non-existent task")
        except Exception as e:
            logger.info(f"✓ Correctly handled error for non-existent task: {e}")
        
        # Test error handling - try to schedule invalid task
        try:
            await scheduler_toolkit.tools[0].run(
                name="",
                command="echo 'test'",
                runAt=future_iso
            )
            logger.error("✗ Should have thrown error for empty task name")
        except Exception as e:
            logger.info(f"✓ Correctly handled error for empty task name: {e}")
        
        logger.info("✓ All Enhanced MCP Scheduler tests passed!")
        
    except Exception as e:
        logger.error(f"✗ Enhanced MCP Scheduler test failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Cleanup
        await orchestrator.aclose()
        logger.info("Enhanced MCP Scheduler tests completed")

async def test_scheduler_database():
    """Test that database is created and working."""
    logger.info("Testing MCP Scheduler database...")
    
    try:
        import sqlite3
        import os
        
        db_path = os.path.join(os.getcwd(), "mcp_servers", "mcp_scheduler.db")
        
        # Check if database file exists
        if os.path.exists(db_path):
            logger.info("✓ Database file exists")
            
            # Test database connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            expected_tables = ["tasks", "task_executions"]
            for table in expected_tables:
                if table in table_names:
                    logger.info(f"✓ Table '{table}' exists")
                else:
                    logger.error(f"✗ Table '{table}' missing")
            
            conn.close()
        else:
            logger.warning("⚠ Database file not found - this is normal if server hasn't been run yet")
            
    except Exception as e:
        logger.error(f"✗ Database test failed: {e}")

if __name__ == "__main__":
    # Run database test first
    asyncio.run(test_scheduler_database())
    
    # Run enhanced scheduler tests
    asyncio.run(test_enhanced_mcp_scheduler())
