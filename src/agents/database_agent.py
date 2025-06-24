"""Database Agent Module

This module provides the DatabaseAgent class for managing database operations,
schema generation, and ORM model creation.
"""

from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from dataclasses import dataclass
import time
from datetime import datetime

from src.infrastructure.logging_system import LoggingSystem

_logging_system = LoggingSystem()
logger = _logging_system.get_logger()

Base = declarative_base()

@dataclass
class DatabaseSchema:
    """Data class for database schema information."""
    table_name: str
    columns: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]] = None
    indexes: List[str] = None

@dataclass
class QueryResult:
    """Data class for query results."""
    success: bool
    data: Any = None
    error: str = None
    execution_time: float = 0.0

class ProjectModel(Base):
    """SQLAlchemy model for projects."""
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TaskModel(Base):
    """SQLAlchemy model for tasks."""
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(255), unique=True, nullable=False)
    project_id = Column(Integer, nullable=False)
    description = Column(Text)
    agent_type = Column(String(50))
    priority = Column(Integer, default=1)
    status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class AgentModel(Base):
    """SQLAlchemy model for agents."""
    __tablename__ = 'agents'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(String(255), unique=True, nullable=False)
    agent_type = Column(String(50))
    status = Column(String(50), default='idle')
    capabilities = Column(Text)  # JSON string
    current_task_id = Column(String(255))
    last_active = Column(DateTime, default=datetime.utcnow)

@_logging_system.error_handler
class DatabaseAgent:
    """Database Agent for managing database operations and schema generation."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the DatabaseAgent with configuration.

        Args:
            config (Dict[str, Any]): Configuration containing database connection details.
        """
        logger.info("Initializing DatabaseAgent")
        self.config = config
        self.engine = None
        self.session_factory = None
        self.metadata = MetaData()
        
        # Database connection configuration
        self.db_config = config.get('database', {})
        self.connection_string = self._build_connection_string()
        
        # Initialize database connection
        self._initialize_database()

    def _build_connection_string(self) -> str:
        """Build database connection string from configuration."""
        host = self.db_config.get('host', 'localhost')
        port = self.db_config.get('port', 5432)
        database = self.db_config.get('database', 'agentic_platform')
        username = self.db_config.get('username', 'postgres')
        password = self.db_config.get('password', 'password')
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"

    def _initialize_database(self) -> None:
        """Initialize database connection and create tables."""
        try:
            logger.info(f"Connecting to database: {self.connection_string.split('@')[1]}")
            self.engine = create_engine(self.connection_string, echo=False)
            self.session_factory = sessionmaker(bind=self.engine)
            
            # Create all tables
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.session_factory()

    def create_project(self, name: str, description: str = None) -> QueryResult:
        """
        Create a new project in the database.

        Args:
            name (str): Project name.
            description (str, optional): Project description.

        Returns:
            QueryResult: Result of the operation.
        """
        start_time = time.time()
        session = self.get_session()
        
        try:
            logger.info(f"Creating project: {name}")
            project = ProjectModel(name=name, description=description)
            session.add(project)
            session.commit()
            
            execution_time = time.time() - start_time
            logger.info(f"Project {name} created successfully in {execution_time:.3f}s")
            
            return QueryResult(
                success=True,
                data={'id': project.id, 'name': project.name},
                execution_time=execution_time
            )
            
        except SQLAlchemyError as e:
            session.rollback()
            execution_time = time.time() - start_time
            logger.error(f"Failed to create project {name}: {e}")
            
            return QueryResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
        finally:
            session.close()

    def create_task(self, task_id: str, project_id: int, description: str, 
                   agent_type: str, priority: int = 1) -> QueryResult:
        """
        Create a new task in the database.

        Args:
            task_id (str): Unique task identifier.
            project_id (int): Associated project ID.
            description (str): Task description.
            agent_type (str): Type of agent needed for this task.
            priority (int): Task priority.

        Returns:
            QueryResult: Result of the operation.
        """
        start_time = time.time()
        session = self.get_session()
        
        try:
            logger.info(f"Creating task: {task_id}")
            task = TaskModel(
                task_id=task_id,
                project_id=project_id,
                description=description,
                agent_type=agent_type,
                priority=priority
            )
            session.add(task)
            session.commit()
            
            execution_time = time.time() - start_time
            logger.info(f"Task {task_id} created successfully in {execution_time:.3f}s")
            
            return QueryResult(
                success=True,
                data={'id': task.id, 'task_id': task.task_id},
                execution_time=execution_time
            )
            
        except SQLAlchemyError as e:
            session.rollback()
            execution_time = time.time() - start_time
            logger.error(f"Failed to create task {task_id}: {e}")
            
            return QueryResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
        finally:
            session.close()

    def register_agent(self, agent_id: str, agent_type: str, capabilities: List[str]) -> QueryResult:
        """
        Register an agent in the database.

        Args:
            agent_id (str): Unique agent identifier.
            agent_type (str): Type of agent.
            capabilities (List[str]): Agent capabilities.

        Returns:
            QueryResult: Result of the operation.
        """
        start_time = time.time()
        session = self.get_session()
        
        try:
            logger.info(f"Registering agent: {agent_id}")
            import json
            agent = AgentModel(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=json.dumps(capabilities)
            )
            session.add(agent)
            session.commit()
            
            execution_time = time.time() - start_time
            logger.info(f"Agent {agent_id} registered successfully in {execution_time:.3f}s")
            
            return QueryResult(
                success=True,
                data={'id': agent.id, 'agent_id': agent.agent_id},
                execution_time=execution_time
            )
            
        except SQLAlchemyError as e:
            session.rollback()
            execution_time = time.time() - start_time
            logger.error(f"Failed to register agent {agent_id}: {e}")
            
            return QueryResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
        finally:
            session.close()

    def update_agent_status(self, agent_id: str, status: str, current_task_id: str = None) -> QueryResult:
        """
        Update agent status in the database.

        Args:
            agent_id (str): Agent identifier.
            status (str): New agent status.
            current_task_id (str, optional): Current task ID.

        Returns:
            QueryResult: Result of the operation.
        """
        start_time = time.time()
        session = self.get_session()
        
        try:
            logger.debug(f"Updating agent {agent_id} status to {status}")
            agent = session.query(AgentModel).filter_by(agent_id=agent_id).first()
            
            if not agent:
                execution_time = time.time() - start_time
                logger.warning(f"Agent {agent_id} not found for status update")
                return QueryResult(
                    success=False,
                    error=f"Agent {agent_id} not found",
                    execution_time=execution_time
                )
            
            agent.status = status
            agent.current_task_id = current_task_id
            agent.last_active = datetime.utcnow()
            session.commit()
            
            execution_time = time.time() - start_time
            logger.debug(f"Agent {agent_id} status updated in {execution_time:.3f}s")
            
            return QueryResult(
                success=True,
                data={'agent_id': agent_id, 'status': status},
                execution_time=execution_time
            )
            
        except SQLAlchemyError as e:
            session.rollback()
            execution_time = time.time() - start_time
            logger.error(f"Failed to update agent {agent_id} status: {e}")
            
            return QueryResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
        finally:
            session.close()

    def get_pending_tasks(self, agent_type: str = None) -> QueryResult:
        """
        Get pending tasks from the database.

        Args:
            agent_type (str, optional): Filter by agent type.

        Returns:
            QueryResult: Result containing pending tasks.
        """
        start_time = time.time()
        session = self.get_session()
        
        try:
            logger.debug(f"Fetching pending tasks for agent type: {agent_type}")
            query = session.query(TaskModel).filter_by(status='pending')
            
            if agent_type:
                query = query.filter_by(agent_type=agent_type)
                
            tasks = query.order_by(TaskModel.priority.desc(), TaskModel.created_at).all()
            
            execution_time = time.time() - start_time
            task_data = [
                {
                    'task_id': task.task_id,
                    'project_id': task.project_id,
                    'description': task.description,
                    'agent_type': task.agent_type,
                    'priority': task.priority,
                    'created_at': task.created_at.isoformat() if task.created_at else None
                }
                for task in tasks
            ]
            
            logger.debug(f"Found {len(task_data)} pending tasks in {execution_time:.3f}s")
            
            return QueryResult(
                success=True,
                data=task_data,
                execution_time=execution_time
            )
            
        except SQLAlchemyError as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed to get pending tasks: {e}")
            
            return QueryResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
        finally:
            session.close()

    def generate_schema(self, table_name: str, columns: List[Dict[str, Any]]) -> DatabaseSchema:
        """
        Generate database schema for a given table specification.

        Args:
            table_name (str): Name of the table.
            columns (List[Dict[str, Any]]): Column specifications.

        Returns:
            DatabaseSchema: Generated schema object.
        """
        logger.info(f"Generating schema for table: {table_name}")
        
        # Validate and process column specifications
        processed_columns = []
        for col in columns:
            if 'name' not in col or 'type' not in col:
                logger.warning(f"Invalid column specification: {col}")
                continue
                
            processed_columns.append({
                'name': col['name'],
                'type': col['type'],
                'nullable': col.get('nullable', True),
                'primary_key': col.get('primary_key', False),
                'unique': col.get('unique', False),
                'default': col.get('default')
            })
        
        schema = DatabaseSchema(
            table_name=table_name,
            columns=processed_columns,
            relationships=columns[0].get('relationships', []) if columns else [],
            indexes=columns[0].get('indexes', []) if columns else []
        )
        
        logger.info(f"Schema generated for {table_name} with {len(processed_columns)} columns")
        return schema

    def execute_query(self, query: str, params: Dict[str, Any] = None) -> QueryResult:
        """
        Execute a raw SQL query.

        Args:
            query (str): SQL query to execute.
            params (Dict[str, Any], optional): Query parameters.

        Returns:
            QueryResult: Result of the query execution.
        """
        start_time = time.time()
        session = self.get_session()
        
        try:
            logger.debug(f"Executing query: {query[:100]}...")
            result = session.execute(query, params or {})
            session.commit()
            
            execution_time = time.time() - start_time
            
            # Try to fetch results if it's a SELECT query
            data = None
            if query.strip().upper().startswith('SELECT'):
                data = [dict(row) for row in result.fetchall()]
            
            logger.debug(f"Query executed successfully in {execution_time:.3f}s")
            
            return QueryResult(
                success=True,
                data=data,
                execution_time=execution_time
            )
            
        except SQLAlchemyError as e:
            session.rollback()
            execution_time = time.time() - start_time
            logger.error(f"Query execution failed: {e}")
            
            return QueryResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
        finally:
            session.close()

    def health_check(self) -> bool:
        """
        Perform a health check on the database connection.

        Returns:
            bool: True if database is healthy, False otherwise.
        """
        try:
            session = self.get_session()
            session.execute("SELECT 1")
            session.close()
            logger.debug("Database health check passed")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def close(self) -> None:
        """Close database connections."""
        if self.engine:
            logger.info("Closing database connections")
            self.engine.dispose()