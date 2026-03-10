"""
Tests for the Document Intelligence System.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from document_parser import DocumentParser
from text_classifier import TextClassifier
from entity_extractor import EntityExtractor
from summarizer import DocumentSummarizer
from keyword_extractor import KeywordExtractor


SAMPLE_TEXT = (
    "Machine learning is a branch of computer science that focuses on algorithms. "
    "These algorithms allow software systems to learn from data and improve performance. "
    "Deep learning is a subset of machine learning that uses neural networks. "
    "Neural networks are inspired by the human brain and consist of layers of nodes. "
    "Common applications include image recognition, natural language processing, and robotics."
)

FINANCE_TEXT = (
    "The stock market experienced significant growth in the last quarter. "
    "Investment portfolios showed strong returns with revenue exceeding expectations. "
    "Bank lending rates remained low, encouraging credit expansion. "
    "Financial analysts predict continued market stability through next year."
)

ENTITY_TEXT = (
    "Contact John Smith at john.smith@example.com or call +1-555-123-4567. "
    "The meeting is on January 15, 2025 at the New York office. "
    "The project budget is $50,000.00 USD and we expect 15% growth. "
    "Visit https://example.com for more details."
)


class TestDocumentParser:
    """Test the DocumentParser class."""

    def setup_method(self):
        self.parser = DocumentParser()

    def test_parse_text_content(self):
        result = self.parser.parse_text(SAMPLE_TEXT)
        assert result["text"] == SAMPLE_TEXT
        assert result["word_count"] > 0
        assert result["char_count"] > 0
        assert result["sentence_count"] > 0

    def test_parse_text_word_count(self):
        result = self.parser.parse_text("one two three four five")
        assert result["word_count"] == 5

    def test_parse_text_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(SAMPLE_TEXT)
            f.flush()
            result = self.parser.parse(f.name)

        assert result["text"] == SAMPLE_TEXT
        assert result["format"] == "txt"
        os.unlink(f.name)

    def test_parse_csv_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write("name,age,city\n")
            f.write("Alice,30,Boston\n")
            f.write("Bob,25,Denver\n")
            f.flush()
            result = self.parser.parse(f.name)

        assert result["format"] == "csv"
        assert result["column_count"] == 3
        assert result["row_count"] == 2
        os.unlink(f.name)

    def test_unsupported_format(self):
        with pytest.raises(ValueError):
            self.parser.parse("file.xyz")

    def test_paragraphs_splitting(self):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        result = self.parser.parse_text(text)
        assert result["paragraph_count"] == 3

    def test_empty_text(self):
        result = self.parser.parse_text("")
        assert result["word_count"] == 0


class TestTextClassifier:
    """Test the TextClassifier class."""

    def setup_method(self):
        self.classifier = TextClassifier()

    def test_classify_technology(self):
        text = "This software uses advanced algorithms for data processing on cloud servers."
        results = self.classifier.classify(text)
        assert len(results) > 0
        assert results[0]["category"] == "technology"
        assert results[0]["score"] > 0

    def test_classify_finance(self):
        results = self.classifier.classify(FINANCE_TEXT)
        categories = [r["category"] for r in results]
        assert "finance" in categories

    def test_classify_empty_text(self):
        results = self.classifier.classify("")
        assert results[0]["category"] == "unknown"

    def test_classify_top_k(self):
        results = self.classifier.classify(SAMPLE_TEXT, top_k=2)
        assert len(results) == 2

    def test_add_category(self):
        self.classifier.add_category("sports", ["game", "team", "player", "score"])
        text = "The team scored a game-winning goal with their best player."
        results = self.classifier.classify(text)
        categories = [r["category"] for r in results]
        assert "sports" in categories

    def test_remove_category(self):
        self.classifier.remove_category("legal")
        assert "legal" not in self.classifier.categories


class TestEntityExtractor:
    """Test the EntityExtractor class."""

    def setup_method(self):
        self.extractor = EntityExtractor()

    def test_extract_email(self):
        entities = self.extractor.extract(ENTITY_TEXT)
        assert "email" in entities
        assert any("john.smith@example.com" in e["text"] for e in entities["email"])

    def test_extract_url(self):
        entities = self.extractor.extract(ENTITY_TEXT)
        assert "url" in entities
        assert any("https://example.com" in e["text"] for e in entities["url"])

    def test_extract_money(self):
        entities = self.extractor.extract(ENTITY_TEXT)
        assert "money" in entities

    def test_extract_percentage(self):
        entities = self.extractor.extract(ENTITY_TEXT)
        assert "percentage" in entities
        assert any("15%" in e["text"] for e in entities["percentage"])

    def test_extract_date(self):
        entities = self.extractor.extract(ENTITY_TEXT)
        assert "date" in entities

    def test_extract_specific_type(self):
        emails = self.extractor.extract_type(ENTITY_TEXT, "email")
        assert len(emails) >= 1

    def test_unknown_entity_type(self):
        with pytest.raises(ValueError):
            self.extractor.extract_type("text", "unknown_type")

    def test_entity_summary(self):
        summary = self.extractor.get_entity_summary(ENTITY_TEXT)
        assert isinstance(summary, dict)
        assert "email" in summary

    def test_custom_pattern(self):
        extractor = EntityExtractor({"hashtag": r"#\w+"})
        entities = extractor.extract("Check #python and #machinelearning")
        assert "hashtag" in entities
        assert len(entities["hashtag"]) == 2


class TestDocumentSummarizer:
    """Test the DocumentSummarizer class."""

    def setup_method(self):
        self.summarizer = DocumentSummarizer()

    def test_summarize_basic(self):
        result = self.summarizer.summarize(SAMPLE_TEXT, num_sentences=2)
        assert "summary" in result
        assert len(result["summary"]) > 0
        assert result["num_summary_sentences"] == 2

    def test_summarize_ratio(self):
        result = self.summarizer.summarize(SAMPLE_TEXT, ratio=0.4)
        assert result["num_summary_sentences"] <= result["num_original_sentences"]

    def test_summarize_compression(self):
        result = self.summarizer.summarize(SAMPLE_TEXT, num_sentences=2)
        assert 0.0 < result["compression_ratio"] < 1.0

    def test_summarize_empty(self):
        result = self.summarizer.summarize("")
        assert result["summary"] == ""

    def test_sentence_scores(self):
        result = self.summarizer.summarize(SAMPLE_TEXT, num_sentences=2)
        for sentence in result["sentences"]:
            assert "score" in sentence
            assert "text" in sentence
            assert sentence["score"] > 0

    def test_order_preservation(self):
        result = self.summarizer.summarize(SAMPLE_TEXT, num_sentences=3)
        indices = [s["index"] for s in result["sentences"]]
        assert indices == sorted(indices)


class TestKeywordExtractor:
    """Test the KeywordExtractor class."""

    def setup_method(self):
        self.extractor = KeywordExtractor()

    def test_extract_keywords(self):
        keywords = self.extractor.extract_keywords(SAMPLE_TEXT, top_k=5)
        assert len(keywords) <= 5
        assert all("keyword" in kw for kw in keywords)
        assert all("score" in kw for kw in keywords)

    def test_keywords_sorted_by_score(self):
        keywords = self.extractor.extract_keywords(SAMPLE_TEXT, top_k=5)
        scores = [kw["score"] for kw in keywords]
        assert scores == sorted(scores, reverse=True)

    def test_extract_keyphrases(self):
        phrases = self.extractor.extract_keyphrases(SAMPLE_TEXT, top_k=3)
        assert len(phrases) <= 3
        assert all("phrase" in p for p in phrases)

    def test_empty_text_keywords(self):
        keywords = self.extractor.extract_keywords("")
        assert keywords == []

    def test_keyword_frequency(self):
        text = "python python python java java"
        keywords = self.extractor.extract_keywords(text, top_k=2)
        assert len(keywords) == 2
        # "python" should have higher frequency
        assert keywords[0]["frequency"] >= keywords[1]["frequency"]

    def test_min_word_length(self):
        keywords = self.extractor.extract_keywords(SAMPLE_TEXT, min_word_length=5)
        for kw in keywords:
            assert len(kw["keyword"]) >= 5


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_parse_classify_summarize(self):
        parser = DocumentParser()
        classifier = TextClassifier()
        summarizer = DocumentSummarizer()
        extractor = KeywordExtractor()

        parsed = parser.parse_text(SAMPLE_TEXT)
        classification = classifier.classify(parsed["text"])
        summary = summarizer.summarize(parsed["text"], num_sentences=2)
        keywords = extractor.extract_keywords(parsed["text"], top_k=5)

        assert parsed["word_count"] > 0
        assert len(classification) > 0
        assert len(summary["summary"]) > 0
        assert len(keywords) > 0

    def test_full_pipeline_with_file(self):
        parser = DocumentParser()
        entity_extractor = EntityExtractor()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(ENTITY_TEXT)
            f.flush()
            parsed = parser.parse(f.name)

        entities = entity_extractor.extract(parsed["text"])
        assert "email" in entities
        os.unlink(f.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
