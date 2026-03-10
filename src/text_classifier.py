"""
Text Classifier Module
Classifies documents into categories using TF-IDF and cosine similarity.
"""

import math
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple


class TextClassifier:
    """Classifies text into predefined categories using TF-IDF similarity."""

    DEFAULT_CATEGORIES = {
        "technology": [
            "software", "hardware", "computer", "algorithm", "data", "network",
            "programming", "code", "system", "digital", "internet", "database",
            "server", "cloud", "machine", "learning", "processor", "memory",
        ],
        "finance": [
            "bank", "money", "investment", "stock", "market", "financial",
            "revenue", "profit", "loan", "credit", "debt", "budget", "economy",
            "trading", "portfolio", "interest", "capital", "asset",
        ],
        "healthcare": [
            "health", "medical", "patient", "doctor", "hospital", "treatment",
            "disease", "diagnosis", "clinical", "drug", "therapy", "symptom",
            "surgery", "medicine", "pharmaceutical", "vaccine", "care",
        ],
        "legal": [
            "law", "court", "legal", "attorney", "judge", "regulation",
            "compliance", "contract", "litigation", "statute", "rights",
            "jurisdiction", "defendant", "plaintiff", "case", "precedent",
        ],
        "education": [
            "school", "student", "teacher", "university", "education",
            "learning", "curriculum", "course", "degree", "academic",
            "research", "classroom", "exam", "knowledge", "training",
        ],
    }

    def __init__(self, categories: Optional[Dict[str, List[str]]] = None):
        """
        Initialize the text classifier.

        Args:
            categories: Dictionary mapping category names to keyword lists.
        """
        self.categories = categories or self.DEFAULT_CATEGORIES
        self._build_idf()

    def _build_idf(self):
        """Build inverse document frequency from category keywords."""
        all_terms = set()
        for keywords in self.categories.values():
            all_terms.update(keywords)
        self._all_terms = all_terms
        self._num_categories = len(self.categories)

    def classify(self, text: str, top_k: int = 3) -> List[Dict]:
        """
        Classify text into categories.

        Args:
            text: Input text to classify.
            top_k: Number of top categories to return.

        Returns:
            List of dictionaries with category and score.
        """
        tokens = self._tokenize(text)
        if not tokens:
            return [{"category": "unknown", "score": 0.0}]

        token_counts = Counter(tokens)
        scores = []

        for category, keywords in self.categories.items():
            score = self._compute_similarity(token_counts, keywords, len(tokens))
            scores.append({"category": category, "score": round(score, 4)})

        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:top_k]

    def _compute_similarity(
        self, token_counts: Counter, keywords: List[str], total_tokens: int
    ) -> float:
        """Compute cosine similarity between document TF-IDF and category vector."""
        if total_tokens == 0:
            return 0.0

        # Build TF vector for document
        doc_tf = {}
        for token, count in token_counts.items():
            doc_tf[token] = count / total_tokens

        # Compute cosine similarity
        dot_product = 0.0
        doc_magnitude = 0.0
        cat_magnitude = 0.0

        keyword_set = set(keywords)
        keyword_weight = 1.0 / len(keywords) if keywords else 0.0

        for token, tf in doc_tf.items():
            doc_magnitude += tf * tf
            if token in keyword_set:
                dot_product += tf * keyword_weight

        for _ in keywords:
            cat_magnitude += keyword_weight * keyword_weight

        doc_magnitude = math.sqrt(doc_magnitude) if doc_magnitude > 0 else 1.0
        cat_magnitude = math.sqrt(cat_magnitude) if cat_magnitude > 0 else 1.0

        return dot_product / (doc_magnitude * cat_magnitude)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase words."""
        text = text.lower()
        tokens = re.findall(r"[a-z]+", text)
        return tokens

    def add_category(self, name: str, keywords: List[str]):
        """Add a new classification category."""
        self.categories[name] = keywords
        self._build_idf()

    def remove_category(self, name: str):
        """Remove a classification category."""
        if name in self.categories:
            del self.categories[name]
            self._build_idf()
