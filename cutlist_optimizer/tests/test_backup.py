import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from cutlist_optimizer.lib.backup import DatabaseBackup, create_backup, cleanup_old_backups, list_backups


class TestDatabaseBackup:
    """Test the DatabaseBackup class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.backup = DatabaseBackup(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_ensure_backup_dir(self):
        """Test that backup directory is created"""
        new_dir = os.path.join(self.temp_dir, 'test_backup')
        backup = DatabaseBackup(new_dir)
        assert os.path.exists(new_dir)
    
    def test_parse_database_uri_valid(self):
        """Test parsing valid database URI"""
        uri = "postgresql://user:pass@localhost:5437/database"
        result = self.backup._parse_database_uri(uri)
        
        expected = {
            'host': 'localhost',
            'port': '5437',
            'user': 'user',
            'password': 'pass',
            'database': 'database'
        }
        assert result == expected
    
    def test_parse_database_uri_invalid_format(self):
        """Test parsing invalid database URI format"""
        uri = "mysql://user:pass@localhost/database"
        with pytest.raises(ValueError, match="Unsupported database URI format"):
            self.backup._parse_database_uri(uri)
    
    def test_parse_database_uri_missing_at(self):
        """Test parsing URI without @ separator"""
        uri = "postgresql://user:passlocalhost/database"
        with pytest.raises(ValueError, match="Invalid database URI format"):
            self.backup._parse_database_uri(uri)
    
    def test_parse_database_uri_missing_slash(self):
        """Test parsing URI without database name"""
        uri = "postgresql://user:pass@localhost"
        with pytest.raises(ValueError, match="Invalid database URI format"):
            self.backup._parse_database_uri(uri)
    
    @patch('subprocess.run')
    def test_create_backup_success(self, mock_run):
        """Test successful backup creation"""
        # Mock successful subprocess run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Mock config
        with patch('cutlist_optimizer.lib.backup.config') as mock_config:
            mock_config.SQLALCHEMY_DATABASE_URI = "postgresql://user:pass@localhost:5437/database"
            
            result = self.backup.create_backup()
            
            assert result.endswith('.sql')
            assert 'cutopt_backup_' in result
            mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_create_backup_failure(self, mock_run):
        """Test backup creation failure"""
        # Mock failed subprocess run
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "pg_dump failed"
        mock_run.return_value = mock_result
        
        # Mock config
        with patch('cutlist_optimizer.lib.backup.config') as mock_config:
            mock_config.SQLALCHEMY_DATABASE_URI = "postgresql://user:pass@localhost:5437/database"
            
            with pytest.raises(Exception, match="pg_dump failed"):
                self.backup.create_backup()
    
    def test_cleanup_old_backups(self):
        """Test cleanup of old backup files"""
        # Create some test backup files
        old_date = datetime.now() - timedelta(days=10)
        new_date = datetime.now() - timedelta(days=2)
        
        # Create old backup file
        old_filename = f"cutopt_backup_{old_date.strftime('%Y%m%d_%H%M%S')}.sql"
        old_path = os.path.join(self.temp_dir, old_filename)
        with open(old_path, 'w') as f:
            f.write("old backup")
        
        # Create new backup file
        new_filename = f"cutopt_backup_{new_date.strftime('%Y%m%d_%H%M%S')}.sql"
        new_path = os.path.join(self.temp_dir, new_filename)
        with open(new_path, 'w') as f:
            f.write("new backup")
        
        # Create non-backup file (should not be deleted)
        other_file = os.path.join(self.temp_dir, "other_file.txt")
        with open(other_file, 'w') as f:
            f.write("other file")
        
        # Run cleanup
        deleted_count = self.backup.cleanup_old_backups(days_to_keep=7)
        
        # Check results
        assert deleted_count == 1
        assert not os.path.exists(old_path)  # Old file should be deleted
        assert os.path.exists(new_path)      # New file should remain
        assert os.path.exists(other_file)    # Other file should remain
    
    def test_list_backups(self):
        """Test listing backup files"""
        # Create some test backup files
        files = [
            "cutopt_backup_20240101_120000.sql",
            "cutopt_backup_20240102_120000.sql",
            "cutopt_backup_20240103_120000.sql"
        ]
        
        for filename in files:
            path = os.path.join(self.temp_dir, filename)
            with open(path, 'w') as f:
                f.write("backup content")
        
        # List backups
        backup_files = self.backup.list_backups()
        
        # Should return all backup files
        assert len(backup_files) == 3
        for file in backup_files:
            assert os.path.basename(file) in files
    
    def test_get_backup_info(self):
        """Test getting backup file information"""
        # Create a test backup file
        filename = "cutopt_backup_20240101_120000.sql"
        path = os.path.join(self.temp_dir, filename)
        with open(path, 'w') as f:
            f.write("backup content")
        
        # Get backup info
        info = self.backup.get_backup_info(path)
        
        # Check info structure
        assert info is not None
        assert info['path'] == path
        assert info['filename'] == filename
        assert info['size_bytes'] > 0
        assert info['size_mb'] >= 0  # Can be 0 for very small files
        assert info['creation_time'] == datetime(2024, 1, 1, 12, 0, 0)
    
    def test_get_backup_info_nonexistent(self):
        """Test getting info for non-existent backup file"""
        info = self.backup.get_backup_info("/nonexistent/path.sql")
        assert info is None


class TestBackupFunctions:
    """Test the convenience functions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('cutlist_optimizer.lib.backup.DatabaseBackup')
    def test_create_backup_function(self, mock_db_backup):
        """Test the create_backup convenience function"""
        mock_instance = MagicMock()
        mock_instance.create_backup.return_value = "/path/to/backup.sql"
        mock_db_backup.return_value = mock_instance
        
        result = create_backup(backup_dir=self.temp_dir)
        
        assert result == "/path/to/backup.sql"
        mock_db_backup.assert_called_once_with(self.temp_dir)
        mock_instance.create_backup.assert_called_once_with(None)
    
    @patch('cutlist_optimizer.lib.backup.DatabaseBackup')
    def test_cleanup_old_backups_function(self, mock_db_backup):
        """Test the cleanup_old_backups convenience function"""
        mock_instance = MagicMock()
        mock_instance.cleanup_old_backups.return_value = 3
        mock_db_backup.return_value = mock_instance
        
        result = cleanup_old_backups(backup_dir=self.temp_dir, days_to_keep=5)
        
        assert result == 3
        mock_db_backup.assert_called_once_with(self.temp_dir)
        mock_instance.cleanup_old_backups.assert_called_once_with(5)
    
    @patch('cutlist_optimizer.lib.backup.DatabaseBackup')
    def test_list_backups_function(self, mock_db_backup):
        """Test the list_backups convenience function"""
        mock_instance = MagicMock()
        mock_instance.list_backups.return_value = ["/backup1.sql", "/backup2.sql"]
        mock_db_backup.return_value = mock_instance
        
        result = list_backups(backup_dir=self.temp_dir)
        
        assert result == ["/backup1.sql", "/backup2.sql"]
        mock_db_backup.assert_called_once_with(self.temp_dir)
        mock_instance.list_backups.assert_called_once() 