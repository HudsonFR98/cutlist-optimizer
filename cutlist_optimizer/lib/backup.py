import logging
import os
import glob
import subprocess
from datetime import datetime, timedelta
from cutlist_optimizer.lib import config

log = logging.getLogger(__name__)


class DatabaseBackup:
    """Database backup utility class"""
    
    def __init__(self, backup_dir='/var/backup'):
        self.backup_dir = backup_dir
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self):
        """Ensure backup directory exists"""
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _parse_database_uri(self, db_uri):
        """Parse database URI to extract connection details
        
        Args:
            db_uri (str): Database URI in format postgresql://user:password@host:port/database
            
        Returns:
            dict: Dictionary with host, port, user, password, database
        """
        if not db_uri.startswith('postgresql://'):
            raise ValueError("Unsupported database URI format - only PostgreSQL supported")
        
        # Remove postgresql:// prefix
        uri_part = db_uri[12:]
        
        # Split by @ to separate credentials from host
        if '@' not in uri_part:
            raise ValueError("Invalid database URI format")
        
        credentials, host_part = uri_part.split('@', 1)
        user, password = credentials.split(':', 1)
        
        # Remove any leading slashes from user
        if user.startswith('/'):
            user = user[1:]
        
        # Split host_part by / to separate host:port from database
        if '/' not in host_part:
            raise ValueError("Invalid database URI format")
        
        host_port, database = host_part.split('/', 1)
        
        if ':' in host_port:
            host, port = host_port.split(':', 1)
        else:
            # Default to the internal PostgreSQL port used inside Docker networks
            host, port = host_port, '5432'
        
        return {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database
        }
    
    def create_backup(self, db_uri=None):
        """Create a database backup
        
        Args:
            db_uri (str, optional): Database URI. If not provided, uses config.SQLALCHEMY_DATABASE_URI
            
        Returns:
            str: Path to the created backup file
            
        Raises:
            Exception: If backup creation fails
        """
        try:
            # Use provided URI or get from config
            if db_uri is None:
                db_uri = config.SQLALCHEMY_DATABASE_URI
            
            # Parse database connection details
            db_config = self._parse_database_uri(db_uri)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'cutopt_backup_{timestamp}.sql'
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Create backup using pg_dump
            cmd = [
                'pg_dump',
                '-h', db_config['host'],
                '-p', db_config['port'],
                '-U', db_config['user'],
                '-d', db_config['database'],
                '-f', backup_path
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['password']
            
            log.info(f"Creating database backup: {backup_path}")
            log.info(f"Command: pg_dump -h {db_config['host']} -p {db_config['port']} -U {db_config['user']} -d {db_config['database']}")
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                log.info(f"Database backup created successfully: {backup_path}")
                return backup_path
            else:
                log.error(f"pg_dump stdout: {result.stdout}")
                log.error(f"pg_dump stderr: {result.stderr}")
                raise Exception(f"pg_dump failed: {result.stderr}")
                
        except Exception as e:
            log.error(f"Database backup failed: {e}")
            raise
    
    def cleanup_old_backups(self, days_to_keep=7):
        """Clean up backup files older than specified days
        
        Args:
            days_to_keep (int): Number of days to keep backups (default: 7)
            
        Returns:
            int: Number of files deleted
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Find all backup files
            backup_pattern = os.path.join(self.backup_dir, 'cutopt_backup_*.sql')
            backup_files = glob.glob(backup_pattern)
            
            deleted_count = 0
            for backup_file in backup_files:
                try:
                    # Extract timestamp from filename (format: cutopt_backup_YYYYMMDD_HHMMSS.sql)
                    filename = os.path.basename(backup_file)
                    if filename.startswith('cutopt_backup_') and filename.endswith('.sql'):
                        # Remove 'cutopt_backup_' prefix and '.sql' suffix
                        # 'cutopt_backup_' is 12 characters long
                        timestamp_str = filename[len('cutopt_backup_'):-4]
                        file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        
                        if file_date < cutoff_date:
                            os.remove(backup_file)
                            deleted_count += 1
                            log.info(f"Deleted old backup: {backup_file}")
                            
                except (ValueError, OSError) as e:
                    log.warning(f"Could not process backup file {backup_file}: {e}")
            
            if deleted_count > 0:
                log.info(f"Cleaned up {deleted_count} old backup files")
            
            return deleted_count
            
        except Exception as e:
            log.error(f"Failed to cleanup old backups: {e}")
            raise
    
    def list_backups(self):
        """List all available backups
        
        Returns:
            list: List of backup file paths sorted by creation time (newest first)
        """
        try:
            backup_pattern = os.path.join(self.backup_dir, 'cutopt_backup_*.sql')
            backup_files = glob.glob(backup_pattern)
            
            # Sort by creation time (newest first)
            backup_files.sort(key=lambda x: os.path.getctime(x), reverse=True)
            
            return backup_files
            
        except Exception as e:
            log.error(f"Failed to list backups: {e}")
            return []
    
    def get_backup_info(self, backup_path):
        """Get information about a backup file
        
        Args:
            backup_path (str): Path to backup file
            
        Returns:
            dict: Dictionary with backup information (size, creation_time, etc.)
        """
        try:
            if not os.path.exists(backup_path):
                return None
            
            stat = os.stat(backup_path)
            filename = os.path.basename(backup_path)
            
            # Extract timestamp from filename
            creation_time = None
            if filename.startswith('cutopt_backup_') and filename.endswith('.sql'):
                # 'cutopt_backup_' is 12 characters long
                timestamp_str = filename[len('cutopt_backup_'):-4]
                try:
                    creation_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                except ValueError:
                    pass
            
            return {
                'path': backup_path,
                'filename': filename,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'creation_time': creation_time,
                'modified_time': datetime.fromtimestamp(stat.st_mtime)
            }
            
        except Exception as e:
            log.error(f"Failed to get backup info for {backup_path}: {e}")
            return None


# Convenience functions for easy use
def create_backup(backup_dir='/var/backup', db_uri=None):
    """Create a database backup
    
    Args:
        backup_dir (str): Directory to store backups
        db_uri (str, optional): Database URI
        
    Returns:
        str: Path to the created backup file
    """
    backup = DatabaseBackup(backup_dir)
    return backup.create_backup(db_uri)


def cleanup_old_backups(backup_dir='/var/backup', days_to_keep=7):
    """Clean up old backup files
    
    Args:
        backup_dir (str): Directory containing backups
        days_to_keep (int): Number of days to keep backups
        
    Returns:
        int: Number of files deleted
    """
    backup = DatabaseBackup(backup_dir)
    return backup.cleanup_old_backups(days_to_keep)


def list_backups(backup_dir='/var/backup'):
    """List all available backups
    
    Args:
        backup_dir (str): Directory containing backups
        
    Returns:
        list: List of backup file paths
    """
    backup = DatabaseBackup(backup_dir)
    return backup.list_backups() 