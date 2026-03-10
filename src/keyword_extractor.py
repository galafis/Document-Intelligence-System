"""
Keyword Extractor Module
Extracts keywords and key phrases using TF-IDF scoring.
"""

import math
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple


class KeywordExtractor:
    """Extracts keywords and key phrases from text using TF-IDF."""

    STOP_WORDS = frozenset({
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "shall", "can", "this", "that",
        "these", "those", "it", "its", "not", "no", "so", "if", "then",
        "than", "when", "where", "which", "who", "whom", "what", "how",
        "all", "each", "every", "both", "few", "more", "most", "some",
        "any", "other", "into", "through", "during", "before", "after",
    })

    def __init__(self, stop_words: Optional[frozenset] = None):
        """
        Initialize the keyword extractor.

        Args:
            stop_words: Custom stop words set.
        """
        self.stop_words = stop_words or self.STOP_WORDS

    def extract_keywords(
        self, text: str, top_k: int = 10, min_word_length: int = 3
    ) -> List[Dict]:
        """
        Extract top keywords from text.

        Args:
            text: Input text.
            top_k: Number of keywords to return.
            min_word_length: Minimum word length to consider.

        Returns:
            List of keyword dictionaries with word and score.
        """
        tokens = self._tokenize(text, min_word_length)
        if not tokens:
            return []

        tf = Counter(tokens)
        total = len(tokens)

        scored = []
        for word, count in tf.items():
            tf_score = count / total
            # Use frequency-based IDF approximation
            idf = math.log(total / (count + 1)) + 1
            tfidf = tf_score * idf
            scored.append({
                "keyword": word,
                "score": round(tfidf, 6),
                "frequency": count,
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def extract_keyphrases(
        self, text: str, top_k: int = 5, max_phrase_length: int = 3
    ) -> List[Dict]:
        """
        Extract key phrases (n-grams) from text.

        Args:
            text: Input text.
            top_k: Number of phrases to return.
            max_phrase_length: Maximum number of words in a phrase.

        Returns:
            List of keyphrase dictionaries.
        """
        sentences = re.split(r"[.!?;]\s+", text)
        phrase_counts = Counter()

        for sentence in sentences:
            words = self._tokenize(sentence, min_length=2)
            for n in range(2, max_phrase_length + 1):
                for i in range(len(words) - n + 1):
                    phrase = " ".join(words[i : i + n])
                    phrase_counts[phrase] += 1

        # Filter phrases appearing more than once
        keyphrases = []
        for phrase, count in phrase_counts.most_common(top_k * 3):
            if count >= 1:
                keyphrases.append({
                    "phrase": phrase,
                    "frequency": count,
                    "word_count": len(phrase.split()),
                })

        return keyphrases[:top_k]

    def _tokenize(self, text: str, min_length: int = 3) -> List[str]:
        """Tokenize text, removing stop words and short words."""
        tokens = re.findall(r"[a-z]+", text.lower())
        return [
            t for t in tokens
            if t not in self.stop_words and len(t) >= min_length
        ]
