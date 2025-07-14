"""Main CLI implementation using Click."""

import click
import yaml
import sys
from typing import Optional
from rich.console import Console
from rich.table import Table
from .auth import login, is_authenticated, delete_token
from .api import APIClient
from .config import get_config, save_config

console = Console()
api_client = APIClient()

def require_auth(f):
    """Decorator to require authentication before running a command."""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            console.print("[red]Please login first using 'agentic-cli login'[/red]")
            sys.exit(1)
        return f(*args, **kwargs)
    return wrapper

@click.group()
def cli():
    """Agentic AI Development Platform CLI."""
    pass

@cli.command()
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
def login_cmd(username: str, password: str):
    """Log in to the Agentic AI Development Platform."""
    if login(username, password):
        console.print("[green]Successfully logged in[/green]")
    else:
        console.print("[red]Login failed[/red]")
        sys.exit(1)

@cli.command()
def logout():
    """Log out from the Agentic AI Development Platform."""
    delete_token()
    console.print("[green]Successfully logged out[/green]")

@cli.command()
@require_auth
@click.argument('name')
@click.option('--config', '-c', type=click.Path(exists=True), help='Project configuration file')
def init(name: str, config: Optional[str]):
    """Initialize a new project."""
    try:
        config_data = {}
        if config:
            with open(config, 'r') as f:
                config_data = yaml.safe_load(f)
        
        result = api_client.init_project(name, config_data)
        console.print(f"[green]Successfully initialized project {name}[/green]")
        console.print(f"Project ID: {result['id']}")
    except Exception as e:
        console.print(f"[red]Failed to initialize project: {str(e)}[/red]")
        sys.exit(1)

@cli.command()
@require_auth
@click.argument('project_id')
@click.option('--requirements', '-r', type=click.Path(exists=True), required=True,
              help='Requirements file (YAML format)')
def submit(project_id: str, requirements: str):
    """Submit requirements for a project."""
    try:
        with open(requirements, 'r') as f:
            req_data = yaml.safe_load(f)
        
        result = api_client.submit_requirements(project_id, req_data)
        console.print("[green]Successfully submitted requirements[/green]")
        console.print(f"Task ID: {result['task_id']}")
    except Exception as e:
        console.print(f"[red]Failed to submit requirements: {str(e)}[/red]")
        sys.exit(1)

@cli.command()
@require_auth
@click.option('--batch-config', '-b', type=click.Path(exists=True), required=True,
              help='Batch configuration file (YAML format)')
def batch(batch_config: str):
    """Submit a batch processing request."""
    try:
        with open(batch_config, 'r') as f:
            config_data = yaml.safe_load(f)
        
        result = api_client.batch_process(config_data)
        console.print("[green]Successfully submitted batch processing request[/green]")
        console.print(f"Batch ID: {result['batch_id']}")
    except Exception as e:
        console.print(f"[red]Failed to submit batch request: {str(e)}[/red]")
        sys.exit(1)

@cli.command()
@require_auth
@click.argument('project_id')
def status(project_id: str):
    """Get the status of a project."""
    try:
        result = api_client.get_project_status(project_id)
        
        table = Table(title=f"Project Status: {project_id}")
        table.add_column("Attribute", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in result.items():
            table.add_row(key, str(value))
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]Failed to get project status: {str(e)}[/red]")
        sys.exit(1)

@cli.command()
@require_auth
def list_projects():
    """List all projects."""
    try:
        result = api_client.list_projects()
        
        table = Table(title="Projects")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        
        for project in result['projects']:
            table.add_row(
                project['id'],
                project['name'],
                project['status']
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]Failed to list projects: {str(e)}[/red]")
        sys.exit(1)

@cli.command()
@click.option('--api-url', help='API Gateway URL')
@click.option('--batch-size', type=int, help='Default batch size')
@click.option('--output-format', type=click.Choice(['text', 'json']), help='Output format')
def configure(api_url: Optional[str], batch_size: Optional[int], output_format: Optional[str]):
    """Configure CLI settings."""
    config = get_config()
    
    if api_url:
        config['api_url'] = api_url
    if batch_size:
        config['batch_size'] = batch_size
    if output_format:
        config['output_format'] = output_format
    
    save_config(config)
    console.print("[green]Configuration updated successfully[/green]")

if __name__ == '__main__':
    cli()