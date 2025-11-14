"""Generative UI schema builder."""

import logging
from typing import Literal
from app.models.schemas import ScoringResult, UISchema, ComponentSpec

logger = logging.getLogger(__name__)


class UISchemaBuilder:
    """Generates UI schema based on scoring results."""

    def generate(self, scoring: ScoringResult) -> UISchema:
        """
        Generate UI schema from scoring result.

        Args:
            scoring: Scoring result from AI analysis

        Returns:
            UISchema defining component tree
        """
        logger.info(f"Generating UI for verdict: {scoring.verdict}")

        # Select layout and theme based on verdict
        layout, theme = self._select_layout_and_theme(scoring.verdict)

        # Assemble components
        components = []
        order = 0

        # 1. Verdict badge (always first)
        components.append(ComponentSpec(
            type="verdict_badge",
            props={
                "verdict": scoring.verdict,
                "theme": theme
            },
            order=order
        ))
        order += 1

        # 2. Score display
        components.append(ComponentSpec(
            type="score_display",
            props={
                "score": scoring.score,
                "max_score": 10.0,
                "confidence": scoring.confidence,
                "data_quality": scoring.data_quality_score
            },
            order=order
        ))
        order += 1

        # 3. Warnings (if any)
        if scoring.warnings:
            components.append(ComponentSpec(
                type="allergen_alert",
                props={
                    "warnings": scoring.warnings,
                    "severity": "high" if scoring.verdict == "avoid" else "medium"
                },
                order=order
            ))
            order += 1

            components.append(ComponentSpec(
                type="insight_list",
                props={
                    "items": scoring.warnings,
                    "type": "warning",
                    "icon": "alert-triangle"
                },
                order=order
            ))
            order += 1

        # 4. Highlights (if any)
        if scoring.highlights:
            components.append(ComponentSpec(
                type="insight_list",
                props={
                    "items": scoring.highlights,
                    "type": "highlight",
                    "icon": "check-circle"
                },
                order=order
            ))
            order += 1

        # 5. Reasoning section (expandable)
        components.append(ComponentSpec(
            type="reasoning_section",
            props={
                "reasoning": scoring.reasoning,
                "reasoning_steps": scoring.reasoning_steps,
                "factors_considered": scoring.factors_considered,
                "expanded": False
            },
            order=order
        ))
        order += 1

        # 6. Citation list (Perplexity-style)
        if scoring.citations:
            components.append(ComponentSpec(
                type="citation_list",
                props={
                    "citations": [c.model_dump() for c in scoring.citations]
                },
                order=order
            ))
            order += 1

        return UISchema(
            layout=layout,
            theme=theme,
            components=components
        )

    def _select_layout_and_theme(
        self,
        verdict: str
    ) -> tuple[Literal["alert", "balanced", "encouraging"], Literal["red", "yellow", "green"]]:
        """
        Select layout and theme based on verdict.

        Args:
            verdict: The verdict (good, moderate, avoid)

        Returns:
            Tuple of (layout, theme)
        """
        mapping = {
            "good": ("encouraging", "green"),
            "moderate": ("balanced", "yellow"),
            "avoid": ("alert", "red")
        }

        return mapping.get(verdict, ("balanced", "yellow"))


# Global UI schema builder instance
ui_schema_builder = UISchemaBuilder()
