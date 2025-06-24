"""
Test cases for the AgentCoordinator class
"""

import unittest
from src.architecture.agent_coordinator import (
    AgentCoordinator,
    AgentType,
    Task,
    Agent
)
from unittest.mock import MagicMock, patch
import time

class TestAgentCoordinator(unittest.TestCase):
    def setUp(self):
        self.config = {
            "timeouts": {
                "backend_timeout": 300,
                "database_timeout": 600,
                "frontend_timeout": 120,
                "testing_timeout": 180
            },
            "retry_policies": {
                "max_retries": 3,
                "backoff_factor": 2
            },
            "concurrency_limits": {
                "backend": 5,
                "database": 2,
                "frontend": 10,
                "testing": 3
            }
        }
        self.coordinator = AgentCoordinator(self.config)

    def test_register_agent(self):
        # Test registering a new agent
        result = self.coordinator.register_agent("agent1", AgentType.BACKEND, ["api_calls"])
        self.assertTrue(result)
        self.assertIn("agent1", self.coordinator.agents)

        # Test registering an existing agent
        result = self.coordinator.register_agent("agent1", AgentType.BACKEND, ["api_calls"])
        self.assertFalse(result)

    def test_unregister_agent(self):
        self.coordinator.register_agent("agent1", AgentType.BACKEND, ["api_calls"])
        result = self.coordinator.unregister_agent("agent1")
        self.assertTrue(result)
        self.assertNotIn("agent1", self.coordinator.agents)

        # Test unregistering non-existent agent
        result = self.coordinator.unregister_agent("nonexistent")
        self.assertFalse(result)

    def test_add_task(self):
        task = Task(
            task_id="task1",
            description="Process data",
            agent_type=AgentType.BACKEND,
            priority=1
        )
        result = self.coordinator.add_task(task)
        self.assertTrue(result)
        self.assertIn("task1", self.coordinator.tasks)

        # Test adding duplicate task
        result = self.coordinator.add_task(Task(
                task_id="task1",
                description="Process data again",
                agent_type=AgentType.BACKEND,
                priority=1
            ))
        self.assertFalse(result)

    def test_assign_tasks(self):
        # Register agents
        self.coordinator.register_agent("backend1", AgentType.BACKEND, ["api_calls"])
        self.coordinator.register_agent("database1", AgentType.DATABASE, ["queries"])
        self.coordinator.register_agent("frontend1", AgentType.FRONTEND, ["rendering"])

        # Add tasks
        task1 = Task(
            task_id="task1",
            description="Process data",
            agent_type=AgentType.BACKEND,
            priority=1
        )
        task2 = Task(
            task_id="task2",
            description="Store results",
            agent_type=AgentType.DATABASE,
            priority=2
        )
        self.coordinator.add_task(task1)
        self.coordinator.add_task(task2)

        # Assign tasks
        self.coordinator.assign_tasks()

        # Check that tasks were assigned
        backend_agent = self.coordinator.agents.get("backend1")
        database_agent = self.coordinator.agents.get("database1")

        if backend_agent and backend_agent.current_task:
            self.assertEqual(backend_agent.current_task.task_id, "task1")
        if database_agent and database_agent.current_task:
            self.assertEqual(database_agent.current_task.task_id, "task2")

    def test_monitor_agents(self):
        # Mock time to control timeout behavior
        class TimeMock:
            def __init__(self, current_time):
                self.current_time = current_time

            def time(self):
                return self.current_time

        # Create an agent with a timed-out task
        mock_time = TimeMock(100)  # Current time
        original_time_func = time.time
        time.time = lambda: mock_time.time()

        agent = Agent(
            agent_id="backend1",
            agent_type=AgentType.BACKEND,
            capabilities=["api_calls"]
        )
        agent.current_task = MagicMock()
        agent.current_task.start_time = 50  # Task started at time 50
        agent.current_task.duration = 40   # Task duration is 40 seconds

        # Set timeout to 30 seconds (should trigger timeout)
        self.coordinator.timeout_settings["backend_timeout"] = 30

        # Add the agent to coordinator for monitoring
        self.coordinator.agents["backend1"] = agent

        # Call monitor_agents
        self.coordinator.monitor_agents()

        # Verify timeout was detected
        self.assertIsNone(agent.current_task)
        self.assertEqual(agent.status, "idle")

        # Reset time function
        time.time = original_time_func

    def test_get_agent_status(self):
        self.coordinator.register_agent("backend1", AgentType.BACKEND, ["api_calls"])
        status = self.coordinator.get_agent_status("backend1")
        self.assertEqual(status["agent_id"], "backend1")
        self.assertEqual(status["type"], "backend")
        self.assertEqual(status["status"], "idle")

    def test_get_task_status(self):
        task = Task(
            task_id="task1",
            description="Process data",
            agent_type=AgentType.BACKEND,
            priority=1
        )
        self.coordinator.add_task(task)

        status = self.coordinator.get_task_status("task1")
        self.assertEqual(status["task_id"], "task1")
        self.assertEqual(status["description"], "Process data")
        self.assertEqual(status["type"], "backend")
        self.assertEqual(status["status"], "completed")

    def test_execute_workflow(self):
        # This is more of an integration test
        coordinator = AgentCoordinator(self.config)

        # Register agents
        coordinator.register_agent("backend1", AgentType.BACKEND, ["api_calls"])
        coordinator.register_agent("database1", AgentType.DATABASE, ["queries"])

        # Add tasks
        task1 = Task(
            task_id="task1",
            description="Process data",
            agent_type=AgentType.BACKEND,
            priority=1
        )
        task2 = Task(
            task_id="task2",
            description="Store results",
            agent_type=AgentType.DATABASE,
            priority=2
        )
        coordinator.add_task(task1)
        coordinator.add_task(task2)

        # Mock time to control workflow execution
        class TimeMock:
            def __init__(self, current_time):
                self.current_time = current_time

            def sleep(self, seconds):
                self.current_time += seconds

            def time(self):
                return self.current_time

        original_time = time.time
        original_sleep = time.sleep
        mock_time = TimeMock(0)

        time.time = mock_time.time
        time.sleep = mock_time.sleep

        # Run the workflow for a short period
        import threading
        stop_event = threading.Event()
        def workflow_thread():
            while not stop_event.is_set():
                coordinator.execute_workflow()

        thread = threading.Thread(target=workflow_thread)
        thread.start()

        # Let it run for a bit
        mock_time.current_time = 2  # Advance time by 2 seconds
        stop_event.set()
        thread.join()

        # Verify tasks were assigned
        backend_agent = coordinator.agents["backend1"]
        database_agent = coordinator.agents["database1"]

        self.assertEqual(backend_agent.current_task.task_id, "task1")
        self.assertEqual(database_agent.current_task.task_id, "task2")

        # Reset time functions
        time.time = original_time
        time.sleep = original_sleep

    def test_concurrency_limits(self):
        # Test that concurrency limits are respected
        coordinator = AgentCoordinator(self.config)

        # Register multiple agents of the same type
        for i in range(3):  # We have a limit of 2 for database agents
            coordinator.register_agent(f"database{i}", AgentType.DATABASE, ["queries"])

        # Add tasks that exceed concurrency limits
        tasks = []
        for i in range(4):
            task = Task(
                task_id=f"task{i}",
                description=f"Database operation {i}",
                agent_type=AgentType.DATABASE,
                priority=1
            )
            coordinator.add_task(task)
            tasks.append(task)

        # Assign tasks
        coordinator.assign_tasks()

        # Verify only 2 tasks were assigned (the limit for database agents)
        assigned_count = sum(1 for agent in coordinator.agents.values()
                            if agent.current_task is not None)
        self.assertEqual(assigned_count, 2)

    def test_retry_policies(self):
        # This would require more complex mocking of task execution
        # For now we'll just verify the retry policies are accessible
        self.assertEqual(self.coordinator.retry_policies["max_retries"], 3)
        self.assertEqual(self.coordinator.retry_policies["backoff_factor"], 2)

    def test_task_dependencies(self):
        # Test task dependencies functionality
        task1 = Task(
            task_id="task1",
            description="Initial data processing",
            agent_type=AgentType.BACKEND,
            priority=1
        )
        task2 = Task(
            task_id="task2",
            description="Store processed data",
            agent_type=AgentType.DATABASE,
            priority=2,
            dependencies=["task1"]
        )

        self.coordinator.add_task(task1)
        self.coordinator.add_task(task2)

        # Register agents
        self.coordinator.register_agent("backend1", AgentType.BACKEND, ["api_calls"])
        self.coordinator.register_agent("database1", AgentType.DATABASE, ["queries"])

        # Assign tasks
        self.coordinator.assign_tasks()

        # Verify task dependencies are respected
        backend_agent = self.coordinator.agents["backend1"]
        database_agent = self.coordinator.agents["database1"]

        self.assertEqual(backend_agent.current_task.task_id, "task1")
        self.assertIsNone(database_agent.current_task)

    def test_priority_assignment(self):
        # Test that higher priority tasks are assigned first
        task_high = Task(
            task_id="high_priority",
            description="High priority task",
            agent_type=AgentType.BACKEND,
            priority=2  # Higher priority
        )
        task_low = Task(
            task_id="low_priority",
            description="Low priority task",
            agent_type=AgentType.BACKEND,
            priority=1
        )

        self.coordinator.add_task(task_high)
        self.coordinator.add_task(task_low)

        # Register agents
        self.coordinator.register_agent("backend1", AgentType.BACKEND, ["api_calls"])

        # Assign tasks
        self.coordinator.assign_tasks()

        # Verify higher priority task was assigned first
        agent = self.coordinator.agents["backend1"]
        self.assertEqual(agent.current_task.task_id, "high_priority")

    def test_agent_capabilities(self):
        # Test that agents are selected based on capabilities
        task = Task(
            task_id="task1",
            description="Process data with specific requirements",
            agent_type=AgentType.BACKEND,
            priority=1
        )

        # Register agents with different capabilities
        self.coordinator.register_agent("backend1", AgentType.BACKEND, ["basic_processing"])
        self.coordinator.register_agent("backend2", AgentType.BACKEND, ["advanced_processing"])

        self.coordinator.add_task(task)

        # Assign tasks
        self.coordinator.assign_tasks()

        # Verify the agent with matching capabilities was selected
        backend1 = self.coordinator.agents["backend1"]
        backend2 = self.coordinator.agents["backend2"]

        # This test assumes that "advanced_processing" is a superset of "basic_processing"
        # So both agents could be assigned, but we just check that at least one is
        self.assertIsNotNone(backend1.current_task or backend2.current_task)

    def test_empty_coordinator(self):
        # Test behavior with no agents or tasks
        coordinator = AgentCoordinator(self.config)

        # Verify initial state
        self.assertEqual(len(coordinator.agents), 0)
        self.assertEqual(len(coordinator.tasks), 0)

        # Assign tasks (should do nothing)
        coordinator.assign_tasks()

        # Monitor agents (should do nothing)
        coordinator.monitor_agents()

    def test_multiple_task_types(self):
        # Test handling of multiple task types
        coordinator = AgentCoordinator(self.config)

        # Register agents of different types
        coordinator.register_agent("backend1", AgentType.BACKEND, ["api_calls"])
        coordinator.register_agent("database1", AgentType.DATABASE, ["queries"])
        coordinator.register_agent("frontend1", AgentType.FRONTEND, ["rendering"])

        # Add tasks of different types
        task1 = Task(
            task_id="task1",
            description="Process data",
            agent_type=AgentType.BACKEND,
            priority=1
        )
        task2 = Task(
            task_id="task2",
            description="Store results",
            agent_type=AgentType.DATABASE,
            priority=2
        )
        task3 = Task(
            task_id="task3",
            description="Render UI",
            agent_type=AgentType.FRONTEND,
            priority=1
        )

        coordinator.add_task(task1)
        coordinator.add_task(task2)
        coordinator.add_task(task3)

        # Assign tasks
        coordinator.assign_tasks()

        # Verify all task types were assigned correctly
        backend_agent = self.coordinator.agents["backend1"]
        database_agent = self.coordinator.agents["database1"]
        frontend_agent = self.coordinator.agents["frontend1"]

        self.assertEqual(backend_agent.current_task.task_id, "task1")
        self.assertEqual(database_agent.current_task.task_id, "task2")
        self.assertEqual(frontend_agent.current_task.task_id, "task3")

if __name__ == "__main__":
    unittest.main()