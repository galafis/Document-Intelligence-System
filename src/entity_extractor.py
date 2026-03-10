"""
Named Entity Extractor Module
Extracts named entities from text using regex-based pattern matching.
"""

import re
from typing import Dict, List, Tuple


class EntityExtractor:
    """Extracts named entities from text using pattern matching."""

    # Regex patterns for common entity types
    PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b(?:\+?1[-.\s]?)?(?:\(?\d{2,3}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{4}\b",
        "url": r"https?://(?:[\w-]+\.)+[\w-]+(?:/[\w./?%&=+-]*)?",
        "date": (
            r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
            r"(?:January|February|March|April|May|June|July|August|"
            r"September|October|November|December)\s+\d{1,2},?\s*\d{4}|"
            r"\d{4}-\d{2}-\d{2})\b"
        ),
        "money": r"\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|BRL|GBP)\b",
        "percentage": r"\b\d+(?:\.\d+)?%\b",
        "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        "cpf": r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
        "cnpj": r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b",
    }

    # Patterns for proper nouns (capitalized sequences)
    PROPER_NOUN_PATTERN = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b"

    # Common title words to help identify person names
    TITLE_WORDS = {"Mr", "Mrs", "Ms", "Dr", "Prof", "Sr", "Sra"}

    # Words that typically start organization names
    ORG_INDICATORS = {
        "Inc", "Corp", "LLC", "Ltd", "Company", "Group", "Foundation",
        "Institute", "University", "Association", "Department", "Ministry",
    }

    def __init__(self, custom_patterns: Dict[str, str] = None):
        """
        Initialize the entity extractor.

        Args:
            custom_patterns: Additional regex patterns for entity types.
        """
        self.patterns = dict(self.PATTERNS)
        if custom_patterns:
            self.patterns.update(custom_patterns)

    def extract(self, text: str) -> Dict[str, List[Dict]]:
        """
        Extract all named entities from text.

        Args:
            text: Input text to extract entities from.

        Returns:
            Dictionary mapping entity types to lists of entity occurrences.
        """
        entities = {}

        # Extract pattern-based entities
        for entity_type, pattern in self.patterns.items():
            matches = self._find_matches(text, pattern, entity_type)
            if matches:
                entities[entity_type] = matches

        # Extract proper nouns (potential person/org names)
        proper_nouns = self._extract_proper_nouns(text)
        if proper_nouns:
            entities["proper_noun"] = proper_nouns

        return entities

    def extract_type(self, text: str, entity_type: str) -> List[Dict]:
        """
        Extract entities of a specific type.

        Args:
            text: Input text.
            entity_type: Type of entity to extract.

        Returns:
            List of entity occurrences.
        """
        if entity_type == "proper_noun":
            return self._extract_proper_nouns(text)

        pattern = self.patterns.get(entity_type)
        if not pattern:
            raise ValueError(f"Unknown entity type: {entity_type}")

        return self._find_matches(text, pattern, entity_type)

    def _find_matches(
        self, text: str, pattern: str, entity_type: str
    ) -> List[Dict]:
        """Find all regex matches and return structured results."""
        matches = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            matches.append({
                "text": match.group(),
                "type": entity_type,
                "start": match.start(),
                "end": match.end(),
            })
        return matches

    def _extract_proper_nouns(self, text: str) -> List[Dict]:
        """Extract proper nouns (capitalized word sequences)."""
        # Skip first word of sentences
        sentences = re.split(r"[.!?]\s+", text)
        proper_nouns = []
        seen = set()

        for sentence in sentences:
            words = sentence.split()
            if len(words) < 2:
                continue

            # Look for capitalized sequences (skip sentence-initial word)
            i = 1
            while i < len(words):
                if re.match(r"^[A-Z][a-z]+$", words[i]):
                    noun_parts = [words[i]]
                    j = i + 1
                    while j < len(words) and re.match(r"^[A-Z][a-z]+$", words[j]):
                        noun_parts.append(words[j])
                        j += 1
                    if len(noun_parts) >= 2:
                        noun = " ".join(noun_parts)
                        if noun not in seen:
                            seen.add(noun)
                            proper_nouns.append({
                                "text": noun,
                                "type": "proper_noun",
                                "start": text.find(noun),
                                "end": text.find(noun) + len(noun),
                            })
                    i = j
                else:
                    i += 1

        return proper_nouns

    def add_pattern(self, entity_type: str, pattern: str):
        """Add a custom entity pattern."""
        self.patterns[entity_type] = pattern

    def get_entity_summary(self, text: str) -> Dict[str, int]:
        """Get a count summary of all entity types found."""
        entities = self.extract(text)
        return {etype: len(elist) for etype, elist in entities.items()}
