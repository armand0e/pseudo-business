"""Unit tests for the TaskDecomposer class."""

import unittest
from unittest.mock import MagicMock
from src.architecture.task_decomposer import TaskDecomposer

class TestTaskDecomposer(unittest.TestCase):
    def setUp(self):
        self.nlp_processor = MagicMock()
        self.decomposer = TaskDecomposer(self.nlp_processor)

        # Mock NLP processor responses
        self.nlp_processor.analyze_text.return_value = {
            'entities': [],
            'complexity': 0.8,
            'keywords': []
        }
        self.nlp_processor.is_valid_task.return_value = True

    def test_analyze_task(self):
        """Test task analysis."""
        result = self.decomposer.analyze_task("Implement a new feature")
        self.assertEqual(result['description'], "Implement a new feature")
        self.assertAlmostEqual(result['complexity'], 0.8)
        self.assertEqual(result['priority'], 2)

    def test_decompose_task(self):
        """Test task decomposition."""
        analyzed_task = {
            'description': "Implement a new feature",
            'entities': [],
            'keywords': [],
            'complexity': 0.8
        }
        subtasks = self.decomposer.decompose_task(analyzed_task)
        self.assertEqual(len(subtasks), 3)
        self.assertTrue(all(st['priority'] == 1 for st in subtasks))

    def test_validate_decomposition(self):
        """Test decomposition validation."""
        valid_subtasks = [{
            'description': "Subtask",
            'entities': [],
            'keywords': [],
            'complexity': 0.2
        }] * 3
        self.assertTrue(self.decomposer.validate_decomposition(valid_subtasks))

        # Test invalid case (empty list)
        self.assertFalse(self.decomposer.validate_decomposition([]))

    def test_assign_priorities(self):
        """Test priority assignment."""
        task = {'complexity': 0.9}
        priorities = self.decomposer._assign_priorities(task, count=2)
        self.assertEqual(len(priorities), 2)
        self.assertEqual(sum(priorities), 2)

    def test_initial_priority(self):
        """Test initial priority determination."""
        self.assertEqual(self.decomposer._determine_initial_priority(0.95), 1)
        self.assertEqual(self.decomposer._determine_initial_priority(0.8), 2)
        self.assertEqual(self.decomposer._determine_initial_priority(0.6), 3)

if __name__ == '__main__':
    unittest.main()