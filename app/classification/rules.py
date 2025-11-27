"""
Classification Rules for Seniority Detection
=============================================
This module provides regex-based classification for job titles to determine
if a user is C-suite or VP level. The rules are loaded from a JSON config
file to allow easy updates without code changes.

Design note: This is built to be easily extensible to add LLM-based 
classification in the future for fuzzy matching.
"""

import re
import json
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.json"


class SeniorityClassifier:
    """Classifies job titles into seniority levels using regex patterns."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize classifier with config file."""
        if config_path is None:
            config_path = CONFIG_PATH
            
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.version = self.config.get('version', 'v1')
        
        # Compile regex patterns for performance
        self.exclusion_regex = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config['exclusion_patterns']
        ]
        
        self.csuite_regex = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config['csuite_patterns']
        ]
        
        self.vp_regex = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config['vp_patterns']
        ]
        
        logger.info(f"Initialized SeniorityClassifier {self.version}")
    
    def normalize_title(self, title: str) -> str:
        """
        Normalize job title for consistent matching.
        
        - Convert to lowercase
        - Strip leading/trailing whitespace
        - Collapse multiple spaces to single space
        - Remove most punctuation (keep hyphens and periods for abbreviations)
        """
        if not title:
            return ""
        
        # Lowercase
        normalized = title.lower().strip()
        
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove excessive punctuation but keep periods and hyphens
        normalized = re.sub(r'[^\w\s\.\-]', '', normalized)
        
        return normalized
    
    def is_excluded(self, normalized_title: str) -> bool:
        """Check if title matches any exclusion patterns."""
        for pattern in self.exclusion_regex:
            if pattern.search(normalized_title):
                logger.debug(f"Title '{normalized_title}' matched exclusion: {pattern.pattern}")
                return True
        return False
    
    def check_csuite(self, normalized_title: str) -> bool:
        """Check if title matches C-suite patterns."""
        for pattern in self.csuite_regex:
            if pattern.search(normalized_title):
                logger.debug(f"Title '{normalized_title}' matched C-suite: {pattern.pattern}")
                return True
        return False
    
    def check_vp(self, normalized_title: str) -> bool:
        """Check if title matches VP patterns."""
        for pattern in self.vp_regex:
            if pattern.search(normalized_title):
                logger.debug(f"Title '{normalized_title}' matched VP: {pattern.pattern}")
                return True
        return False
    
    def classify(self, title: str) -> Tuple[bool, str]:
        """
        Classify a job title into seniority level.
        
        Args:
            title: Raw job title string
            
        Returns:
            Tuple of (is_senior, seniority_level)
            - is_senior: True if title indicates VP or C-suite
            - seniority_level: 'csuite', 'vp', or '' (empty string if not senior)
        """
        if not title or not title.strip():
            return (False, "")
        
        normalized = self.normalize_title(title)
        
        # Check exclusions first
        if self.is_excluded(normalized):
            logger.info(f"Title excluded: {title}")
            return (False, "")
        
        # Check C-suite patterns
        if self.check_csuite(normalized):
            logger.info(f"Title classified as C-suite: {title}")
            return (True, "csuite")
        
        # Check VP patterns
        if self.check_vp(normalized):
            logger.info(f"Title classified as VP: {title}")
            return (True, "vp")
        
        # Not senior
        logger.debug(f"Title not classified as senior: {title}")
        return (False, "")


# Singleton instance for easy import
_classifier_instance = None


def get_classifier() -> SeniorityClassifier:
    """Get singleton classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = SeniorityClassifier()
    return _classifier_instance


def classify_title(title: str) -> Tuple[bool, str]:
    """
    Convenience function to classify a title.
    
    Returns: (is_senior, seniority_level)
    """
    classifier = get_classifier()
    return classifier.classify(title)


# Future extension point for LLM-based classification
class LLMClassifier:
    """
    Placeholder for future LLM-based classification.
    
    This would be used for fuzzy titles that don't match regex patterns
    but might still indicate seniority (e.g., "Head of Global Enterprise Sales").
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize LLM classifier."""
        self.api_key = api_key
        # TODO: Initialize LLM client (OpenAI, Anthropic, etc.)
        pass
    
    def classify(self, title: str) -> Tuple[bool, str]:
        """
        Classify title using LLM.
        
        This would send a prompt to the LLM asking it to classify the title.
        """
        # TODO: Implement LLM classification
        raise NotImplementedError("LLM classification not yet implemented")


# Hybrid classifier that tries regex first, falls back to LLM
class HybridClassifier:
    """
    Combines regex and LLM classification.
    
    Uses regex first (fast, deterministic), falls back to LLM for ambiguous cases.
    """
    
    def __init__(self, use_llm: bool = False):
        """Initialize hybrid classifier."""
        self.regex_classifier = get_classifier()
        self.llm_classifier = LLMClassifier() if use_llm else None
    
    def classify(self, title: str) -> Tuple[bool, str]:
        """Classify using regex first, optionally LLM fallback."""
        is_senior, level = self.regex_classifier.classify(title)
        
        if is_senior or not self.llm_classifier:
            return (is_senior, level)
        
        # If regex didn't match and we have LLM, try LLM
        try:
            return self.llm_classifier.classify(title)
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            return (False, "")

