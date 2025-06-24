# NLP Processor Documentation

## Overview
The NLP Processor provides natural language processing capabilities using spaCy for text analysis, named entity recognition, and dependency parsing.

## Features

### 1. Text Processing
- Preprocessing: Cleaning and tokenizing input text
- Entity Recognition: Identifying named entities in text
- Dependency Parsing: Analyzing grammatical structure of sentences

### 2. Integration with Logging System
The NLPProcessor class is now integrated with the logging system for:
- Detailed logging of processing operations
- Error handling through decorator
- Configurable log levels and output channels

## Usage Examples

### Basic Setup
```python
from src.infrastructure.logging_system import LoggingSystem
from src.architecture.nlp_processor import NLPProcessor

# Initialize logging system
logging_system = LoggingSystem()
logging_system.setup_logging(
    log_level='INFO',
    log_file='nlp.log'
)

# Create and use NLP processor
processor = NLPProcessor({
    'model_name': 'en_core_web_sm'
})
processor.load_model()

text = "Apple is looking at buying U.K. startup for $1 billion"
entities = processor.recognize_entities(text)
print(entities)
```

### Error Handling
```python
@logging_system.error_handler
def process_text(text):
    # This function will have automatic error handling and logging
    return processor.preprocess_text(text)
```

## Configuration Options

The NLPProcessor can be configured through the constructor with a configuration dictionary containing:

- `model_name`: Name of the spaCy model to load (default: 'en_core_web_sm')
- Other processing parameters as needed

## Output Formats

All processing results are returned in consistent formats:

1. **Preprocessed Text**: Cleaned and tokenized string
2. **Entity Recognition**: List of dictionaries with `text` and `label` keys
3. **Dependency Parsing**: List of dictionaries with `text`, `dep`, and `head` keys

## Integration Guidelines

### For Developers
1. Initialize the LoggingSystem before creating NLPProcessor instances
2. Use the error handler decorator for any functions that process text
3. Configure appropriate log levels based on your needs

### For System Administrators
1. Monitor the NLP processing logs for errors or warnings
2. Adjust log rotation settings as needed based on usage
3. Ensure the spaCy model is properly installed and accessible