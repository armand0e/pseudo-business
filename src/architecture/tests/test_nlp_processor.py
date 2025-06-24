"""
Unit tests for the NLPProcessor class.
"""

import unittest
from src.architecture.nlp_processor import NLPProcessor

class TestNLPProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test configuration."""
        self.config = {
            'model_name': 'en_core_web_sm',
            # Add other configuration parameters as needed
        }
        self.processor = NLPProcessor(self.config)

    def test_load_model(self):
        """Test loading the spaCy model."""
        self.processor.load_model()
        self.assertIsNotNone(self.processor.nlp)
        # Test that the model has expected capabilities
        self.assertTrue(hasattr(self.processor.nlp, 'vocab'))

    def test_preprocess_text(self):
        """Test text preprocessing."""
        # Test with normal string
        result = self.processor.preprocess_text("  Hello, World! 123  ")
        self.assertEqual(result, "hello world")

        # Test with empty string
        result = self.processor.preprocess_text("")
        self.assertEqual(result, "")

        # Test with non-string input
        with self.assertRaises(ValueError):
            self.processor.preprocess_text(123)

    def test_recognize_entities(self):
        """Test named entity recognition."""
        self.processor.load_model()
        text = "Apple is looking to buy a U.K. startup for $1 billion"
        entities = self.processor.recognize_entities(text)
        self.assertEqual(len(entities), 3)
        self.assertTrue(any(e['label'] == 'ORG' for e in entities))

    def test_parse_dependencies(self):
        """Test dependency parsing."""
        self.processor.load_model()
        text = "The quick brown fox jumps over the lazy dog"
        dependencies = self.processor.parse_dependencies(text)
        self.assertEqual(len(dependencies), 9)
        self.assertTrue(any(d['dep'] == 'ROOT' for d in dependencies))

if __name__ == '__main__':
    unittest.main()