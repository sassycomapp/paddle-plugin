"""
Quota Reset Cron Job Integration

This module provides OS-level cron job integration for the quota reset system,
allowing for system-level scheduling and monitoring of quota reset operations.
"""

import logging
import subprocess
import json
import os
import sys
import signal
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import argparse
import schedule
import requests
from dataclasses import dataclass, asdict

from src.quota_reset_scheduler import QuotaResetScheduler, ResetPeriod
from simba.simba.database.postgres import PostgresDB

logger = logging.getLogger(__name__)


@dataclass
class CronJobConfig:
    """Cron job configuration."""
    name: str
    schedule: str
    command: str
    working_directory: str = "."
    environment: Optional[Dict[str, str]] = None
    timeout: int = 300
    retry_count: int = 3
    retry_delay: int = 60
    enabled: bool = True
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.environment is None:
            self.environment = {}


class QuotaResetCronManager:
    """
    Manager for OS-level cron jobs related to quota reset operations.
    
    Provides integration between OS cron jobs and the quota reset system,
    allowing for system-level scheduling and monitoring.
    """
    
    def __init__(self, config_file: Optional[str] = None, 
                 scheduler: Optional[QuotaResetScheduler] = None,
                 db: Optional[PostgresDB] = None):
        """
        Initialize the cron manager.
        
        Args:
            config_file: Path to configuration file
            scheduler: Quota reset scheduler instance
            db: Database instance
        """
        self.config_file = config_file or "quota_reset_cron_config.json"
        self.scheduler = scheduler or QuotaResetScheduler()
        self.db = db or PostgresDB()
        
        # Load configuration
        self.cron_jobs: Dict[str, CronJobConfig] = {}
        self.load_config()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Setup logging
        self.setup_logging()
        
        logger.info("QuotaResetCronManager initialized")
    
    def setup_logging(self):
        """Setup logging for the cron manager."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('quota_reset_cron.log'),
                logging.StreamHandler()
            ]
        )
    
    def load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                for job_name, job_config in config_data.get('cron_jobs', {}).items():
                    self.cron_jobs[job_name] = CronJobConfig(
                        name=job_name,
                        schedule=job_config['schedule'],
                        command=job_config['command'],
                        working_directory=job_config.get('working_directory', '.'),
                        environment=job_config.get('environment', {}),
                        timeout=job_config.get('timeout', 300),
                        retry_count=job_config.get('retry_count', 3),
                        retry_delay=job_config.get('retry_delay', 60),
                        enabled=job_config.get('enabled', True),
                        metadata=job_config.get('metadata', {})
                    )
                
                logger.info(f"Loaded {len(self.cron_jobs)} cron jobs from {self.config_file}")
            else:
                logger.warning(f"Config file not found: {self.config_file}")
                self.create_default_config()
                
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """Create default configuration file."""
        default_config = {
            "cron_jobs": {
                "daily_quota_reset": {
                    "schedule": "0 0 * * *",
                    "command": "python scripts/reset_quotas.py --type daily",
                    "working_directory": ".",
                    "environment": {},
                    "timeout": 300,
                    "retry_count": 3,
                    "retry_delay": 60,
                    "enabled": True,
                    "metadata": {
                        "description": "Daily quota reset for all users",
                        "priority": "high"
                    }
                },
                "weekly_quota_reset": {
                    "schedule": "0 0 * * 1",
                    "command": "python scripts/reset_quotas.py --type weekly",
                    "working_directory": ".",
                    "environment": {},
                    "timeout": 300,
                    "retry_count": 3,
                    "retry_delay": 60,
                    "enabled": True,
                    "metadata": {
                        "description": "Weekly quota reset for all users",
                        "priority": "medium"
                    }
                },
                "monthly_quota_reset": {
                    "schedule": "0 0 1 * *",
                    "command": "python scripts/reset_quotas.py --type monthly",
                    "working_directory": ".",
                    "environment": {},
                    "timeout": 300,
                    "retry_count": 3,
                    "retry_delay": 60,
                    "enabled": True,
                    "metadata": {
                        "description": "Monthly quota reset for all users",
                        "priority": "medium"
                    }
                },
                "quota_reset_monitor": {
                    "schedule": "*/5 * * * *",
                    "command": "python scripts/reset_quotas.py --monitor",
                    "working_directory": ".",
                    "environment": {},
                    "timeout": 60,
                    "retry_count": 1,
                    "retry_delay": 30,
                    "enabled": True,
                    "metadata": {
                        "description": "Monitor quota reset system health",
                        "priority": "low"
                    }
                }
            }
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            # Load the default config
            for job_name, job_config in default_config['cron_jobs'].items():
                self.cron_jobs[job_name] = CronJobConfig(
                    name=job_name,
                    schedule=job_config['schedule'],
                    command=job_config['command'],
                    working_directory=job_config.get('working_directory', '.'),
                    environment=job_config.get('environment', {}),
                    timeout=job_config.get('timeout', 300),
                    retry_count=job_config.get('retry_count', 3),
                    retry_delay=job_config.get('retry_delay', 60),
                    enabled=job_config.get('enabled', True),
                    metadata=job_config.get('metadata', {})
                )
            
            logger.info(f"Created default config file: {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error creating default config: {e}")
    
    def save_config(self):
        """Save configuration to file."""
        try:
            config_data = {
                "cron_jobs": {
                    name: asdict(job) for name, job in self.cron_jobs.items()
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Saved config to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def add_cron_job(self, job: CronJobConfig):
        """Add a new cron job."""
        self.cron_jobs[job.name] = job
        self.save_config()
        logger.info(f"Added cron job: {job.name}")
    
    def remove_cron_job(self, job_name: str):
        """Remove a cron job."""
        if job_name in self.cron_jobs:
            del self.cron_jobs[job_name]
            self.save_config()
            logger.info(f"Removed cron job: {job_name}")
        else:
            logger.warning(f"Cron job not found: {job_name}")
    
    def enable_cron_job(self, job_name: str):
        """Enable a cron job."""
        if job_name in self.cron_jobs:
            self.cron_jobs[job_name].enabled = True
            self.save_config()
            logger.info(f"Enabled cron job: {job_name}")
        else:
            logger.warning(f"Cron job not found: {job_name}")
    
    def disable_cron_job(self, job_name: str):
        """Disable a cron job."""
        if job_name in self.cron_jobs:
            self.cron_jobs[job_name].enabled = False
            self.save_config()
            logger.info(f"Disabled cron job: {job_name}")
        else:
            logger.warning(f"Cron job not found: {job_name}")
    
    def execute_cron_job(self, job_name: str) -> Dict[str, Any]:
        """
        Execute a cron job.
        
        Args:
            job_name: Name of the job to execute
            
        Returns:
            Execution result
        """
        if job_name not in self.cron_jobs:
            return {
                'success': False,
                'error': f'Cron job not found: {job_name}'
            }
        
        job = self.cron_jobs[job_name]
        
        if not job.enabled:
            return {
                'success': False,
                'error': f'Cron job is disabled: {job_name}'
            }
        
        logger.info(f"Executing cron job: {job_name}")
        
        # Prepare environment
        env = os.environ.copy()
        env.update(job.environment)
        
        # Prepare working directory
        work_dir = os.path.abspath(job.working_directory)
        
        # Execute with retry logic
        for attempt in range(job.retry_count):
            try:
                start_time = time.time()
                
                # Execute the command
                result = subprocess.run(
                    job.command,
                    shell=True,
                    cwd=work_dir,
                    env=env,
                    timeout=job.timeout,
                    capture_output=True,
                    text=True
                )
                
                execution_time = time.time() - start_time
                
                # Log result
                if result.returncode == 0:
                    logger.info(f"Cron job {job_name} completed successfully in {execution_time:.2f}s")
                    return {
                        'success': True,
                        'return_code': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'execution_time': execution_time,
                        'attempt': attempt + 1
                    }
                else:
                    logger.warning(f"Cron job {job_name} failed with return code {result.returncode}")
                    if attempt < job.retry_count - 1:
                        logger.info(f"Retrying in {job.retry_delay}s...")
                        time.sleep(job.retry_delay)
                    else:
                        return {
                            'success': False,
                            'return_code': result.returncode,
                            'stdout': result.stdout,
                            'stderr': result.stderr,
                            'execution_time': execution_time,
                            'attempt': attempt + 1
                        }
                        
            except subprocess.TimeoutExpired:
                logger.error(f"Cron job {job_name} timed out after {job.timeout}s")
                if attempt < job.retry_count - 1:
                    logger.info(f"Retrying in {job.retry_delay}s...")
                    time.sleep(job.retry_delay)
                else:
                    return {
                        'success': False,
                        'error': 'Timeout',
                        'execution_time': job.timeout,
                        'attempt': attempt + 1
                    }
                    
            except Exception as e:
                logger.error(f"Error executing cron job {job_name}: {e}")
                if attempt < job.retry_count - 1:
                    logger.info(f"Retrying in {job.retry_delay}s...")
                    time.sleep(job.retry_delay)
                else:
                    return {
                        'success': False,
                        'error': str(e),
                        'execution_time': time.time() - start_time,
                        'attempt': attempt + 1
                    }
        
        return {
            'success': False,
            'error': 'All retry attempts failed'
        }
    
    def setup_schedule(self):
        """Setup the schedule for all enabled cron jobs."""
        for job_name, job in self.cron_jobs.items():
            if job.enabled:
                try:
                    # Parse the cron schedule and set up the job
                    self._setup_cron_schedule(job)
                    logger.info(f"Setup schedule for cron job: {job_name}")
                except Exception as e:
                    logger.error(f"Error setting up schedule for {job_name}: {e}")
    
    def _setup_cron_schedule(self, job: CronJobConfig):
        """Setup schedule for a single cron job."""
        # This is a simplified implementation
        # In a real implementation, you would use a proper cron library
        # or integrate with the system cron daemon
        
        # For demonstration, we'll use the schedule library
        # Note: This is not a full cron implementation
        
        # Parse the cron schedule (simplified)
        parts = job.schedule.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron schedule: {job.schedule}")
        
        minute, hour, day, month, weekday = parts
        
        # Setup the job (simplified)
        if minute == '*' and hour == '*' and day == '*' and month == '*' and weekday == '*':
            # Every minute
            schedule.every().minute.do(self._execute_scheduled_job, job.name)
        elif minute == '0' and hour == '*' and day == '*' and month == '*' and weekday == '*':
            # Every hour
            schedule.every().hour.do(self._execute_scheduled_job, job.name)
        elif minute == '0' and hour == '0' and day == '*' and month == '*' and weekday == '*':
            # Every day at midnight
            schedule.every().day.at("00:00").do(self._execute_scheduled_job, job.name)
        elif minute == '0' and hour == '0' and day == '*' and month == '*' and weekday == '1':
            # Every Monday at midnight
            schedule.every().monday.at("00:00").do(self._execute_scheduled_job, job.name)
        elif minute == '0' and hour == '0' and day == '1' and month == '*' and weekday == '*':
            # Every 1st of the month at midnight
            schedule.every(1).day.at("00:00").do(self._execute_scheduled_job, job.name)
        else:
            # Custom schedule (simplified)
            logger.warning(f"Custom cron schedule not fully supported: {job.schedule}")
            # For now, just run every hour
            schedule.every().hour.do(self._execute_scheduled_job, job.name)
    
    def _execute_scheduled_job(self, job_name: str):
        """Execute a scheduled job."""
        result = self.execute_cron_job(job_name)
        
        # Log the result
        if result['success']:
            logger.info(f"Scheduled job {job_name} completed successfully")
        else:
            logger.error(f"Scheduled job {job_name} failed: {result.get('error', 'Unknown error')}")
        
        # Store execution result in database
        try:
            self._store_execution_result(job_name, result)
        except Exception as e:
            logger.error(f"Error storing execution result: {e}")
    
    def _store_execution_result(self, job_name: str, result: Dict[str, Any]):
        """Store execution result in database."""
        try:
            query = """
                INSERT INTO quota_reset_cron_history 
                (job_name, success, return_code, stdout, stderr, execution_time, attempt, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            self.db.execute_query(
                query,
                (
                    job_name,
                    result['success'],
                    result.get('return_code'),
                    result.get('stdout', ''),
                    result.get('stderr', ''),
                    result.get('execution_time', 0),
                    result.get('attempt', 1)
                )
            )
            
        except Exception as e:
            logger.error(f"Error storing execution result: {e}")
    
    def start(self):
        """Start the cron manager."""
        logger.info("Starting QuotaResetCronManager")
        
        # Setup schedules
        self.setup_schedule()
        
        # Start the scheduler
        self.scheduler.start()
        
        # Start the schedule loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, stopping...")
                break
            except Exception as e:
                logger.error(f"Error in schedule loop: {e}")
                time.sleep(5)
        
        # Cleanup
        self.stop()
    
    def stop(self):
        """Stop the cron manager."""
        logger.info("Stopping QuotaResetCronManager")
        
        # Stop the scheduler
        self.scheduler.stop()
        
        # Clear all scheduled jobs
        schedule.clear()
        
        logger.info("QuotaResetCronManager stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        logger.info(f"Received signal {signum}, stopping...")
        self.stop()
        sys.exit(0)
    
    def get_cron_jobs(self) -> Dict[str, CronJobConfig]:
        """Get all cron jobs."""
        return self.cron_jobs.copy()
    
    def get_cron_job(self, job_name: str) -> Optional[CronJobConfig]:
        """Get a specific cron job."""
        return self.cron_jobs.get(job_name)
    
    def get_execution_history(self, job_name: Optional[str] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution history."""
        try:
            if job_name:
                query = """
                    SELECT * FROM quota_reset_cron_history
                    WHERE job_name = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                results = self.db.fetch_all(query, (job_name, limit))
            else:
                query = """
                    SELECT * FROM quota_reset_cron_history
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                results = self.db.fetch_all(query, (limit,))
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting execution history: {e}")
            return []
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status."""
        try:
            # Get cron jobs status
            enabled_jobs = len([job for job in self.cron_jobs.values() if job.enabled])
            total_jobs = len(self.cron_jobs)
            
            # Get scheduler health
            scheduler_health = self.scheduler.get_system_health()
            
            # Get recent execution results
            recent_results = self.get_execution_history(limit=10)
            successful_executions = len([r for r in recent_results if r['success']])
            
            return {
                'cron_manager_status': 'running',
                'total_cron_jobs': total_jobs,
                'enabled_cron_jobs': enabled_jobs,
                'scheduler_status': scheduler_health['scheduler_status'],
                'database_status': scheduler_health['database_status'],
                'recent_success_rate': successful_executions / len(recent_results) if recent_results else 0,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'cron_manager_status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


def main():
    """Main entry point for the cron manager."""
    parser = argparse.ArgumentParser(description='Quota Reset Cron Manager')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--daemon', '-d', action='store_true', help='Run as daemon')
    parser.add_argument('--health', '-h', action='store_true', help='Show system health')
    parser.add_argument('--list-jobs', '-l', action='store_true', help='List all cron jobs')
    parser.add_argument('--job', '-j', help='Execute specific job')
    
    args = parser.parse_args()
    
    # Initialize cron manager
    cron_manager = QuotaResetCronManager(config_file=args.config)
    
    if args.health:
        # Show system health
        health = cron_manager.get_system_health()
        print(json.dumps(health, indent=2))
        return
    
    if args.list_jobs:
        # List all cron jobs
        jobs = cron_manager.get_cron_jobs()
        print("Cron Jobs:")
        for job_name, job in jobs.items():
            status = "enabled" if job.enabled else "disabled"
            print(f"  {job_name}: {status} ({job.schedule})")
        return
    
    if args.job:
        # Execute specific job
        result = cron_manager.execute_cron_job(args.job)
        print(json.dumps(result, indent=2))
        return
    
    # Start the cron manager
    try:
        cron_manager.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        cron_manager.stop()


if __name__ == "__main__":
    main()