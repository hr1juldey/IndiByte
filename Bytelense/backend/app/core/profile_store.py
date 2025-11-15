"""Profile storage manager using aiofiles for async JSON I/O."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import aiofiles

from app.models.schemas import EnhancedUserProfile, DailyTargets, OnboardingRequest
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProfileStore:
    """Manages user profile storage in JSON files."""

    def __init__(self, profiles_dir: str = None):
        """Initialize profile store."""
        self.profiles_dir = Path(profiles_dir or settings.profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Profile store initialized at {self.profiles_dir}")

    def _get_profile_path(self, name: str) -> Path:
        """Get file path for a user profile."""
        # Sanitize name to prevent directory traversal
        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).lower()
        return self.profiles_dir / f"{safe_name}.json"

    async def exists(self, name: str) -> bool:
        """Check if a profile exists."""
        profile_path = self._get_profile_path(name)
        return profile_path.exists()

    async def load(self, name: str) -> Optional[EnhancedUserProfile]:
        """Load a user profile from JSON file."""
        profile_path = self._get_profile_path(name)

        if not profile_path.exists():
            logger.warning(f"Profile not found: {name}")
            return None

        try:
            async with aiofiles.open(profile_path, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)

            # Parse datetime fields
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

            profile = EnhancedUserProfile(**data)
            logger.info(f"Loaded profile: {name}")
            return profile

        except Exception as e:
            logger.error(f"Error loading profile {name}: {e}")
            return None

    async def create(self, onboarding_data: OnboardingRequest) -> EnhancedUserProfile:
        """Create a new user profile."""
        profile_path = self._get_profile_path(onboarding_data.name)

        if profile_path.exists():
            raise ValueError(f"Profile {onboarding_data.name} already exists")

        # Calculate daily targets
        daily_targets = DailyTargetCalculator.calculate(
            age=onboarding_data.age,
            gender=onboarding_data.gender,
            height_cm=onboarding_data.height_cm,
            weight_kg=onboarding_data.weight_kg,
            goals=onboarding_data.goals
        )

        # Create profile
        now = datetime.now()
        profile = EnhancedUserProfile(
            name=onboarding_data.name,
            created_at=now,
            updated_at=now,
            age=onboarding_data.age,
            gender=onboarding_data.gender,
            height_cm=onboarding_data.height_cm,
            weight_kg=onboarding_data.weight_kg,
            goals=onboarding_data.goals,
            allergies=onboarding_data.allergies,
            dietary_preferences=onboarding_data.dietary_preferences,
            nutritional_focus=onboarding_data.nutritional_focus,
            daily_targets=daily_targets
        )

        await self.save(profile)
        logger.info(f"Created profile: {onboarding_data.name}")
        return profile

    async def save(self, profile: EnhancedUserProfile) -> None:
        """Save a profile to JSON file."""
        profile_path = self._get_profile_path(profile.name)

        # Update timestamp
        profile.updated_at = datetime.now()

        # Serialize to dict
        data = profile.model_dump()
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()

        # Add schema version for future migrations
        data["schema_version"] = "1.0"

        # Write to file atomically
        try:
            async with aiofiles.open(profile_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, indent=2))
            logger.info(f"Saved profile: {profile.name}")
        except Exception as e:
            logger.error(f"Error saving profile {profile.name}: {e}")
            raise

    async def update(self, name: str, updates: Dict[str, Any]) -> EnhancedUserProfile:
        """Update an existing profile (partial update)."""
        profile = await self.load(name)

        if not profile:
            raise ValueError(f"Profile {name} not found")

        # Apply updates
        for key, value in updates.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)

        # Recalculate daily targets if relevant fields changed
        if any(k in updates for k in ["age", "gender", "height_cm", "weight_kg", "goals"]):
            profile.daily_targets = DailyTargetCalculator.calculate(
                age=profile.age,
                gender=profile.gender,
                height_cm=profile.height_cm,
                weight_kg=profile.weight_kg,
                goals=profile.goals
            )

        await self.save(profile)
        return profile


class DailyTargetCalculator:
    """Calculates daily nutritional targets based on user profile."""

    @staticmethod
    def calculate(
        age: Optional[int],
        gender: Optional[str],
        height_cm: Optional[float],
        weight_kg: Optional[float],
        goals: list[str]
    ) -> DailyTargets:
        """Calculate daily nutritional targets."""

        # Default targets (moderate adult)
        calories = 2000
        protein_g = 75.0
        carbs_g = 250.0
        fat_g = 65.0
        sugar_g = 30.0
        sodium_mg = 2300.0
        fiber_g = 28.0

        # Calculate BMR if we have the data
        if all([age, gender, height_cm, weight_kg]):
            bmr = DailyTargetCalculator._calculate_bmr(
                age, gender, height_cm, weight_kg
            )
            # Assume moderate activity level (1.55 multiplier)
            tdee = bmr * 1.55
            calories = int(tdee)

        # Adjust for goals
        for goal in goals:
            goal_lower = goal.lower()

            if "weight_loss" in goal_lower or "lose_weight" in goal_lower:
                calories -= 500  # 500 cal deficit
                sugar_g = min(sugar_g, 25.0)
                sodium_mg = min(sodium_mg, 1500.0)

            elif "muscle" in goal_lower or "gain" in goal_lower:
                calories += 200  # Slight surplus
                protein_g = max(protein_g, weight_kg * 2.0 if weight_kg else 120.0)

            elif "diabetes" in goal_lower or "blood_sugar" in goal_lower:
                sugar_g = min(sugar_g, 25.0)
                carbs_g = min(carbs_g, 180.0)
                fiber_g = max(fiber_g, 35.0)

            elif "heart" in goal_lower or "cardiovascular" in goal_lower:
                sodium_mg = min(sodium_mg, 1500.0)
                fat_g = min(fat_g, 50.0)
                fiber_g = max(fiber_g, 35.0)

        return DailyTargets(
            calories=calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            sugar_g=sugar_g,
            sodium_mg=sodium_mg,
            fiber_g=fiber_g
        )

    @staticmethod
    def _calculate_bmr(
        age: int,
        gender: str,
        height_cm: float,
        weight_kg: float
    ) -> float:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation."""
        # BMR = 10*weight(kg) + 6.25*height(cm) - 5*age(years) + s
        # s = +5 for males, -161 for females
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age

        if gender and gender.lower() in ["male", "m"]:
            bmr += 5
        else:
            bmr -= 161

        return bmr


# Global profile store instance
profile_store = ProfileStore()
