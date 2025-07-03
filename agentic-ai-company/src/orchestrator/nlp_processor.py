#!/usr/bin/env python3
"""
NLP Processor for Master Orchestrator
Uses spaCy for natural language processing tasks
"""

import spacy
from typing import List, Dict, Any

class NLPProcessor:
    """NLP processor using spaCy for text analysis."""

    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize the NLP processor with a spaCy model."""
        self.nlp = spacy.load(model_name)

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text and return structured information."""
        doc = self.nlp(text)
        return {
            "text": text,
            "tokens": [token.text for token in doc],
            "entities": [(ent.text, ent.label_) for ent in doc.ents],
            "sentences": [sent.text for sent in doc.sents],
            "noun_chunks": [chunk.text for chunk in doc.noun_chunks]
        }

    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from the text."""
        doc = self.nlp(text)
        return [chunk.text for chunk in doc.noun_chunks]

    def identify_intent(self, text: str) -> Dict[str, Any]:
        """Identify intent and extract relevant information."""
        doc = self.nlp(text)

        # Simple heuristic-based intent detection
        if any(token.text.lower() in ["create", "build"] for token in doc):
            return {"intent": "CREATE_PROJECT", "confidence": 0.95}
        elif any(token.text.lower() in ["deploy", "release"] for token in doc):
            return {"intent": "DEPLOY_APPLICATION", "confidence": 0.85}
        else:
            return {"intent": "UNKNOWN", "confidence": 0.1}

        return {"intent": "UNKNOWN", "confidence": 0.0}

    def extract_requirements(self, text: str) -> Dict[str, List[str]]:
        """Extract requirements from user input."""
        doc = self.nlp(text)

        # Extract features mentioned in the text
        features = []
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "FEATURE"]:
                features.append(ent.text)

        # Extract any specific technologies mentioned
        tech_mentions = [token.text for token in doc if token.pos_ == "NOUN" and token.dep_ == "compound"]

        return {
            "features": features,
            "technologies": tech_mentions
        }