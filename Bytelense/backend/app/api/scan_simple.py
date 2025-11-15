"""
Simplified WebSocket scan handler for testing.

This module provides a minimal scan flow that returns mock data without
requiring full OCR, LLM, or search integrations. Use this for:
- Frontend development and testing
- Quick backend verification
- Integration testing without external dependencies

To use: Comment out scan.py imports in main.py and import this instead.
"""

import logging
import asyncio
import uuid
from datetime import datetime

from app.main import sio
from app.models.schemas import (
    ScanRequest,
    ScanProgressEvent,
    ScanErrorEvent,
    DetailedAssessment,
    CitationSource
)

logger = logging.getLogger(__name__)


@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    logger.info(f"Client connected: {sid}")
    await sio.emit("connected", {"message": "Connected to Bytelense server"}, room=sid)


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {sid}")


@sio.event
async def start_scan(sid, data):
    """
    Simplified scan handler that returns mock data.

    Emits progress updates through 5 stages, then returns a mock DetailedAssessment.
    No actual OCR, LLM, or search operations are performed.

    Args:
        sid: Socket.IO session ID
        data: Scan request data (user_name, image_base64, source)
    """
    scan_id = str(uuid.uuid4())
    logger.info(f"[SIMPLE SCAN] {scan_id} started for {data.get('user_name')}")

    try:
        # Validate request
        try:
            request = ScanRequest(**data)
        except Exception as e:
            logger.error(f"[{scan_id}] Invalid request: {e}")
            await _emit_error(
                sid, scan_id, "image_processing",
                "INVALID_REQUEST",
                "Invalid scan request format"
            )
            return

        # Stage 1: Image Processing
        await sio.emit("scan_progress", ScanProgressEvent(
            scan_id=scan_id,
            stage="image_processing",
            stage_number=1,
            total_stages=5,
            message="Analyzing image...",
            progress=0.2
        ).model_dump(), room=sid)
        await asyncio.sleep(0.5)  # Simulate processing

        # Stage 2: Nutrition Retrieval
        await sio.emit("scan_progress", ScanProgressEvent(
            scan_id=scan_id,
            stage="nutrition_retrieval",
            stage_number=2,
            total_stages=5,
            message="Looking up nutrition data...",
            progress=0.4
        ).model_dump(), room=sid)
        await asyncio.sleep(0.5)

        # Stage 3: Profile Loading
        await sio.emit("scan_progress", ScanProgressEvent(
            scan_id=scan_id,
            stage="profile_loading",
            stage_number=3,
            total_stages=5,
            message="Loading your profile...",
            progress=0.6
        ).model_dump(), room=sid)
        await asyncio.sleep(0.3)

        # Stage 4: Scoring
        await sio.emit("scan_progress", ScanProgressEvent(
            scan_id=scan_id,
            stage="scoring",
            stage_number=4,
            total_stages=5,
            message="Analyzing nutrition against your goals...",
            progress=0.8
        ).model_dump(), room=sid)
        await asyncio.sleep(0.5)

        # Stage 5: Assessment Generation
        await sio.emit("scan_progress", ScanProgressEvent(
            scan_id=scan_id,
            stage="assessment_generation",
            stage_number=5,
            total_stages=5,
            message="Preparing your personalized verdict...",
            progress=0.95
        ).model_dump(), room=sid)
        await asyncio.sleep(0.3)

        # Create mock DetailedAssessment
        assessment = DetailedAssessment(
            scan_id=scan_id,
            timestamp=datetime.utcnow(),
            product_name="Lay's Classic Potato Chips",
            final_score=6.5,
            verdict="moderate",
            verdict_emoji="🟡",
            base_score=5.5,
            context_adjustment="Your goal is weight loss, so high-calorie snacks receive a penalty",
            time_multiplier=0.95,
            highlights=[
                "Good source of quick energy",
                "Portable and convenient",
                "No artificial preservatives listed"
            ],
            warnings=[
                "High in sodium (350mg per 100g - 15% of daily limit)",
                "High in saturated fat (2.5g per 100g)",
                "Low nutritional density (mostly empty calories)",
                "Portion control is critical (easy to overconsume)"
            ],
            allergen_alerts=[],
            moderation_message="Okay in moderation (1 serving = ~15 chips). Consider as an occasional treat rather than daily snack.",
            timing_recommendation="Best consumed during high-activity periods (post-workout, during sports). Avoid as late-night snack.",
            reasoning_steps=[
                "Analyzed macronutrient breakdown: 10g fat, 15g carbs, 2g protein per serving",
                "Compared sodium content against daily target (2000mg) - this serving provides 18%",
                "Evaluated ingredient quality: potatoes, oil, salt - minimal processing",
                "Assessed alignment with weight loss goal: High calorie density conflicts with goal",
                "Applied time-of-day penalty: Evening consumption (less activity to burn calories)",
                "Generated moderation guidelines based on portion size and frequency"
            ],
            sources=[
                CitationSource(
                    url="https://world.openfoodfacts.org/product/0028400047388",
                    title="Lay's Classic Potato Chips - OpenFoodFacts",
                    snippet="Nutrition facts and ingredients for Lay's Classic",
                    source_type="database"
                ),
                CitationSource(
                    url="https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/sodium",
                    title="American Heart Association - Sodium Guidelines",
                    snippet="Recommended sodium intake: <2,300mg/day, ideal <1,500mg/day",
                    source_type="guidelines"
                ),
                CitationSource(
                    url="https://www.healthline.com/nutrition/chips-and-health",
                    title="Healthline - Are Potato Chips Healthy?",
                    snippet="Analysis of potato chips: nutrition, health effects, and better alternatives",
                    source_type="research"
                )
            ],
            alternative_products=[
                "Air-popped popcorn (lower calorie density)",
                "Baked vegetable chips (lower fat)",
                "Rice cakes with hummus (more protein)",
                "Roasted chickpeas (higher fiber and protein)"
            ],
            nutrition_snapshot={
                "calories": 536,
                "protein_g": 6.7,
                "carbs_g": 53.0,
                "fat_g": 34.0,
                "fiber_g": 4.5,
                "sodium_mg": 525,
                "sugar_g": 0.4,
                "serving_size_g": 100
            }
        )

        # Emit complete event
        await sio.emit("scan_complete", {
            "scan_id": scan_id,
            "detailed_assessment": assessment.model_dump(mode='json')
        }, room=sid)

        logger.info(f"[SIMPLE SCAN] {scan_id} completed successfully")

    except Exception as e:
        logger.error(f"[SIMPLE SCAN] {scan_id} error: {e}", exc_info=True)
        await _emit_error(
            sid, scan_id, "unknown",
            "INTERNAL_ERROR",
            "An unexpected error occurred"
        )


async def _emit_error(
    sid: str,
    scan_id: str,
    stage: str,
    error_code: str,
    message: str,
    retry_suggestions: list = None
):
    """Helper to emit scan error."""
    await sio.emit("scan_error", ScanErrorEvent(
        scan_id=scan_id,
        error=error_code,
        message=message,
        stage=stage,
        retry_suggestions=retry_suggestions or ["Try again with a clearer image"],
        recoverable=True
    ).model_dump(), room=sid)
