import logging
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, desc
from sqlalchemy.ext.declarative import declared_attr

from cutlist_optimizer.lib.database import Base, DBSession

log = logging.getLogger(__name__)


class TaskExecution(Base):
    """Model for storing task execution history"""
    __tablename__ = 'task_executions'
    
    id = Column(Integer, primary_key=True)
    task_name = Column(String(100), nullable=False, index=True)
    task_id = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='pending')  # pending, running, completed, failed
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime)
    execution_time = Column(Integer)  # in seconds
    result = Column(Text)
    error_message = Column(Text)
    task_args = Column(JSON)  # Store task arguments as JSON
    task_kwargs = Column(JSON)  # Store task keyword arguments as JSON
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __init__(self, task_name, task_id, task_args=None, task_kwargs=None):
        self.task_name = task_name
        self.task_id = task_id
        self.task_args = task_args or {}
        self.task_kwargs = task_kwargs or {}
        self.status = 'pending'
        self.started_at = datetime.utcnow()
    
    def mark_running(self):
        """Mark task as running"""
        self.status = 'running'
        self.started_at = datetime.utcnow()
    
    def mark_completed(self, result=None):
        """Mark task as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.result = str(result) if result is not None else None
        self.execution_time = int((self.completed_at - self.started_at).total_seconds())
    
    def mark_failed(self, error_message=None):
        """Mark task as failed"""
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.execution_time = int((self.completed_at - self.started_at).total_seconds())
    
    @classmethod
    def get_recent_executions(cls, limit=50):
        """Get recent task executions"""
        return cls.query.order_by(desc(cls.created_at)).limit(limit).all()
    
    @classmethod
    def get_executions_by_task(cls, task_name, limit=20):
        """Get executions for a specific task"""
        return cls.query.filter_by(task_name=task_name).order_by(desc(cls.created_at)).limit(limit).all()
    
    @classmethod
    def get_failed_executions(cls, limit=20):
        """Get failed task executions"""
        return cls.query.filter_by(status='failed').order_by(desc(cls.completed_at)).limit(limit).all()


class ScheduledTask(Base):
    """Model for storing scheduled task configurations"""
    __tablename__ = 'scheduled_tasks'
    
    id = Column(Integer, primary_key=True)
    task_name = Column(String(100), nullable=False, unique=True)
    task_function = Column(String(100), nullable=False)
    cron_expression = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    task_args = Column(JSON, default={})
    task_kwargs = Column(JSON, default={})
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, task_name, task_function, cron_expression, description=None, 
                 task_args=None, task_kwargs=None):
        self.task_name = task_name
        self.task_function = task_function
        self.cron_expression = cron_expression
        self.description = description
        self.task_args = task_args or {}
        self.task_kwargs = task_kwargs or {}
        self.is_active = True  # Always active since pause/resume is removed
    
    @classmethod
    def get_active_tasks(cls):
        """Get all active scheduled tasks"""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def get_task_by_name(cls, task_name):
        """Get a scheduled task by name"""
        return cls.query.filter_by(task_name=task_name).first()


# Add query properties to models
TaskExecution.query = DBSession.query_property()
ScheduledTask.query = DBSession.query_property()

# Ensure models are imported when the module is loaded
__all__ = ['TaskExecution', 'ScheduledTask'] 