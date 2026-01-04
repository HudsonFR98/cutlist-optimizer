import logging
import uuid
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from flask import current_app

from cutlist_optimizer.lib import config
from cutlist_optimizer.lib.telegram import send_error_notification_telegram
from cutlist_optimizer.lib.backup import create_backup, cleanup_old_backups, list_backups
from cutlist_optimizer.models.task import TaskExecution, ScheduledTask
from cutlist_optimizer.lib.database import DBSession

log = logging.getLogger(__name__)


class TaskScheduler:
    """Task scheduler service using APScheduler"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self._registered_tasks = {}
        self._task_metadata = {}  # Store cron expressions and descriptions
        self._pending_schedules = []
        self._started = False
    
    def start(self):
        """Start the scheduler (only once)"""
        if self._started:
            log.debug("Task scheduler already started, skipping")
            return
            
        if not self.scheduler.running:
            self.scheduler.start()
            self._started = True
            log.info("Task scheduler started")
            # Import task models to ensure they are registered
            from cutlist_optimizer.models.task import TaskExecution, ScheduledTask
            self._load_scheduled_tasks()
            self._schedule_pending_tasks()
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self._started = False
            log.info("Task scheduler shutdown")
    
    def register_task(self, task_name, task_function, cron_expression=None, description=None):
        """Register a task function with optional scheduling"""
        # Prevent duplicate registration
        if task_name in self._registered_tasks:
            log.debug(f"Task '{task_name}' already registered, skipping")
            return
            
        self._registered_tasks[task_name] = task_function
        # Store metadata for comparison with database
        self._task_metadata[task_name] = {
            'cron_expression': cron_expression,
            'description': description
        }
        log.debug(f"Registered task: {task_name}")
        
        # If cron expression provided, schedule the task
        if cron_expression:
            self._pending_schedules.append({
                'task_name': task_name,
                'cron_expression': cron_expression,
                'description': description
            })
    
    def schedule_task(self, task_name, cron_expression, description=None, 
                     task_args=None, task_kwargs=None):
        """Schedule a task with cron expression"""
        if task_name not in self._registered_tasks:
            raise ValueError(f"Task '{task_name}' is not registered")
        
        # Check if task already exists in database
        existing_task = ScheduledTask.get_task_by_name(task_name)
        if existing_task:
            log.debug(f"Task '{task_name}' already scheduled in database, skipping")
            return existing_task
        
        # Store in database
        scheduled_task = ScheduledTask(
            task_name=task_name,
            task_function=task_name,
            cron_expression=cron_expression,
            description=description,
            task_args=task_args or {},
            task_kwargs=task_kwargs or {}
        )
        
        try:
            DBSession.add(scheduled_task)
            DBSession.commit()
            
            # Add to scheduler
            self._add_job_to_scheduler(scheduled_task)
            log.info(f"Scheduled task '{task_name}' with cron: {cron_expression}")
            
            return scheduled_task
            
        except Exception as e:
            DBSession.rollback()
            log.error(f"Failed to schedule task '{task_name}': {e}")
            raise
    
    def _schedule_pending_tasks(self):
        """Schedule all pending tasks that were registered with decorator"""
        for pending in self._pending_schedules:
            try:
                # Check if task already exists in database
                existing_task = ScheduledTask.get_task_by_name(pending['task_name'])
                if not existing_task:
                    self.schedule_task(
                        task_name=pending['task_name'],
                        cron_expression=pending['cron_expression'],
                        description=pending['description']
                    )
                else:
                    log.debug(f"Task '{pending['task_name']}' already scheduled")
            except Exception as e:
                log.error(f"Failed to schedule pending task '{pending['task_name']}': {e}")
        
        # Clear pending schedules
        self._pending_schedules.clear()
    
    def _add_job_to_scheduler(self, scheduled_task):
        """Add a job to the APScheduler"""
        try:
            # Check if job already exists in scheduler
            existing_job = self.scheduler.get_job(scheduled_task.task_name)
            if existing_job:
                log.debug(f"Job '{scheduled_task.task_name}' already exists in scheduler, skipping")
                return
            
            # Parse cron expression (format: "minute hour day month day_of_week")
            parts = scheduled_task.cron_expression.split()
            if len(parts) != 5:
                raise ValueError(f"Invalid cron expression: {scheduled_task.cron_expression}")
            
            minute, hour, day, month, day_of_week = parts
            
            # Create trigger
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )
            
            # Add job to scheduler
            job = self.scheduler.add_job(
                func=self._execute_task,
                trigger=trigger,
                args=[scheduled_task.task_name, scheduled_task.task_args, scheduled_task.task_kwargs],
                id=scheduled_task.task_name,
                replace_existing=True
            )
            
            log.info(f"Added job '{scheduled_task.task_name}' to scheduler")
            
            # Update next run time (may not be available immediately)
            try:
                scheduled_task.next_run = job.next_run_time
            except AttributeError:
                # next_run_time may not be available immediately
                scheduled_task.next_run = None
            DBSession.commit()
            
        except Exception as e:
            log.error(f"Failed to add job to scheduler: {e}")
            raise
    
    def _load_scheduled_tasks(self):
        """Load scheduled tasks from database"""
        try:
            # Load all scheduled tasks to restore their state
            scheduled_tasks = ScheduledTask.query.all()
            for task in scheduled_tasks:
                if task.task_name in self._registered_tasks:
                    # Check if cron expression or description has changed
                    metadata = self._task_metadata[task.task_name]
                    cron_changed = metadata['cron_expression'] != task.cron_expression
                    description_changed = metadata['description'] != task.description
                    
                    if cron_changed or description_changed:
                        # Update the task in database
                        if cron_changed:
                            old_cron = task.cron_expression
                            task.cron_expression = metadata['cron_expression']
                            log.info(f"Updated cron expression for task '{task.task_name}': {old_cron} -> {task.cron_expression}")
                        
                        if description_changed:
                            old_desc = task.description
                            task.description = metadata['description']
                            log.info(f"Updated description for task '{task.task_name}': {old_desc} -> {task.description}")
                        
                        DBSession.commit()
                    
                    # Add job to scheduler (this will update the next_run time)
                    self._add_job_to_scheduler(task)
                else:
                    # Delete task from database if it's no longer in code
                    log.info(f"Deleting task '{task.task_name}' from database (no longer in code)")
                    DBSession.delete(task)
                    DBSession.commit()
        except Exception as e:
            log.error(f"Failed to load scheduled tasks: {e}")
    

    
    def _execute_task(self, task_name, task_args, task_kwargs):
        """Execute a task and record the result"""
        task_id = str(uuid.uuid4())
        execution = TaskExecution(task_name, task_id, task_args, task_kwargs)
        
        try:
            DBSession.add(execution)
            DBSession.commit()
            
            # Mark as running
            execution.mark_running()
            DBSession.commit()
            
            log.info(f"Executing task '{task_name}' (ID: {task_id})")
            
            # Execute the task
            task_function = self._registered_tasks[task_name]
            result = task_function(*task_args, **task_kwargs)
            
            # Mark as completed
            execution.mark_completed(result)
            
            # Update the last_run and next_run fields in ScheduledTask
            scheduled_task = ScheduledTask.get_task_by_name(task_name)
            if scheduled_task:
                scheduled_task.last_run = datetime.utcnow()
                
                # Get the updated next run time from the scheduler
                job = self.scheduler.get_job(task_name)
                if job:
                    try:
                        if job.next_run_time:
                            scheduled_task.next_run = job.next_run_time
                            log.debug(f"Updated next_run for task '{task_name}' to {job.next_run_time}")
                    except AttributeError:
                        # next_run_time may not be available
                        pass
                
                DBSession.commit()
                log.debug(f"Updated last_run for task '{task_name}'")
            
            log.info(f"Task '{task_name}' completed successfully (ID: {task_id})")
            
        except Exception as e:
            log.error(f"Task '{task_name}' failed (ID: {task_id}): {e}")
            
            # Mark as failed
            execution.mark_failed(str(e))
            
            # Update the next_run field in ScheduledTask even for failed tasks
            scheduled_task = ScheduledTask.get_task_by_name(task_name)
            if scheduled_task:
                # Get the updated next run time from the scheduler
                job = self.scheduler.get_job(task_name)
                if job:
                    try:
                        if job.next_run_time:
                            scheduled_task.next_run = job.next_run_time
                            log.debug(f"Updated next_run for failed task '{task_name}' to {job.next_run_time}")
                    except AttributeError:
                        # next_run_time may not be available
                        pass
            
            DBSession.commit()
            
            # Send error notification via Telegram
            self._send_task_error_notification(task_name, task_id, str(e), task_args, task_kwargs)
    
    def _send_task_error_notification(self, task_name, task_id, error_message, task_args, task_kwargs):
        """Send error notification via Telegram for failed tasks"""
        try:
            details = {
                'Event': 'Task Execution Failed',
                'Task Name': task_name,
                'Task ID': task_id,
                'Error': error_message,
                'Arguments': task_args,
                'Keyword Arguments': task_kwargs,
                'Environment': config.CONTEXT,
            }
            send_error_notification_telegram(
                title=f"Task Failure: {task_name}",
                details=details
            )
            
            log.info(f"Sent error notification for task '{task_name}'")
            
        except Exception as e:
            log.error(f"Failed to send error notification for task '{task_name}': {e}")
    
    def _job_listener(self, event):
        """Handle job execution events"""
        if event.exception:
            log.error(f"Job {event.job_id} raised an exception: {event.exception}")
        else:
            log.debug(f"Job {event.job_id} executed successfully")
    
    def get_job_status(self, task_name):
        """Get the status of a scheduled job"""
        job = self.scheduler.get_job(task_name)
        if job:
            try:
                next_run = job.next_run_time
            except AttributeError:
                next_run = None
            return {
                'next_run': next_run,
                'active': True
            }
        return {'active': False}


# Global task scheduler instance
task_scheduler = TaskScheduler()


# Task decorator for easy registration and scheduling
def scheduled_task(cron_expression, description=None):
    """Decorator to register and schedule a task function
    
    Args:
        cron_expression (str): Cron expression for scheduling (e.g., '0 4 * * *')
        description (str, optional): Task description
    """
    def decorator(func):
        task_name = func.__name__
        task_scheduler.register_task(task_name, func, cron_expression, description)
        return func
    return decorator


# Database backup task
@scheduled_task('0 4 * * *', 'Create database backup every day at 4:00 AM and clean up old backups')
def database_backup():
    """Create database backup and clean up old backups"""
    try:
        # Create backup using the backup library
        backup_path = create_backup()
        
        # Clean up old backups (older than 1 week)
        deleted_count = cleanup_old_backups(days_to_keep=7)
        
        return f"Backup created: {backup_path}, cleaned up {deleted_count} old backups"
        
    except Exception as e:
        log.error(f"Database backup failed: {e}")
        raise