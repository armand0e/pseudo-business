"""Tests for Configuration Manager Module"""

import pytest
import tempfile
import os
import yaml
from unittest.mock import patch, mock_open

from src.infrastructure.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager."""

    def test_config_manager_initialization_no_file(self):
        """Test initialization when no config file exists."""
        with patch('os.path.exists', return_value=False):
            config_manager = ConfigManager()
            
            assert config_manager.config_path is None
            # Should use default configuration
            assert 'database' in config_manager.config
            assert 'api_gateway' in config_manager.config

    def test_config_manager_initialization_with_file(self):
        """Test initialization with existing config file."""
        test_config = {
            'database': {
                'host': 'test-host',
                'port': 3306
            }
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=yaml.dump(test_config))):
                config_manager = ConfigManager('config/test.yaml')
                
                assert config_manager.config_path == 'config/test.yaml'
                assert config_manager.config['database']['host'] == 'test-host'
                assert config_manager.config['database']['port'] == 3306

    def test_find_config_file(self):
        """Test config file discovery."""
        with patch('os.path.exists') as mock_exists:
            # First two paths don't exist, third one does
            mock_exists.side_effect = [False, False, True, False]
            
            config_manager = ConfigManager()
            assert config_manager.config_path == "../config/config.yaml"

    def test_get_default_config(self):
        """Test default configuration."""
        with patch('os.path.exists', return_value=False):
            config_manager = ConfigManager()
            config = config_manager._get_default_config()
            
            # Verify required sections exist
            assert 'database' in config
            assert 'api_gateway' in config
            assert 'master_orchestrator' in config
            assert 'agents' in config
            assert 'evolution_engine' in config
            assert 'logging' in config
            
            # Verify some specific values
            assert config['database']['host'] == 'localhost'
            assert config['database']['port'] == 5432
            assert config['api_gateway']['port'] == 8000

    def test_merge_configs(self):
        """Test configuration merging."""
        config_manager = ConfigManager()
        
        default_config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'username': 'postgres'
            },
            'api_gateway': {
                'port': 8000
            }
        }
        
        user_config = {
            'database': {
                'host': 'remote-host',
                'password': 'secret'
            },
            'new_section': {
                'value': 'test'
            }
        }
        
        merged = config_manager._merge_configs(default_config, user_config)
        
        # Verify merged values
        assert merged['database']['host'] == 'remote-host'  # Overridden
        assert merged['database']['port'] == 5432  # Preserved from default
        assert merged['database']['username'] == 'postgres'  # Preserved from default
        assert merged['database']['password'] == 'secret'  # Added from user
        assert merged['api_gateway']['port'] == 8000  # Preserved from default
        assert merged['new_section']['value'] == 'test'  # Added from user

    def test_apply_env_overrides(self):
        """Test environment variable overrides."""
        config_manager = ConfigManager()
        
        config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test_db',
                'username': 'postgres',
                'password': 'password'
            },
            'api_gateway': {
                'host': '0.0.0.0',
                'port': 8000,
                'jwt_secret': 'default-secret'
            },
            'logging': {
                'level': 'INFO'
            }
        }
        
        env_vars = {
            'DATABASE_HOST': 'remote-host',
            'DATABASE_PORT': '3306',
            'DATABASE_NAME': 'prod_db',
            'DATABASE_USER': 'admin',
            'DATABASE_PASSWORD': 'secure-password',
            'API_HOST': '127.0.0.1',
            'API_PORT': '9000',
            'JWT_SECRET': 'super-secret',
            'LOG_LEVEL': 'DEBUG'
        }
        
        with patch.dict(os.environ, env_vars):
            updated_config = config_manager._apply_env_overrides(config)
            
            assert updated_config['database']['host'] == 'remote-host'
            assert updated_config['database']['port'] == 3306
            assert updated_config['database']['database'] == 'prod_db'
            assert updated_config['database']['username'] == 'admin'
            assert updated_config['database']['password'] == 'secure-password'
            assert updated_config['api_gateway']['host'] == '127.0.0.1'
            assert updated_config['api_gateway']['port'] == 9000
            assert updated_config['api_gateway']['jwt_secret'] == 'super-secret'
            assert updated_config['logging']['level'] == 'DEBUG'

    def test_get_config_methods(self):
        """Test specific config getter methods."""
        with patch('os.path.exists', return_value=False):
            config_manager = ConfigManager()
            
            # Test getter methods
            db_config = config_manager.get_database_config()
            assert 'host' in db_config
            assert 'port' in db_config
            
            api_config = config_manager.get_api_gateway_config()
            assert 'host' in api_config
            assert 'port' in api_config
            
            orchestrator_config = config_manager.get_master_orchestrator_config()
            assert 'max_concurrent_tasks' in orchestrator_config
            
            agents_config = config_manager.get_agents_config()
            assert 'timeouts' in agents_config
            assert 'concurrency_limits' in agents_config
            
            evolution_config = config_manager.get_evolution_engine_config()
            assert 'population_size' in evolution_config
            
            logging_config = config_manager.get_logging_config()
            assert 'level' in logging_config

    def test_get_with_dot_notation(self):
        """Test getting values with dot notation."""
        with patch('os.path.exists', return_value=False):
            config_manager = ConfigManager()
            
            # Test existing keys
            assert config_manager.get('database.host') == 'localhost'
            assert config_manager.get('database.port') == 5432
            assert config_manager.get('api_gateway.port') == 8000
            
            # Test non-existing keys
            assert config_manager.get('nonexistent.key') is None
            assert config_manager.get('nonexistent.key', 'default') == 'default'

    def test_set_with_dot_notation(self):
        """Test setting values with dot notation."""
        with patch('os.path.exists', return_value=False):
            config_manager = ConfigManager()
            
            # Set existing key
            config_manager.set('database.host', 'new-host')
            assert config_manager.get('database.host') == 'new-host'
            
            # Set new nested key
            config_manager.set('new.nested.key', 'value')
            assert config_manager.get('new.nested.key') == 'value'

    def test_reload_config(self):
        """Test configuration reloading."""
        test_config = {
            'database': {
                'host': 'initial-host'
            }
        }
        
        updated_config = {
            'database': {
                'host': 'updated-host'
            }
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=yaml.dump(test_config))):
                config_manager = ConfigManager('config/test.yaml')
                assert config_manager.get('database.host') == 'initial-host'
                
                # Update the mock to return updated config
                with patch('builtins.open', mock_open(read_data=yaml.dump(updated_config))):
                    config_manager.reload()
                    assert config_manager.get('database.host') == 'updated-host'

    def test_save_config(self):
        """Test configuration saving."""
        with patch('os.path.exists', return_value=False):
            config_manager = ConfigManager()
            
            # Test saving with default path
            with patch('os.makedirs') as mock_makedirs:
                with patch('builtins.open', mock_open()) as mock_file:
                    config_manager.save('config/test.yaml')
                    
                    mock_makedirs.assert_called_once()
                    mock_file.assert_called_once_with('config/test.yaml', 'w')

    def test_save_config_error(self):
        """Test configuration saving error handling."""
        with patch('os.path.exists', return_value=False):
            config_manager = ConfigManager()
            
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                with pytest.raises(IOError):
                    config_manager.save('config/test.yaml')

    def test_load_config_error(self):
        """Test error handling during config loading."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="invalid: yaml: content:")):
                # Should fall back to default config on YAML parse error
                config_manager = ConfigManager('config/invalid.yaml')
                
                # Should have default configuration
                assert 'database' in config_manager.config
                assert config_manager.config['database']['host'] == 'localhost'

    def test_empty_config_file(self):
        """Test handling of empty config file."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="")):
                config_manager = ConfigManager('config/empty.yaml')
                
                # Should merge with defaults
                assert 'database' in config_manager.config
                assert config_manager.config['database']['host'] == 'localhost'


if __name__ == "__main__":
    pytest.main([__file__])