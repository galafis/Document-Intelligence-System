"""
Document Summarizer Module
Extractive summarization using TF-IDF sentence scoring.
"""

import math
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple


class DocumentSummarizer:
    """Generates extractive summaries using TF-IDF-based sentence scoring."""

    STOP_WORDS = frozenset({
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "shall", "can", "this", "that",
        "these", "those", "it", "its", "not", "no", "so", "if", "then",
        "than", "when", "where", "which", "who", "whom", "what", "how",
        "all", "each", "every", "both", "few", "more", "most", "some",
        "any", "other", "into", "through", "during", "before", "after",
        "above", "below", "between", "out", "off", "over", "under", "about",
        "up", "down", "as", "just", "also", "very", "often", "however",
    })

    def __init__(self, stop_words: Optional[frozenset] = None):
        """
        Initialize the summarizer.

        Args:
            stop_words: Custom stop words set.
        """
        self.stop_words = stop_words or self.STOP_WORDS

    def summarize(
        self,
        text: str,
        num_sentences: int = 3,
        ratio: Optional[float] = None,
    ) -> Dict:
        """
        Generate an extractive summary.

        Args:
            text: Input text to summarize.
            num_sentences: Number of sentences in summary.
            ratio: Ratio of sentences to include (overrides num_sentences).

        Returns:
            Dictionary with summary text and metadata.
        """
        sentences = self._split_sentences(text)
        if not sentences:
            return {"summary": "", "sentences": [], "compression_ratio": 0.0}

        if ratio is not None:
            num_sentences = max(1, int(len(sentences) * ratio))

        num_sentences = min(num_sentences, len(sentences))

        # Score sentences using TF-IDF
        scores = self._score_sentences(sentences)

        # Select top sentences while preserving order
        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )[:num_sentences]

        # Preserve original order
        selected_indices = sorted(ranked_indices)
        summary_sentences = [sentences[i] for i in selected_indices]

        summary_text = " ".join(summary_sentences)
        compression = len(summary_text) / len(text) if text else 0.0

        return {
            "summary": summary_text,
            "sentences": [
                {"text": sentences[i], "score": round(scores[i], 4), "index": i}
                for i in selected_indices
            ],
            "num_original_sentences": len(sentences),
            "num_summary_sentences": len(summary_sentences),
            "compression_ratio": round(compression, 4),
        }

    def _score_sentences(self, sentences: List[str]) -> List[float]:
        """Score sentences using TF-IDF."""
        # Tokenize all sentences
        tokenized = [self._tokenize(s) for s in sentences]

        # Build document frequency
        df = Counter()
        for tokens in tokenized:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] += 1

        num_docs = len(sentences)
        scores = []

        for tokens in tokenized:
            if not tokens:
                scores.append(0.0)
                continue

            tf = Counter(tokens)
            score = 0.0

            for token, count in tf.items():
                term_tf = count / len(tokens)
                term_idf = math.log((num_docs + 1) / (df[token] + 1)) + 1
                score += term_tf * term_idf

            # Normalize by sentence length (avoid bias toward long sentences)
            score /= math.sqrt(len(tokens))

            # Position bonus: first and last sentences get a boost
            scores.append(score)

        # Position boost
        if scores:
            max_score = max(scores) if max(scores) > 0 else 1.0
            scores[0] += max_score * 0.1  # First sentence boost
            if len(scores) > 1:
                scores[-1] += max_score * 0.05  # Last sentence boost

        return scores

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text, removing stop words."""
        tokens = re.findall(r"[a-z]+", text.lower())
        return [t for t in tokens if t not in self.stop_words and len(t) > 2]

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sentences if len(s.strip()) > 10]
