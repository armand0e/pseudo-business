"""Configuration management for the CLI tool."""

import os
import yaml
from typing import Dict, Any

CONFIG_DIR = os.path.expanduser("~/.agentic-cli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")

def ensure_config_dir():
    """Ensure the config directory exists."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def load_config() -> Dict[str, Any]:
    """Load configuration from the config file."""
    ensure_config_dir()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_config(config: Dict[str, Any]):
    """Save configuration to the config file."""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f)

# Default configuration
DEFAULT_CONFIG = {
    'api_url': 'http://localhost:8000',
    'batch_size': 10,
    'output_format': 'text'
}

def get_config() -> Dict[str, Any]:
    """Get the current configuration, merging defaults with user config."""
    config = DEFAULT_CONFIG.copy()
    config.update(load_config())
    return config