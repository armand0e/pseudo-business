"""Configuration Manager Module

This module provides configuration management capabilities for the platform.
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path

from src.infrastructure.logging_system import LoggingSystem

_logging_system = LoggingSystem()
logger = _logging_system.get_logger()

@_logging_system.error_handler
class ConfigManager:
    """Configuration manager for loading and managing application settings."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path (str, optional): Path to the configuration file.
        """
        logger.info("Initializing ConfigManager")
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()

    def _find_config_file(self) -> str:
        """Find the configuration file."""
        possible_paths = [
            "config/config.yaml",
            "config.yaml",
            "../config/config.yaml",
            "../../config/config.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found config file at: {path}")
                return path
        
        logger.warning("No config file found, using default configuration")
        return None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path or not os.path.exists(self.config_path):
            logger.info("Using default configuration")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                logger.info(f"Configuration loaded from: {self.config_path}")
                
                # Merge with defaults
                default_config = self._get_default_config()
                merged_config = self._merge_configs(default_config, config)
                
                # Override with environment variables
                return self._apply_env_overrides(merged_config)
                
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            logger.info("Falling back to default configuration")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "agentic_platform",
                "username": "postgres",
                "password": "password"
            },
            "api_gateway": {
                "host": "0.0.0.0",
                "port": 8000,
                "jwt_secret": "default-secret-key",
                "jwt_algorithm": "HS256",
                "jwt_expiry_hours": 24,
                "rate_limiting": {
                    "max_requests_per_minute": 100
                },
                "cors": {
                    "allowed_origins": ["*"]
                },
                "allowed_hosts": ["*"],
                "default_users": {
                    "admin": "admin123",
                    "developer": "dev123"
                }
            },
            "master_orchestrator": {
                "max_concurrent_tasks": 10,
                "task_timeout_seconds": 300,
                "heartbeat_interval": 30
            },
            "agents": {
                "timeouts": {
                    "backend_timeout": 300,
                    "frontend_timeout": 240,
                    "database_timeout": 180,
                    "testing_timeout": 600
                },
                "retry_policies": {
                    "max_retries": 3,
                    "retry_delay": 5
                },
                "concurrency_limits": {
                    "backend": 5,
                    "frontend": 3,
                    "database": 2,
                    "testing": 2
                }
            },
            "evolution_engine": {
                "population_size": 10,
                "mutation_rate": 0.1,
                "crossover_rate": 0.8,
                "max_generations": 100,
                "fitness_threshold": 0.95
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_path": "app.log",
                "max_bytes": 10485760,
                "backup_count": 5
            }
        }

    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge user configuration with default configuration.

        Args:
            default (Dict[str, Any]): Default configuration.
            user (Dict[str, Any]): User configuration.

        Returns:
            Dict[str, Any]: Merged configuration.
        """
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.

        Args:
            config (Dict[str, Any]): Configuration to override.

        Returns:
            Dict[str, Any]: Configuration with environment overrides applied.
        """
        # Database configuration
        if os.getenv('DATABASE_HOST'):
            config['database']['host'] = os.getenv('DATABASE_HOST')
        if os.getenv('DATABASE_PORT'):
            config['database']['port'] = int(os.getenv('DATABASE_PORT'))
        if os.getenv('DATABASE_NAME'):
            config['database']['database'] = os.getenv('DATABASE_NAME')
        if os.getenv('DATABASE_USER'):
            config['database']['username'] = os.getenv('DATABASE_USER')
        if os.getenv('DATABASE_PASSWORD'):
            config['database']['password'] = os.getenv('DATABASE_PASSWORD')
        
        # API Gateway configuration
        if os.getenv('API_HOST'):
            config['api_gateway']['host'] = os.getenv('API_HOST')
        if os.getenv('API_PORT'):
            config['api_gateway']['port'] = int(os.getenv('API_PORT'))
        if os.getenv('JWT_SECRET'):
            config['api_gateway']['jwt_secret'] = os.getenv('JWT_SECRET')
        
        # Logging configuration
        if os.getenv('LOG_LEVEL'):
            config['logging']['level'] = os.getenv('LOG_LEVEL')
        
        logger.debug("Environment variable overrides applied")
        return config

    def get_config(self) -> Dict[str, Any]:
        """
        Get the complete configuration.

        Returns:
            Dict[str, Any]: Complete configuration dictionary.
        """
        return self.config

    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration.

        Returns:
            Dict[str, Any]: Database configuration.
        """
        return self.config.get('database', {})

    def get_api_gateway_config(self) -> Dict[str, Any]:
        """
        Get API gateway configuration.

        Returns:
            Dict[str, Any]: API gateway configuration.
        """
        return self.config.get('api_gateway', {})

    def get_master_orchestrator_config(self) -> Dict[str, Any]:
        """
        Get master orchestrator configuration.

        Returns:
            Dict[str, Any]: Master orchestrator configuration.
        """
        return self.config.get('master_orchestrator', {})

    def get_agents_config(self) -> Dict[str, Any]:
        """
        Get agents configuration.

        Returns:
            Dict[str, Any]: Agents configuration.
        """
        return self.config.get('agents', {})

    def get_evolution_engine_config(self) -> Dict[str, Any]:
        """
        Get evolution engine configuration.

        Returns:
            Dict[str, Any]: Evolution engine configuration.
        """
        return self.config.get('evolution_engine', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.

        Returns:
            Dict[str, Any]: Logging configuration.
        """
        return self.config.get('logging', {})

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key using dot notation.

        Args:
            key (str): Configuration key (e.g., 'database.host').
            default (Any): Default value if key is not found.

        Returns:
            Any: Configuration value.
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by key using dot notation.

        Args:
            key (str): Configuration key (e.g., 'database.host').
            value (Any): Value to set.
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        logger.debug(f"Configuration updated: {key} = {value}")

    def reload(self) -> None:
        """Reload configuration from file."""
        logger.info("Reloading configuration")
        self.config = self._load_config()

    def save(self, path: Optional[str] = None) -> None:
        """
        Save current configuration to file.

        Args:
            path (str, optional): Path to save configuration to.
        """
        save_path = path or self.config_path
        if not save_path:
            save_path = "config/config.yaml"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        try:
            with open(save_path, 'w') as file:
                yaml.dump(self.config, file, default_flow_style=False, indent=2)
            logger.info(f"Configuration saved to: {save_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration to {save_path}: {e}")
            raise