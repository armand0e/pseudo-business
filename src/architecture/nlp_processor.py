"""
NLP Processor using spaCy for text processing, named entity recognition, and dependency parsing.
"""

from src.infrastructure.logging_system import LoggingSystem
import spacy
from typing import Optional, Dict, List

_logging_system = LoggingSystem()
logger = _logging_system.get_logger()

@_logging_system.error_handler
class NLPProcessor:
    """
    A class to handle natural language processing tasks using spaCy.

    Attributes:
        nlp (spacy.Language): The loaded spaCy model.
        config (Dict): Configuration parameters for the NLP processor.
    """

    def __init__(self, config: Dict):
        """
        Initialize the NLPProcessor with a given configuration.

        Args:
            config (Dict): Configuration dictionary containing model name and other parameters.
        """
        self.config = config
        self.nlp = None

    def load_model(self) -> None:
        """
        Load the spaCy model specified in the configuration.

        Raises:
            ValueError: If the model name is not supported or if loading fails.
        """
        logger.info("Loading spaCy model")
        try:
            model_name = self.config.get('model_name', 'en_core_web_sm')
            self.nlp = spacy.load(model_name)
            logger.info(f"Successfully loaded model '{model_name}'")
        except OSError as e:
            error_msg = f"Model '{self.config.get('model_name')}' not found. Please install it first."
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess the input text by cleaning and tokenizing.

        Args:
            text (str): Input text to preprocess.

        Returns:
            str: Cleaned and tokenized text.
        """
        logger.debug(f"Preprocessing text: '{text[:50]}...'")
        if not isinstance(text, str):
            raise ValueError("Input must be a string.")

        # Basic preprocessing
        text = text.strip()
        text = text.lower()

        # Remove special characters and numbers (optional)
        text = ''.join([char for char in text if char.isalpha() or char.isspace()])
        
        # Remove extra whitespace
        text = ' '.join(text.split())

        return text

    def recognize_entities(self, text: str) -> List[Dict]:
        """
        Recognize named entities in the input text.

        Args:
            text (str): Input text to analyze.

        Returns:
            List[Dict]: List of dictionaries containing entity text and label.
        """
        if self.nlp is None:
            logger.error("Model not loaded. Call load_model() first.")
            raise RuntimeError("Model not loaded. Call load_model() first.")

        logger.debug(f"Recognizing entities in text: '{text[:50]}...'")
        doc = self.nlp(text)
        return [{'text': ent.text, 'label': ent.label_} for ent in doc.ents]

    def parse_dependencies(self, text: str) -> List[Dict]:
        """
        Perform dependency parsing on the input text.

        Args:
            text (str): Input text to analyze.

        Returns:
            List[Dict]: List of dictionaries containing token text and dependencies.
        """
        if self.nlp is None:
            logger.error("Model not loaded. Call load_model() first.")
            raise RuntimeError("Model not loaded. Call load_model() first.")

        logger.debug(f"Parsing dependencies for text: '{text[:50]}...'")
        doc = self.nlp(text)
        return [{'text': token.text, 'dep': token.dep_, 'head': token.head.text} for token in doc]

    def analyze_text(self, text: str) -> Dict:
        """
        Analyze text and return comprehensive information including entities, complexity, and keywords.

        Args:
            text (str): Input text to analyze.

        Returns:
            Dict: Dictionary containing analysis results.
        """
        if self.nlp is None:
            logger.error("Model not loaded. Call load_model() first.")
            raise RuntimeError("Model not loaded. Call load_model() first.")

        logger.debug(f"Analyzing text: '{text[:50]}...'")
        doc = self.nlp(text)
        
        # Calculate complexity based on sentence length and dependency depth
        complexity = min(1.0, len(doc) / 50.0)  # Simple complexity measure
        
        # Extract keywords (nouns and proper nouns)
        keywords = [token.text.lower() for token in doc if token.pos_ in ['NOUN', 'PROPN']]
        
        return {
            'entities': [{'text': ent.text, 'label': ent.label_} for ent in doc.ents],
            'complexity': complexity,
            'keywords': keywords
        }

    def process_text(self, text: str) -> Dict:
        """
        Process input text and return comprehensive analysis.

        Args:
            text (str): Input text to process.

        Returns:
            Dict: Dictionary containing processed text analysis.
        """
        logger.info(f"Processing text: '{text[:50]}...'")
        
        try:
            # Load model if not already loaded
            if self.nlp is None:
                self.load_model()
            
            # Analyze the text
            result = self.analyze_text(text)
            
            # Add additional processing information
            result.update({
                'original_text': text,
                'preprocessed_text': self.preprocess_text(text),
                'dependencies': self.parse_dependencies(text),
                'is_valid_task': self.is_valid_task(text),
                'text_length': len(text),
                'word_count': len(text.split())
            })
            
            logger.info("Text processing completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            # Return basic analysis on error
            return {
                'original_text': text,
                'entities': [],
                'complexity': 0.0,
                'keywords': [],
                'error': str(e)
            }

    def is_valid_task(self, text: str) -> bool:
        """
        Validate if the given text represents a valid task.

        Args:
            text (str): Input text to validate.

        Returns:
            bool: True if valid task, False otherwise.
        """
        if not text or len(text.strip()) < 3:
            return False
        
        # Simple validation - check for action words
        action_words = ['implement', 'create', 'build', 'design', 'test', 'fix', 'update', 'develop']
        text_lower = text.lower()
        return any(word in text_lower for word in action_words)