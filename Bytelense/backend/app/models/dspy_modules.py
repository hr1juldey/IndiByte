"""DSPy modules for AI-powered nutrition scoring."""

import logging
from typing import List
import dspy

from app.core.config import settings
from app.mcp.searxng_tools import (
    search_nutrition_database,
    compare_similar_products,
    get_health_guidelines
)

logger = logging.getLogger(__name__)


# ============================================================================
# DSPy Signatures
# ============================================================================

class ScoreNutrition(dspy.Signature):
    """
    Analyze food nutrition data against user health profile using available tools.
    Generate a personalized health score with scientific reasoning and citations.
    """

    nutrition_data = dspy.InputField(
        desc="Raw nutrition data from sources (JSON format)"
    )
    user_profile = dspy.InputField(
        desc="User health profile and goals (JSON format)"
    )

    score = dspy.OutputField(
        desc="Health score 0-10 based on analysis"
    )
    verdict = dspy.OutputField(
        desc="Overall verdict: good, moderate, or avoid"
    )
    reasoning = dspy.OutputField(
        desc="Step-by-step scientific explanation with inline citations [1], [2]"
    )
    warnings = dspy.OutputField(
        desc="Specific health concerns with citations (JSON list)"
    )
    highlights = dspy.OutputField(
        desc="Key nutritional facts (3-5 items) with citations (JSON list)"
    )
    confidence = dspy.OutputField(
        desc="Confidence in analysis 0-1"
    )


# ============================================================================
# Configure Ollama
# ============================================================================

def configure_ollama():
    """Configure DSPy to use Ollama."""
    try:
        lm = dspy.LM(
            f'ollama_chat/{settings.ollama_model}',
            api_base=settings.ollama_api_base,
            api_key=''  # Not needed for local Ollama
        )
        dspy.configure(lm=lm)
        logger.info(f"DSPy configured with Ollama model: {settings.ollama_model}")
    except Exception as e:
        logger.error(f"Failed to configure Ollama: {e}")
        raise


# ============================================================================
# ReAct Agent Module
# ============================================================================

class NutritionScorerAgent(dspy.Module):
    """
    ReAct agent that scores nutrition data using tools for research.

    The agent will iteratively:
    1. Reason about the current state
    2. Decide which tool to call (or finish)
    3. Execute tool and gather info
    4. Repeat until confident answer (max 5 iterations)
    """

    def __init__(self):
        """Initialize ReAct agent with tools."""
        super().__init__()

        # Configure Ollama
        configure_ollama()

        # Create ReAct agent with tools (not ChainOfThought)
        self.agent = dspy.ReAct(
            signature=ScoreNutrition,
            tools=[
                search_nutrition_database,
                compare_similar_products,
                get_health_guidelines
            ],
            max_iters=settings.max_react_iterations
        )

        logger.info("NutritionScorerAgent initialized with ReAct")

    def forward(self, nutrition_data: dict, user_profile: dict):
        """
        Score nutrition data against user profile.

        Args:
            nutrition_data: Nutrition data dict
            user_profile: User profile dict

        Returns:
            DSPy prediction with score, verdict, reasoning, etc.
        """
        try:
            # Convert dicts to JSON strings for LLM input
            import json
            nutrition_json = json.dumps(nutrition_data, indent=2)
            profile_json = json.dumps(user_profile, indent=2)

            # Run ReAct agent
            result = self.agent(
                nutrition_data=nutrition_json,
                user_profile=profile_json
            )

            logger.info(f"ReAct agent completed: score={result.score}, verdict={result.verdict}")
            return result

        except Exception as e:
            logger.error(f"ReAct agent error: {e}")
            raise


# ============================================================================
# Data Cleaner Module (Simplified for MVP)
# ============================================================================

class DataCleanerAgent:
    """
    Cleans and normalizes nutrition data from multiple sources.

    For MVP, this is rule-based. In v0.2, can be DSPy-powered.
    """

    @staticmethod
    def clean(raw_data: dict) -> tuple[dict, float]:
        """
        Clean and normalize nutrition data.

        Args:
            raw_data: Raw nutrition data dict

        Returns:
            Tuple of (cleaned_data, quality_score)
        """
        quality_score = 1.0

        # Check for missing critical fields
        required_fields = ["product_name", "calories", "protein_g", "carbs_g", "fat_g"]
        missing_fields = [f for f in required_fields if not raw_data.get(f)]

        if missing_fields:
            quality_score -= 0.2 * len(missing_fields)
            logger.warning(f"Missing fields: {missing_fields}")

        # Normalize units (already done in nutrition_api, but double-check)
        cleaned = raw_data.copy()

        # Ensure numeric fields are floats
        numeric_fields = [
            "calories", "protein_g", "carbs_g", "fat_g",
            "sugar_g", "sodium_mg", "fiber_g", "saturated_fat_g"
        ]

        for field in numeric_fields:
            if field in cleaned and cleaned[field] is not None:
                try:
                    cleaned[field] = float(cleaned[field])
                except (ValueError, TypeError):
                    cleaned[field] = 0.0
                    quality_score -= 0.05

        # Flag low confidence data
        if cleaned.get("confidence", 1.0) < 0.7:
            quality_score *= cleaned.get("confidence", 0.7)

        return cleaned, max(quality_score, 0.0)


# ============================================================================
# Summary Generator (Simplified for MVP)
# ============================================================================

class SummaryGenerator:
    """
    Generates concise summaries of scoring results.

    For MVP, this is template-based. In v0.2, can be DSPy-powered.
    """

    @staticmethod
    def generate(score: float, verdict: str, highlights: List[str]) -> str:
        """Generate a summary."""
        summary_prefix = {
            "good": "✓ This product aligns well with your goals.",
            "moderate": "⚠ This product has both pros and cons.",
            "avoid": "✗ This product may not be suitable for your goals."
        }

        prefix = summary_prefix.get(verdict, "Analysis complete.")
        highlights_text = " ".join(highlights[:3])

        return f"{prefix} {highlights_text}"
