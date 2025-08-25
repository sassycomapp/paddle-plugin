#!/usr/bin/env python3
"""
Standalone Quota Reset Script

This script provides a command-line interface for executing quota reset operations
outside of the main application context. It can be used for manual resets,
emergency operations, and integration with OS cron jobs.
"""

import argparse
import logging
import sys
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.quota_reset_scheduler import QuotaResetScheduler, ResetPeriod
from src.quota_reset_cron import QuotaResetCronManager
from simba.simba.database.postgres import PostgresDB

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.getLogger().setLevel(level)
    
    # Create file handler
    file_handler = logging.FileHandler('quota_reset.log')
    file_handler.setLevel(level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Add to root logger
    logging.getLogger().addHandler(file_handler)


def reset_quotas(args):
    """Execute quota reset operation."""
    try:
        # Initialize database
        db = PostgresDB()
        
        # Initialize scheduler
        scheduler = QuotaResetScheduler(db=db)
        
        # Start scheduler
        scheduler.start()
        
        try:
            if args.user_id:
                # Reset specific user
                logger.info(f"Resetting quotas for user: {args.user_id}")
                operation = scheduler.execute_quota_reset(
                    user_id=args.user_id,
                    reset_type=args.type,
                    reset_start=args.start_time,
                    reset_end=args.end_time
                )
            else:
                # Reset all users
                logger.info("Resetting quotas for all users")
                operation = scheduler.execute_quota_reset(
                    reset_type=args.type,
                    reset_start=args.start_time,
                    reset_end=args.end_time
                )
            
            # Display results
            print("\n" + "="*50)
            print("QUOTA RESET RESULTS")
            print("="*50)
            print(f"Status: {operation.status.value}")
            print(f"Users Affected: {operation.users_affected}")
            print(f"Tokens Reset: {operation.tokens_reset}")
            print(f"Execution Time: {operation.execution_time:.2f}s" if operation.execution_time else "N/A")
            
            if operation.error_message:
                print(f"Error: {operation.error_message}")
            
            print("="*50)
            
            # Return appropriate exit code
            return 0 if operation.status.value == 'completed' else 1
            
        finally:
            # Stop scheduler
            scheduler.stop()
            
    except Exception as e:
        logger.error(f"Error resetting quotas: {e}")
        print(f"Error: {e}")
        return 1


def schedule_reset(args):
    """Schedule a quota reset operation."""
    try:
        # Initialize database
        db = PostgresDB()
        
        # Initialize scheduler
        scheduler = QuotaResetScheduler(db=db)
        
        try:
            # Schedule the reset
            schedule_id = scheduler.schedule_quota_reset(
                user_id=args.user_id,
                reset_type=ResetPeriod(args.type),
                reset_interval=args.interval,
                reset_time=args.time
            )
            
            print(f"\nScheduled quota reset with ID: {schedule_id}")
            print(f"Type: {args.type}")
            print(f"Interval: {args.interval}")
            print(f"Time: {args.time}")
            if args.user_id:
                print(f"User: {args.user_id}")
            
            return 0
            
        finally:
            # Stop scheduler
            scheduler.stop()
            
    except Exception as e:
        logger.error(f"Error scheduling reset: {e}")
        print(f"Error: {e}")
        return 1


def list_schedules(args):
    """List scheduled quota resets."""
    try:
        # Initialize database
        db = PostgresDB()
        
        # Get pending schedules
        schedules = db.get_pending_resets(args.limit)
        
        if not schedules:
            print("No pending schedules found.")
            return 0
        
        print(f"\nPending Quota Reset Schedules (showing {len(schedules)} of {args.limit})")
        print("="*80)
        
        for schedule in schedules:
            print(f"ID: {schedule['id']}")
            print(f"User: {schedule['user_id'] or 'All Users'}")
            print(f"Type: {schedule['reset_type']}")
            print(f"Interval: {schedule['reset_interval']}")
            print(f"Time: {schedule['reset_time']}")
            print(f"Next Reset: {schedule['next_reset']}")
            print(f"Active: {'Yes' if schedule['is_active'] else 'No'}")
            print("-" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error listing schedules: {e}")
        print(f"Error: {e}")
        return 1


def cancel_schedule(args):
    """Cancel a scheduled quota reset."""
    try:
        # Initialize database
        db = PostgresDB()
        
        # Cancel the schedule
        success = db.cancel_scheduled_reset(args.schedule_id)
        
        if success:
            print(f"Cancelled scheduled quota reset: {args.schedule_id}")
            return 0
        else:
            print(f"Schedule not found: {args.schedule_id}")
            return 1
            
    except Exception as e:
        logger.error(f"Error cancelling schedule: {e}")
        print(f"Error: {e}")
        return 1


def show_history(args):
    """Show quota reset history."""
    try:
        # Initialize database
        db = PostgresDB()
        
        # Get history
        history = db.get_reset_history(
            user_id=args.user_id,
            start_date=args.start_date,
            end_date=args.end_date,
            limit=args.limit
        )
        
        if not history:
            print("No reset history found.")
            return 0
        
        print(f"\nQuota Reset History (showing {len(history)} of {args.limit})")
        print("="*100)
        
        for record in history:
            print(f"ID: {record['id']}")
            print(f"Schedule ID: {record['schedule_id']}")
            print(f"User: {record['user_id'] or 'All Users'}")
            print(f"Type: {record['reset_type']}")
            print(f"Start: {record['reset_start']}")
            print(f"End: {record['reset_end']}")
            print(f"Tokens Reset: {record['tokens_reset']}")
            print(f"Users Affected: {record['users_affected']}")
            print(f"Status: {record['status']}")
            print(f"Execution Time: {record['execution_time']}")
            print(f"Created: {record['created_at']}")
            if record['error_message']:
                print(f"Error: {record['error_message']}")
            print("-" * 100)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error showing history: {e}")
        print(f"Error: {e}")
        return 1


def show_health(args):
    """Show system health status."""
    try:
        # Initialize database
        db = PostgresDB()
        
        # Get health status
        health = db.get_quota_reset_health()
        
        print("\nQuota Reset System Health")
        print("="*50)
        print(f"Total Schedules: {health['total_schedules']}")
        print(f"Active Schedules: {health['active_schedules']}")
        print(f"Pending Resets: {health['pending_resets']}")
        print(f"Last Reset: {health['last_reset']}")
        print(f"Next Reset: {health['next_reset']}")
        print(f"System Status: {health['system_status']}")
        print("="*50)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error showing health: {e}")
        print(f"Error: {e}")
        return 1


def monitor_system(args):
    """Monitor the quota reset system."""
    try:
        # Initialize cron manager
        cron_manager = QuotaResetCronManager()
        
        print("Starting quota reset system monitor...")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                # Get system health
                health = cron_manager.get_system_health()
                
                # Clear screen
                print("\033[H\033[J", end="")
                
                # Display health
                print("Quota Reset System Monitor")
                print("="*50)
                print(f"Timestamp: {health['timestamp']}")
                print(f"Cron Manager: {health['cron_manager_status']}")
                print(f"Total Cron Jobs: {health['total_cron_jobs']}")
                print(f"Enabled Cron Jobs: {health['enabled_cron_jobs']}")
                print(f"Scheduler Status: {health['scheduler_status']}")
                print(f"Database Status: {health['database_status']}")
                print(f"Recent Success Rate: {health['recent_success_rate']:.1%}")
                print("="*50)
                
                # Wait before next update
                import time
                time.sleep(args.interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            return 0
            
    except Exception as e:
        logger.error(f"Error monitoring system: {e}")
        print(f"Error: {e}")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Quota Reset Management Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Reset all users' quotas daily
  python reset_quotas.py --reset --type daily
  
  # Reset specific user's quotas
  python reset_quotas.py --reset --user-id user123 --type daily
  
  # Schedule a weekly reset
  python reset_quotas.py --schedule --type weekly --interval "7 days" --time "02:00:00"
  
  # List pending schedules
  python reset_quotas.py --list-schedules --limit 10
  
  # Cancel a schedule
  python reset_quotas.py --cancel --schedule-id 123
  
  # Show reset history
  python reset_quotas.py --history --limit 50
  
  # Show system health
  python reset_quotas.py --health
  
  # Monitor system
  python reset_quotas.py --monitor --interval 60
        """
    )
    
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--config', '-c', help='Configuration file path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Execute quota reset')
    reset_parser.add_argument('--user-id', help='Specific user to reset')
    reset_parser.add_argument('--type', choices=['daily', 'weekly', 'monthly', 'custom'], 
                            default='daily', help='Reset type')
    reset_parser.add_argument('--start-time', help='Start time (ISO format)')
    reset_parser.add_argument('--end-time', help='End time (ISO format)')
    
    # Schedule command
    schedule_parser = subparsers.add_parser('schedule', help='Schedule quota reset')
    schedule_parser.add_argument('--user-id', help='Specific user to reset')
    schedule_parser.add_argument('--type', choices=['daily', 'weekly', 'monthly', 'custom'], 
                               default='daily', help='Reset type')
    schedule_parser.add_argument('--interval', default='1 day', help='Reset interval')
    schedule_parser.add_argument('--time', default='00:00:00', help='Reset time')
    
    # List schedules command
    list_parser = subparsers.add_parser('list-schedules', help='List pending schedules')
    list_parser.add_argument('--limit', type=int, default=10, help='Maximum number to show')
    
    # Cancel schedule command
    cancel_parser = subparsers.add_parser('cancel', help='Cancel scheduled reset')
    cancel_parser.add_argument('--schedule-id', type=int, required=True, help='Schedule ID to cancel')
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show reset history')
    history_parser.add_argument('--user-id', help='Filter by user ID')
    history_parser.add_argument('--start-date', help='Start date (ISO format)')
    history_parser.add_argument('--end-date', help='End date (ISO format)')
    history_parser.add_argument('--limit', type=int, default=50, help='Maximum number to show')
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Show system health')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor system')
    monitor_parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Execute command
    if args.command == 'reset':
        return reset_quotas(args)
    elif args.command == 'schedule':
        return schedule_reset(args)
    elif args.command == 'list-schedules':
        return list_schedules(args)
    elif args.command == 'cancel':
        return cancel_schedule(args)
    elif args.command == 'history':
        return show_history(args)
    elif args.command == 'health':
        return show_health(args)
    elif args.command == 'monitor':
        return monitor_system(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())