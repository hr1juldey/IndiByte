"""WebSocket scanning handler."""

import logging
import base64
import uuid
from datetime import datetime

from app.main import sio
from app.models.schemas import (
    StartScanEvent,
    ScanProgressEvent,
    ScanCompleteEvent,
    ScanErrorEvent,
    ScanResult
)
from app.core.profile_store import profile_store
from app.services.image_processing import image_processor
from app.services.nutrition_api import nutrition_aggregator
from app.services.scoring import scoring_service
from app.services.ui_generator import ui_schema_builder

logger = logging.getLogger(__name__)


@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    logger.info(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {sid}")


@sio.event
async def start_scan(sid, data):
    """
    Handle scan request from client.

    This orchestrates the entire scanning pipeline:
    1. Image processing (barcode/OCR)
    2. Nutrition data retrieval
    3. AI scoring
    4. UI generation
    5. Response

    Args:
        sid: Socket.IO session ID
        data: Scan request data
    """
    scan_id = str(uuid.uuid4())
    logger.info(f"[{scan_id}] Scan started for user: {data.get('user')}")

    try:
        # Parse request
        request = StartScanEvent(**data)

        # ====================================================================
        # STAGE 1: Image Processing
        # ====================================================================
        await sio.emit("scan_progress", ScanProgressEvent(
            stage="detecting_barcode",
            progress=10,
            message="Analyzing image..."
        ).model_dump(), room=sid)

        try:
            image_bytes = base64.b64decode(request.image_data)
        except Exception as e:
            logger.error(f"[{scan_id}] Base64 decode error: {e}")
            await _emit_error(sid, "detecting_barcode", "Invalid image data", "IMAGE_DECODE_ERROR")
            return

        image_result = await image_processor.process(image_bytes)

        if not image_result.barcode and not image_result.ocr_text:
            await _emit_error(
                sid,
                "detecting_barcode",
                "Could not detect barcode or extract text",
                "IMAGE_PROCESSING_FAILED",
                "Try better lighting or a clearer image"
            )
            return

        logger.info(f"[{scan_id}] Image processed: barcode={image_result.barcode}, ocr={bool(image_result.ocr_text)}")

        # ====================================================================
        # STAGE 2: Nutrition Data Retrieval
        # ====================================================================
        await sio.emit("scan_progress", ScanProgressEvent(
            stage="fetching_nutrition",
            progress=30,
            message="Looking up nutrition data..."
        ).model_dump(), room=sid)

        nutrition_data = await nutrition_aggregator.get_nutrition_data(
            barcode=image_result.barcode,
            product_name=image_result.ocr_text
        )

        if not nutrition_data:
            await _emit_error(
                sid,
                "fetching_nutrition",
                "Product not found in database",
                "PRODUCT_NOT_FOUND",
                "Try scanning the barcode again or manual entry"
            )
            return

        logger.info(f"[{scan_id}] Nutrition data retrieved: {nutrition_data.product_name}")

        # ====================================================================
        # STAGE 3: Load User Profile
        # ====================================================================
        await sio.emit("scan_progress", ScanProgressEvent(
            stage="loading_profile",
            progress=50,
            message="Loading your profile..."
        ).model_dump(), room=sid)

        user_profile = await profile_store.load(request.user)

        if not user_profile:
            await _emit_error(
                sid,
                "loading_profile",
                "User profile not found",
                "PROFILE_NOT_FOUND",
                "Please complete onboarding first"
            )
            return

        # ====================================================================
        # STAGE 4: AI Scoring
        # ====================================================================
        await sio.emit("scan_progress", ScanProgressEvent(
            stage="analyzing",
            progress=60,
            message="Analyzing nutrition against your goals..."
        ).model_dump(), room=sid)

        scoring_result = await scoring_service.score(nutrition_data, user_profile)

        logger.info(f"[{scan_id}] Scoring complete: score={scoring_result.score}, verdict={scoring_result.verdict}")

        # ====================================================================
        # STAGE 5: UI Generation
        # ====================================================================
        await sio.emit("scan_progress", ScanProgressEvent(
            stage="generating_ui",
            progress=85,
            message="Preparing your personalized verdict..."
        ).model_dump(), room=sid)

        ui_schema = ui_schema_builder.generate(scoring_result)

        # ====================================================================
        # STAGE 6: Send Complete Result
        # ====================================================================
        scan_result = ScanResult(
            scan_id=scan_id,
            user_name=request.user,
            timestamp=datetime.now(),
            image_processing=image_result,
            nutrition_data=nutrition_data,
            scoring=scoring_result,
            ui_schema=ui_schema
        )

        await sio.emit("scan_complete", ScanCompleteEvent(
            result=scan_result
        ).model_dump(), room=sid)

        logger.info(f"[{scan_id}] Scan complete")

    except Exception as e:
        logger.error(f"[{scan_id}] Scan error: {e}", exc_info=True)
        await _emit_error(
            sid,
            "unknown",
            "An unexpected error occurred",
            "INTERNAL_ERROR",
            "Please try again"
        )


async def _emit_error(
    sid: str,
    stage: str,
    error: str,
    error_code: str,
    retry_suggestion: str = None
):
    """Helper to emit scan error."""
    await sio.emit("scan_error", ScanErrorEvent(
        stage=stage,
        error=error,
        error_code=error_code,
        retry_suggestion=retry_suggestion
    ).model_dump(), room=sid)
