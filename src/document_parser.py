"""
Document Parser Module
Handles PDF text extraction and document structure parsing.
"""

import re
import struct
import zlib
from typing import Dict, List, Optional, Tuple


class DocumentParser:
    """Parses documents and extracts text content."""

    SUPPORTED_FORMATS = (".txt", ".csv", ".pdf")

    def parse(self, file_path: str) -> Dict:
        """
        Parse a document and extract its content.

        Args:
            file_path: Path to the document file.

        Returns:
            Dictionary with extracted text, metadata, and structure.
        """
        if file_path.lower().endswith(".pdf"):
            return self._parse_pdf(file_path)
        elif file_path.lower().endswith(".txt"):
            return self._parse_text(file_path)
        elif file_path.lower().endswith(".csv"):
            return self._parse_csv(file_path)
        else:
            raise ValueError(f"Unsupported format: {file_path}")

    def parse_text(self, raw_text: str) -> Dict:
        """
        Parse raw text content directly.

        Args:
            raw_text: Raw text string.

        Returns:
            Dictionary with parsed content and metadata.
        """
        paragraphs = self._split_paragraphs(raw_text)
        sentences = self._split_sentences(raw_text)
        words = raw_text.split()

        return {
            "text": raw_text,
            "paragraphs": paragraphs,
            "sentences": sentences,
            "word_count": len(words),
            "char_count": len(raw_text),
            "paragraph_count": len(paragraphs),
            "sentence_count": len(sentences),
        }

    def _parse_text(self, file_path: str) -> Dict:
        """Parse a plain text file."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        result = self.parse_text(content)
        result["source"] = file_path
        result["format"] = "txt"
        return result

    def _parse_csv(self, file_path: str) -> Dict:
        """Parse a CSV file and extract text content."""
        rows = []
        headers = []
        with open(file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                fields = line.strip().split(",")
                if i == 0:
                    headers = fields
                else:
                    rows.append(fields)

        all_text = " ".join(
            " ".join(row) for row in rows
        )

        return {
            "text": all_text,
            "headers": headers,
            "rows": rows,
            "row_count": len(rows),
            "column_count": len(headers),
            "source": file_path,
            "format": "csv",
        }

    def _parse_pdf(self, file_path: str) -> Dict:
        """
        Extract text from a PDF file using pure Python.
        Handles basic PDF text extraction without external dependencies.
        """
        try:
            with open(file_path, "rb") as f:
                data = f.read()

            text = self._extract_pdf_text(data)
            result = self.parse_text(text)
            result["source"] = file_path
            result["format"] = "pdf"
            return result
        except Exception as e:
            return {
                "text": "",
                "source": file_path,
                "format": "pdf",
                "error": str(e),
                "paragraphs": [],
                "sentences": [],
                "word_count": 0,
                "char_count": 0,
                "paragraph_count": 0,
                "sentence_count": 0,
            }

    def _extract_pdf_text(self, data: bytes) -> str:
        """
        Extract text from raw PDF bytes.
        Basic extraction targeting text operators BT/ET blocks.
        """
        text_parts = []

        # Find all stream objects
        stream_pattern = rb"stream\r?\n(.*?)\r?\nendstream"
        for match in re.finditer(stream_pattern, data, re.DOTALL):
            stream_data = match.group(1)
            try:
                decompressed = zlib.decompress(stream_data)
                extracted = self._parse_pdf_text_operators(decompressed)
                if extracted:
                    text_parts.append(extracted)
            except (zlib.error, Exception):
                extracted = self._parse_pdf_text_operators(stream_data)
                if extracted:
                    text_parts.append(extracted)

        return "\n".join(text_parts)

    def _parse_pdf_text_operators(self, stream: bytes) -> str:
        """Parse PDF text operators (Tj, TJ, ') from a content stream."""
        text_parts = []
        try:
            content = stream.decode("latin-1")
        except (UnicodeDecodeError, AttributeError):
            return ""

        # Extract text from Tj operator: (text) Tj
        tj_pattern = r"\(([^)]*)\)\s*Tj"
        for match in re.finditer(tj_pattern, content):
            text_parts.append(match.group(1))

        # Extract text from TJ operator: [(text) ...] TJ
        tj_array_pattern = r"\[(.*?)\]\s*TJ"
        for match in re.finditer(tj_array_pattern, content, re.DOTALL):
            array_content = match.group(1)
            for text_match in re.finditer(r"\(([^)]*)\)", array_content):
                text_parts.append(text_match.group(1))

        return " ".join(text_parts)

    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = re.split(r"\n\s*\n", text.strip())
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sentences if s.strip()]
