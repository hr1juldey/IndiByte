"""Citation management for Perplexity-style references."""

import logging
from datetime import datetime
from typing import List, Dict
import re

from app.models.schemas import Citation

logger = logging.getLogger(__name__)


class CitationManager:
    """Manages inline citations and reference lists like Perplexity AI."""

    def __init__(self):
        """Initialize citation manager."""
        self.sources: List[Dict] = []
        self.citation_map: Dict[str, int] = {}
        self.next_id = 1

    def add_source(
        self,
        url: str,
        title: str,
        snippet: str,
        source_type: str = "searxng"
    ) -> int:
        """
        Add a source and return its citation ID.

        Args:
            url: Source URL
            title: Source title
            snippet: Relevant excerpt
            source_type: Type of source

        Returns:
            Citation ID number
        """
        # Check if already added
        if url in self.citation_map:
            return self.citation_map[url]

        # Add new source
        citation_id = self.next_id
        self.sources.append({
            "id": citation_id,
            "url": url,
            "title": title,
            "snippet": snippet[:200],  # Limit snippet length
            "accessed": datetime.now(),
            "source_type": source_type
        })

        self.citation_map[url] = citation_id
        self.next_id += 1

        logger.debug(f"Added citation [{citation_id}]: {title}")
        return citation_id

    def format_inline_citation(self, text: str, source_id: int) -> str:
        """
        Format text with inline citation.

        Args:
            text: Text to cite
            source_id: Citation ID

        Returns:
            Text with inline citation: 'High in sodium [1]'
        """
        return f"{text} [{source_id}]"

    def extract_citations_from_text(self, text: str) -> List[int]:
        """
        Extract citation IDs from text with [1], [2] patterns.

        Args:
            text: Text with inline citations

        Returns:
            List of citation IDs
        """
        pattern = r'\[(\d+)\]'
        matches = re.findall(pattern, text)
        return [int(m) for m in matches]

    def generate_citation_objects(self) -> List[Citation]:
        """
        Generate Citation objects for API response.

        Returns:
            List of Citation objects
        """
        citations = []

        for source in self.sources:
            # Assign authority score based on source type
            authority_score = self._get_authority_score(source["source_type"])

            citations.append(Citation(
                id=source["id"],
                url=source["url"],
                title=source["title"],
                snippet=source["snippet"],
                accessed=source["accessed"],
                source_type=source["source_type"],
                authority_score=authority_score
            ))

        return citations

    def _get_authority_score(self, source_type: str) -> float:
        """Get authority score based on source type."""
        authority_scores = {
            "openfoodfacts": 0.9,
            "who": 0.95,
            "fda": 0.95,
            "usda": 0.95,
            "searxng": 0.7
        }
        return authority_scores.get(source_type, 0.6)

    def get_reference_list(self) -> List[Dict]:
        """
        Generate formatted reference list for UI.

        Returns:
            List of reference dicts
        """
        return self.sources.copy()

    def clear(self):
        """Clear all citations (for new scan)."""
        self.sources.clear()
        self.citation_map.clear()
        self.next_id = 1
