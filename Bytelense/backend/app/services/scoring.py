"""Nutrition scoring service using DSPy ReAct agent."""

import logging
import json
from typing import List
from app.models.schemas import NutritionData, UserProfile, ScoringResult, Citation
from app.models.dspy_modules import (
    NutritionScorerAgent,
    DataCleanerAgent,
    SummaryGenerator
)
from app.services.citation_manager import CitationManager

logger = logging.getLogger(__name__)


class NutritionScoringService:
    """Orchestrates nutrition scoring with AI reasoning."""

    def __init__(self):
        """Initialize scoring service."""
        self.agent = NutritionScorerAgent()
        self.data_cleaner = DataCleanerAgent()
        self.summary_generator = SummaryGenerator()
        logger.info("Nutrition scoring service initialized")

    async def score(
        self,
        nutrition_data: NutritionData,
        user_profile: UserProfile
    ) -> ScoringResult:
        """
        Score nutrition data against user profile.

        Args:
            nutrition_data: Nutrition data to analyze
            user_profile: User health profile

        Returns:
            Complete scoring result with verdict, reasoning, and citations
        """
        logger.info(f"Scoring {nutrition_data.product_name} for {user_profile.name}")

        # Initialize citation manager
        citation_mgr = CitationManager()

        # Step 1: Check for allergens (immediate fail)
        allergen_warnings = self._check_allergens(nutrition_data, user_profile)
        if allergen_warnings:
            return self._create_allergen_fail_result(
                nutrition_data,
                allergen_warnings,
                citation_mgr
            )

        # Step 2: Clean and validate data
        nutrition_dict = nutrition_data.model_dump()
        cleaned_data, data_quality_score = self.data_cleaner.clean(nutrition_dict)

        # Add primary source citation
        if nutrition_data.data_source == "openfoodfacts" and nutrition_data.barcode:
            citation_mgr.add_source(
                url=f"https://world.openfoodfacts.org/product/{nutrition_data.barcode}",
                title=f"{nutrition_data.product_name} - OpenFoodFacts",
                snippet=f"Nutrition data for {nutrition_data.product_name}",
                source_type="openfoodfacts"
            )

        # Step 3: Run DSPy ReAct agent
        try:
            profile_dict = user_profile.model_dump()
            result = self.agent.forward(cleaned_data, profile_dict)

            # Parse agent output
            score = self._parse_score(result.score)
            verdict = self._parse_verdict(result.verdict)
            reasoning = result.reasoning
            warnings = self._parse_json_list(result.warnings)
            highlights = self._parse_json_list(result.highlights)
            confidence = self._parse_confidence(result.confidence)

            # Extract reasoning steps (from ReAct trace)
            reasoning_steps = self._extract_reasoning_steps(result)

            # Generate citations from reasoning
            citations = citation_mgr.generate_citation_objects()

            return ScoringResult(
                score=score,
                verdict=verdict,
                reasoning=reasoning,
                warnings=warnings,
                highlights=highlights,
                citations=citations,
                confidence=confidence,
                data_quality_score=data_quality_score,
                reasoning_steps=reasoning_steps,
                factors_considered=[
                    "Goal alignment",
                    "Nutritional density",
                    "Processing level",
                    "Portion appropriateness",
                    "Data quality"
                ]
            )

        except Exception as e:
            logger.error(f"ReAct agent error: {e}")
            # Fallback to rule-based scoring
            return self._fallback_scoring(
                nutrition_data,
                user_profile,
                data_quality_score,
                citation_mgr
            )

    def _check_allergens(
        self,
        nutrition_data: NutritionData,
        user_profile: UserProfile
    ) -> List[str]:
        """Check for allergen violations."""
        warnings = []

        for allergen in user_profile.allergies:
            allergen_lower = allergen.lower()

            # Check allergens list
            if any(allergen_lower in a.lower() for a in nutrition_data.allergens):
                warnings.append(f"Contains {allergen}")

            # Check ingredients
            ingredients_text = " ".join(nutrition_data.ingredients).lower()
            if allergen_lower in ingredients_text:
                warnings.append(f"May contain {allergen} in ingredients")

        return warnings

    def _create_allergen_fail_result(
        self,
        nutrition_data: NutritionData,
        warnings: List[str],
        citation_mgr: CitationManager
    ) -> ScoringResult:
        """Create auto-fail result for allergen violations."""
        citations = citation_mgr.generate_citation_objects()

        return ScoringResult(
            score=0.0,
            verdict="avoid",
            reasoning=f"This product contains allergens that you're allergic to. {', '.join(warnings)}",
            warnings=warnings,
            highlights=[],
            citations=citations,
            confidence=1.0,
            data_quality_score=1.0,
            reasoning_steps=["Allergen check failed"],
            factors_considered=["Allergen safety"]
        )

    def _fallback_scoring(
        self,
        nutrition_data: NutritionData,
        user_profile: UserProfile,
        data_quality_score: float,
        citation_mgr: CitationManager
    ) -> ScoringResult:
        """Fallback rule-based scoring when AI fails."""
        logger.warning("Using fallback rule-based scoring")

        score = 5.0  # Start neutral
        warnings = []
        highlights = []

        # Simple rules based on daily targets
        targets = user_profile.daily_targets

        # Check sugar
        if nutrition_data.sugar_g > targets.sugar_g * 0.5:
            score -= 2.0
            warnings.append("High sugar content")
        else:
            highlights.append("Low sugar")

        # Check sodium
        if nutrition_data.sodium_mg > targets.sodium_mg * 0.3:
            score -= 2.0
            warnings.append("High sodium")
        else:
            highlights.append("Low sodium")

        # Check protein
        if nutrition_data.protein_g > 10.0:
            score += 1.0
            highlights.append("Good protein source")

        # Check fiber
        if nutrition_data.fiber_g and nutrition_data.fiber_g > 5.0:
            score += 1.0
            highlights.append("High fiber")

        score = max(0.0, min(10.0, score))
        verdict = "good" if score >= 7.0 else "moderate" if score >= 4.0 else "avoid"

        citations = citation_mgr.generate_citation_objects()

        return ScoringResult(
            score=score,
            verdict=verdict,
            reasoning=f"Rule-based analysis: {', '.join(highlights + warnings)}",
            warnings=warnings,
            highlights=highlights,
            citations=citations,
            confidence=0.6,
            data_quality_score=data_quality_score,
            reasoning_steps=["Rule-based fallback scoring"],
            factors_considered=["Sugar", "Sodium", "Protein", "Fiber"]
        )

    def _parse_score(self, score_str: str) -> float:
        """Parse score from string."""
        try:
            score = float(score_str)
            return max(0.0, min(10.0, score))
        except (ValueError, TypeError):
            logger.warning(f"Invalid score: {score_str}")
            return 5.0

    def _parse_verdict(self, verdict_str: str) -> str:
        """Parse verdict from string."""
        verdict_lower = str(verdict_str).lower()
        if "good" in verdict_lower:
            return "good"
        elif "avoid" in verdict_lower:
            return "avoid"
        else:
            return "moderate"

    def _parse_confidence(self, confidence_str: str) -> float:
        """Parse confidence from string."""
        try:
            confidence = float(confidence_str)
            return max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            return 0.7

    def _parse_json_list(self, json_str: str) -> List[str]:
        """Parse JSON list from string."""
        try:
            if isinstance(json_str, list):
                return json_str
            data = json.loads(json_str)
            if isinstance(data, list):
                return data
            return []
        except (json.JSONDecodeError, TypeError):
            # Try to parse as comma-separated
            items = str(json_str).split(",")
            return [item.strip() for item in items if item.strip()]

    def _extract_reasoning_steps(self, result) -> List[str]:
        """Extract reasoning steps from ReAct result."""
        # In a full implementation, we'd extract the thought/action/observation trace
        # For MVP, we return a simple list
        return [
            "Analyzed nutritional content",
            "Compared against user goals",
            "Researched health guidelines",
            "Generated personalized verdict"
        ]


# Global scoring service instance
scoring_service = NutritionScoringService()
