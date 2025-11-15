"""
Health Modeling Engine - Implements LLD Section 4

Calculates BMI, BMR, TDEE, and personalized daily targets based on user profile.
Follows Mifflin-St Jeor formula for BMR and activity-based TDEE multipliers.
"""

import logging
from typing import Dict, Tuple
from app.models.schemas import (
    Demographics,
    LifestyleHabits,
    HealthGoals,
    HealthMetrics,
    DailyTargets
)

logger = logging.getLogger(__name__)


class HealthModelingEngine:
    """Calculates health metrics and personalized targets."""

    # BMI Categories (kg/m²)
    BMI_CATEGORIES = {
        "underweight": (0, 18.5),
        "normal": (18.5, 25.0),
        "overweight": (25.0, 30.0),
        "obese": (30.0, float('inf'))
    }

    # Activity multipliers for TDEE
    WORK_STYLE_MULTIPLIER = {
        "desk_job": 1.2,
        "light_activity": 1.375,
        "physical_job": 1.55
    }

    EXERCISE_BONUS = {
        "rarely": 0.0,
        "1-2_times_week": 0.05,
        "3-4_times_week": 0.1,
        "5_times_week": 0.15,
        "daily": 0.2
    }

    COMMUTE_BONUS = {
        "car": 0.0,
        "public_transport": 0.02,
        "bike": 0.08,
        "walk": 0.05
    }

    def __init__(self):
        """Initialize health modeling engine."""
        logger.info("HealthModelingEngine initialized")

    async def calculate_metrics(
        self,
        demographics: Demographics,
        lifestyle: LifestyleHabits,
        goals: HealthGoals
    ) -> Tuple[HealthMetrics, DailyTargets]:
        """
        Calculate complete health metrics and daily targets.

        Args:
            demographics: User demographic data
            lifestyle: User lifestyle habits
            goals: User health goals

        Returns:
            Tuple of (HealthMetrics, DailyTargets)
        """
        logger.info(f"Calculating metrics for age={demographics.age}, gender={demographics.gender}")

        # Calculate BMI
        bmi = self._calculate_bmi(demographics.height_cm, demographics.weight_kg)
        bmi_category = self._get_bmi_category(bmi)

        # Calculate BMR (Mifflin-St Jeor)
        bmr = self._calculate_bmr_mifflin(
            demographics.weight_kg,
            demographics.height_cm,
            demographics.age,
            demographics.gender
        )

        # Calculate TDEE
        activity_multiplier = self._calculate_activity_multiplier(lifestyle)
        tdee = bmr * activity_multiplier

        # Adjust for weight goals
        target_calories = self._adjust_calories_for_goal(tdee, goals.target_weight_kg, demographics.weight_kg)

        # Calculate health risks
        health_risks = self._assess_health_risks(bmi_category, lifestyle)

        # Build HealthMetrics
        health_metrics = HealthMetrics(
            bmi=round(bmi, 2),
            bmi_category=bmi_category,
            bmr=round(bmr, 1),
            tdee=round(tdee, 1),
            target_calories=round(target_calories, 1),
            health_risks=health_risks
        )

        # Calculate daily targets
        daily_targets = self._calculate_daily_targets(
            target_calories,
            goals,
            demographics.gender,
            lifestyle
        )

        logger.info(f"Calculated: BMI={bmi:.2f}, TDEE={tdee:.0f}, Target={target_calories:.0f}")
        return health_metrics, daily_targets

    def _calculate_bmi(self, height_cm: float, weight_kg: float) -> float:
        """Calculate Body Mass Index."""
        height_m = height_cm / 100
        return weight_kg / (height_m ** 2)

    def _get_bmi_category(self, bmi: float) -> str:
        """Classify BMI into category."""
        for category, (low, high) in self.BMI_CATEGORIES.items():
            if low <= bmi < high:
                return category
        return "obese"

    def _calculate_bmr_mifflin(
        self,
        weight_kg: float,
        height_cm: float,
        age: int,
        gender: str
    ) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor formula.

        Male: BMR = (10 × weight) + (6.25 × height) - (5 × age) + 5
        Female: BMR = (10 × weight) + (6.25 × height) - (5 × age) - 161
        """
        base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)

        if gender == "male":
            return base + 5
        elif gender == "female":
            return base - 161
        else:  # other
            return base - 78  # Average of male and female

    def _calculate_activity_multiplier(self, lifestyle: LifestyleHabits) -> float:
        """
        Calculate total activity multiplier for TDEE.

        Combines work style, exercise frequency, and commute type.
        """
        base = self.WORK_STYLE_MULTIPLIER[lifestyle.work_style]
        exercise_bonus = self.EXERCISE_BONUS[lifestyle.exercise_frequency]
        commute_bonus = self.COMMUTE_BONUS[lifestyle.commute_type]

        # Penalties for poor habits
        penalties = 0.0
        if lifestyle.sleep_hours < 6:
            penalties += 0.05  # Poor sleep reduces metabolic efficiency
        if lifestyle.smoking == "yes":
            penalties += 0.03  # Smoking slightly increases metabolism (but terrible for health)

        total = base + exercise_bonus + commute_bonus - penalties
        return max(1.2, min(2.5, total))  # Clamp between 1.2 and 2.5

    def _adjust_calories_for_goal(
        self,
        tdee: float,
        target_weight: float,
        current_weight: float
    ) -> float:
        """
        Adjust calorie target based on weight goals.

        - Weight loss: -500 kcal/day (1 lb/week)
        - Weight gain: +300 kcal/day
        - Maintenance: TDEE
        """
        if target_weight < current_weight:
            # Weight loss: 500 kcal deficit
            return tdee - 500
        elif target_weight > current_weight:
            # Weight gain: 300 kcal surplus
            return tdee + 300
        else:
            # Maintenance
            return tdee

    def _assess_health_risks(self, bmi_category: str, lifestyle: LifestyleHabits) -> list:
        """Identify health risks based on metrics and lifestyle."""
        risks = []

        # BMI risks
        if bmi_category == "underweight":
            risks.append("underweight_malnutrition_risk")
        elif bmi_category == "overweight":
            risks.append("overweight_cardiovascular_risk")
        elif bmi_category == "obese":
            risks.append("obesity_multiple_disease_risk")

        # Lifestyle risks
        if lifestyle.sleep_hours < 6:
            risks.append("insufficient_sleep")
        if lifestyle.smoking == "yes":
            risks.append("smoking_health_hazard")
        if lifestyle.alcohol == "heavy":
            risks.append("excessive_alcohol_consumption")
        if lifestyle.exercise_frequency == "rarely":
            risks.append("sedentary_lifestyle")

        return risks

    def _calculate_daily_targets(
        self,
        target_calories: float,
        goals: HealthGoals,
        gender: str,
        lifestyle: LifestyleHabits
    ) -> DailyTargets:
        """
        Calculate personalized daily nutrient targets.

        Based on calorie target, health goals, and nutritional science.
        """
        # Protein: 0.8-2.0g per kg body weight depending on goal
        if goals.fitness_goal == "muscle_gain":
            protein_g = target_calories * 0.30 / 4  # 30% of calories, 4 kcal/g
        else:
            protein_g = target_calories * 0.20 / 4  # 20% of calories

        # Carbs: 45-65% of calories
        if goals.fitness_goal == "weight_loss":
            carbs_g = target_calories * 0.40 / 4  # Lower carbs for weight loss
        else:
            carbs_g = target_calories * 0.50 / 4  # Moderate carbs

        # Fat: 20-35% of calories
        fat_g = target_calories * 0.25 / 9  # 25% of calories, 9 kcal/g

        # Fiber: 25-38g per day
        fiber_g = 30.0 if gender == "male" else 25.0

        # Sugar: <10% of calories (WHO guideline)
        sugar_g = target_calories * 0.10 / 4

        # Sodium: <2300mg per day (FDA guideline)
        sodium_mg = 2000.0

        return DailyTargets(
            calories=round(target_calories, 1),
            protein_g=round(protein_g, 1),
            carbs_g=round(carbs_g, 1),
            fat_g=round(fat_g, 1),
            fiber_g=round(fiber_g, 1),
            sugar_g=round(sugar_g, 1),
            sodium_mg=round(sodium_mg, 1)
        )


# Global engine instance
health_modeling_engine = HealthModelingEngine()
