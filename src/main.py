"""Main Application Module

This module provides the main entry point for the Agentic AI Development Platform.
"""

import asyncio
import signal
import sys
from typing import Dict, Any
import uvicorn

from src.infrastructure.config_manager import ConfigManager
from src.infrastructure.logging_system import LoggingSystem
from src.infrastructure.api_gateway import APIGateway
from src.agents.database_agent import DatabaseAgent
from src.agents.backend_agent import BackendAgent
from src.architecture.agent_coordinator import AgentCoordinator, AgentType
from src.architecture.nlp_processor import NLPProcessor
from src.architecture.task_decomposer import TaskDecomposer

_logging_system = LoggingSystem()
logger = _logging_system.get_logger()

@_logging_system.error_handler
class AgendicPlatform:
    """Main application class for the Agentic AI Development Platform."""

    def __init__(self):
        """Initialize the platform."""
        logger.info("Initializing Agentic AI Development Platform")
        
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        
        # Initialize core components
        self.database_agent = None
        self.api_gateway = None
        self.agent_coordinator = None
        self.nlp_processor = None
        self.task_decomposer = None
        self.backend_agent = None
        
        # Platform state
        self.running = False

    async def initialize(self):
        """Initialize all platform components."""
        logger.info("Initializing platform components")
        
        try:
            # Initialize database agent
            logger.info("Initializing Database Agent")
            self.database_agent = DatabaseAgent(self.config)
            
            # Initialize NLP processor
            logger.info("Initializing NLP Processor")
            self.nlp_processor = NLPProcessor(self.config)
            
            # Initialize task decomposer
            logger.info("Initializing Task Decomposer")
            self.task_decomposer = TaskDecomposer(self.config)
            
            # Initialize agent coordinator
            logger.info("Initializing Agent Coordinator")
            agents_config = self.config_manager.get_agents_config()
            self.agent_coordinator = AgentCoordinator(agents_config)
            
            # Initialize backend agent
            logger.info("Initializing Backend Agent")
            self.backend_agent = BackendAgent(self.config)
            
            # Register agents with coordinator
            self.agent_coordinator.register_agent(
                agent_id="backend_agent_001",
                agent_type=AgentType.BACKEND,
                capabilities=self.backend_agent.get_capabilities()
            )
            
            # Initialize API Gateway
            logger.info("Initializing API Gateway")
            api_config = self.config_manager.get_api_gateway_config()
            self.api_gateway = APIGateway(api_config)
            
            # Set API Gateway dependencies
            self.api_gateway.set_dependencies(
                database_agent=self.database_agent,
                master_orchestrator=self.agent_coordinator
            )
            
            logger.info("Platform initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize platform: {e}")
            raise

    async def start(self):
        """Start the platform."""
        logger.info("Starting Agentic AI Development Platform")
        
        try:
            await self.initialize()
            
            # Start API Gateway
            api_config = self.config_manager.get_api_gateway_config()
            host = api_config.get('host', '0.0.0.0')
            port = api_config.get('port', 8000)
            
            logger.info(f"Starting API Gateway on {host}:{port}")
            
            # Configure uvicorn
            config = uvicorn.Config(
                app=self.api_gateway.get_app(),
                host=host,
                port=port,
                log_level="info",
                access_log=True
            )
            
            server = uvicorn.Server(config)
            
            # Set up signal handlers
            def signal_handler(signum, frame):
                logger.info(f"Received signal {signum}, shutting down...")
                asyncio.create_task(self.stop())
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            self.running = True
            logger.info("Platform started successfully")
            
            # Start the server
            await server.serve()
            
        except Exception as e:
            logger.error(f"Failed to start platform: {e}")
            await self.stop()
            raise

    async def stop(self):
        """Stop the platform."""
        logger.info("Stopping Agentic AI Development Platform")
        
        try:
            self.running = False
            
            # Perform cleanup
            if self.api_gateway:
                await self.api_gateway.shutdown()
            
            if self.database_agent:
                self.database_agent.close()
            
            logger.info("Platform stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during platform shutdown: {e}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get platform status.

        Returns:
            Dict[str, Any]: Platform status information.
        """
        return {
            "running": self.running,
            "components": {
                "database_agent": self.database_agent is not None,
                "api_gateway": self.api_gateway is not None,
                "agent_coordinator": self.agent_coordinator is not None,
                "nlp_processor": self.nlp_processor is not None,
                "task_decomposer": self.task_decomposer is not None,
                "backend_agent": self.backend_agent is not None
            },
            "health": {
                "database": self.database_agent.health_check() if self.database_agent else False
            }
        }

async def run_platform():
    """Run the platform."""
    platform = AgendicPlatform()
    
    try:
        await platform.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Platform error: {e}")
        sys.exit(1)
    finally:
        await platform.stop()

def main():
    """Main entry point."""
    logger.info("Starting Agentic AI Development Platform")
    
    try:
        # Run the platform
        asyncio.run(run_platform())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()