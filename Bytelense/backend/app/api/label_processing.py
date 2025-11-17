"""
Label Image Processing API Endpoints

Handles Stage-2 backend processing of food label images:
- Receives preprocessed image from frontend
- Applies adaptive processing pipeline
- Runs OCR and returns results
"""

import logging
import base64
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from app.services.label_processing import LabelProcessor
from chandra.model import InferenceManager
from chandra.model.schema import BatchInputItem, BatchOutputItem
from app.services.ocr_single_image import SingleImageOCRManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/label", tags=["label-processing"])

# Global processor instances
_processor: LabelProcessor = None
_ocr_manager: InferenceManager = None
_single_ocr_manager: SingleImageOCRManager = None


def get_processor() -> LabelProcessor:
    """Get or create label processor instance."""
    global _processor
    if _processor is None:
        _processor = LabelProcessor(enable_sr=False)  # SR disabled for now
    return _processor


def get_ocr_manager() -> InferenceManager:
    """Get or create OCR manager instance."""
    global _ocr_manager
    if _ocr_manager is None:
        try:
            logger.info("Initializing ChandraOCR with HuggingFace backend...")
            _ocr_manager = InferenceManager(method="hf")
            logger.info("ChandraOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChandraOCR: {e}")
            raise
    return _ocr_manager


def get_single_ocr_manager() -> SingleImageOCRManager:
    """Get or create single image OCR manager instance."""
    global _single_ocr_manager
    if _single_ocr_manager is None:
        try:
            logger.info("Initializing Single Image ChandraOCR...")
            _single_ocr_manager = SingleImageOCRManager()
            logger.info("Single Image ChandraOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Single Image ChandraOCR: {e}")
            raise
    return _single_ocr_manager


# ==================== Request/Response Models ====================


class LabelProcessRequest(BaseModel):
    """Request to process a label image."""
    image_base64: str  # JPEG base64 with or without data URI prefix
    metadata: dict = {}  # Optional metadata from frontend


class QualityAnalysisResponse(BaseModel):
    """Image quality analysis response."""
    quality_tier: str  # "good", "fair", "poor"
    sharpness: float
    exposure_score: float
    saturation_mean: float
    dark_ratio: float
    clipped_ratio: float


class ProcessingStageResult(BaseModel):
    """Individual processing stage result."""
    stage_name: str
    duration_ms: float


class LabelProcessResponse(BaseModel):
    """Response from label processing."""
    status: str  # "success" or "error"
    enhanced_image_base64: str  # Processed image as base64
    quality_analysis: QualityAnalysisResponse
    stages_applied: list
    timings: dict
    total_processing_ms: float
    message: str = ""


class OCRResult(BaseModel):
    """Result from OCR processing."""
    markdown: str  # OCR text in markdown format
    html: str  # OCR text in HTML format
    raw: str  # Raw OCR output
    token_count: int  # Number of tokens processed
    error: bool  # Whether OCR encountered an error
    chunks: dict = {}  # Structured OCR chunks
    images: dict = {}  # Extracted images


class LabelProcessWithOCRResponse(BaseModel):
    """Response from label processing with OCR."""
    status: str  # "success" or "error"
    enhanced_image_base64: str  # Processed image as base64
    quality_analysis: QualityAnalysisResponse
    stages_applied: list
    timings: dict
    total_processing_ms: float
    ocr_result: Optional[OCRResult] = None
    ocr_time_ms: float = 0.0
    total_time_ms: float = 0.0  # Total including OCR
    message: str = ""


# ==================== Helper Functions ====================


def decode_base64_image(b64_str: str) -> np.ndarray:
    """
    Decode base64 image string to numpy array.

    Args:
        b64_str: Base64 string (with or without data URI prefix)

    Returns:
        OpenCV image (BGR) or None if invalid
    """
    try:
        # Remove data URI prefix if present
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]

        # Decode
        img_bytes = base64.b64decode(b64_str)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("cv2.imdecode returned None")

        return img
    except Exception as e:
        logger.error(f"Failed to decode base64 image: {e}")
        raise


def encode_image_to_base64(img: np.ndarray, quality: int = 85) -> str:
    """
    Encode numpy image to base64 JPEG.

    Args:
        img: OpenCV image (BGR)
        quality: JPEG quality (1-100)

    Returns:
        Base64 string with data URI prefix
    """
    _, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    b64 = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


# ==================== Endpoints ====================


@router.post("/process", response_model=LabelProcessResponse)
async def process_label_image(request: LabelProcessRequest) -> LabelProcessResponse:
    """
    Process a food label image with adaptive pipeline.

    Stage-2 backend processing:
    1. Decode and validate image
    2. Analyze quality
    3. Select processing tier (light/medium/heavy)
    4. Apply adaptive processing pipeline
    5. Return enhanced image + metadata

    Args:
        request: Label processing request with base64 image

    Returns:
        Processing result with enhanced image and analysis
    """
    import time

    try:
        # Decode image
        logger.info("Decoding image...")
        img = decode_base64_image(request.image_base64)

        if img is None or img.size == 0:
            raise HTTPException(status_code=400, detail="Invalid image data")

        logger.info(f"Image decoded: {img.shape}")

        # Get processor
        processor = get_processor()

        # Process with adaptive pipeline
        logger.info("Starting adaptive processing...")
        start_time = time.time()
        result = processor.process_adaptive(img)
        total_time = (time.time() - start_time) * 1000

        # Encode result
        enhanced_b64 = encode_image_to_base64(result.enhanced_image, quality=90)

        # Quality analysis response
        quality_response = QualityAnalysisResponse(
            quality_tier=result.quality_analysis.quality_tier,
            sharpness=float(result.quality_analysis.sharpness),
            exposure_score=float(result.quality_analysis.exposure_score),
            saturation_mean=float(result.quality_analysis.saturation_mean),
            dark_ratio=float(result.quality_analysis.dark_ratio),
            clipped_ratio=float(result.quality_analysis.clipped_ratio),
        )

        logger.info(
            f"Processing complete: quality={quality_response.quality_tier}, "
            f"stages={len(result.stages_applied)}, time={total_time:.0f}ms"
        )

        return LabelProcessResponse(
            status="success",
            enhanced_image_base64=enhanced_b64,
            quality_analysis=quality_response,
            stages_applied=result.stages_applied,
            timings=result.timings,
            total_processing_ms=total_time,
            message=f"Processing successful with {len(result.stages_applied)} stages"
        )

    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        return LabelProcessResponse(
            status="error",
            enhanced_image_base64="",
            quality_analysis=QualityAnalysisResponse(
                quality_tier="poor",
                sharpness=0.0,
                exposure_score=0.0,
                saturation_mean=0.0,
                dark_ratio=1.0,
                clipped_ratio=0.0,
            ),
            stages_applied=[],
            timings={},
            total_processing_ms=0.0,
            message=f"Processing failed: {str(e)}"
        )


@router.post("/analyze-quality")
async def analyze_quality(request: LabelProcessRequest) -> QualityAnalysisResponse:
    """
    Quick quality analysis without processing.

    Useful for frontend to determine if image should be reshot.

    Args:
        request: Image to analyze

    Returns:
        Quality metrics
    """
    try:
        img = decode_base64_image(request.image_base64)
        processor = get_processor()
        quality = processor.analyze_quality(img)

        return QualityAnalysisResponse(
            quality_tier=quality.quality_tier,
            sharpness=float(quality.sharpness),
            exposure_score=float(quality.exposure_score),
            saturation_mean=float(quality.saturation_mean),
            dark_ratio=float(quality.dark_ratio),
            clipped_ratio=float(quality.clipped_ratio),
        )

    except Exception as e:
        logger.error(f"Quality analysis failed: {e}")
        raise HTTPException(status_code=400, detail=f"Analysis failed: {str(e)}")


@router.post("/test-image")
async def test_with_file(file: UploadFile = File(...)):
    """
    Test processing with uploaded file.

    For testing via multipart/form-data instead of base64.

    Args:
        file: Image file upload

    Returns:
        Processing result
    """
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        processor = get_processor()
        result = processor.process_adaptive(img)

        enhanced_b64 = encode_image_to_base64(result.enhanced_image, quality=90)

        return {
            "status": "success",
            "enhanced_image_base64": enhanced_b64,
            "quality_tier": result.quality_analysis.quality_tier,
            "stages": result.stages_applied,
            "timings_ms": result.timings,
        }

    except Exception as e:
        logger.error(f"File processing failed: {e}")
        raise HTTPException(status_code=400, detail=f"Processing failed: {str(e)}")


@router.post("/process-with-ocr", response_model=LabelProcessWithOCRResponse)
async def process_label_with_ocr(request: LabelProcessRequest) -> LabelProcessWithOCRResponse:
    """
    Process a food label image and extract text with OCR.

    Full processing pipeline:
    1. Decode and validate image
    2. Analyze quality
    3. Apply adaptive image enhancement
    4. Run ChandraOCR on enhanced image
    5. Return enhanced image + OCR results

    Args:
        request: Label processing request with base64 image

    Returns:
        Processing result with enhanced image, quality analysis, and OCR text
    """
    import time

    overall_start = time.time()

    try:
        # Decode image
        logger.info("Decoding image for OCR processing...")
        img = decode_base64_image(request.image_base64)

        if img is None or img.size == 0:
            raise HTTPException(status_code=400, detail="Invalid image data")

        logger.info(f"Image decoded: {img.shape}")

        # Get processor
        processor = get_processor()

        # Process with adaptive pipeline
        logger.info("Starting adaptive image processing...")
        img_start = time.time()
        result = processor.process_adaptive(img)
        img_time = (time.time() - img_start) * 1000

        logger.info(
            f"Image processing complete: quality={result.quality_analysis.quality_tier}, "
            f"stages={len(result.stages_applied)}, time={img_time:.0f}ms"
        )

        # Encode result image
        enhanced_b64 = encode_image_to_base64(result.enhanced_image, quality=90)

        # Convert OpenCV image (BGR) to PIL Image (RGB) for OCR
        ocr_img_bgr = result.enhanced_image
        ocr_img_rgb = cv2.cvtColor(ocr_img_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(ocr_img_rgb)

        # Run OCR using memory-efficient single image processing
        logger.info("Starting ChandraOCR with single-image processing...")
        ocr_start = time.time()

        try:
            # Use the single image OCR manager which is more memory-efficient
            single_ocr_manager = get_single_ocr_manager()

            # Process single image directly
            ocr_output = single_ocr_manager.process_single_image(
                image=pil_img,
                prompt_type="ocr"
            )

            ocr_time = (time.time() - ocr_start) * 1000

            if not ocr_output.error:
                # Create a mock BatchOutputItem-like structure from the single result
                from chandra.output import parse_markdown, parse_html, parse_chunks, extract_images

                chunks = parse_chunks(ocr_output.raw, pil_img)
                images = extract_images(ocr_output.raw, chunks, pil_img)

                ocr_result = OCRResult(
                    markdown=parse_markdown(ocr_output.raw),
                    html=parse_html(ocr_output.raw),
                    raw=ocr_output.raw,
                    token_count=ocr_output.token_count,
                    error=ocr_output.error,
                    chunks=chunks if chunks else {},
                    images=images if images else {},
                )
                logger.info(
                    f"OCR complete: tokens={ocr_output.token_count}, error={ocr_output.error}, time={ocr_time:.0f}ms"
                )
            else:
                raise Exception("OCR processing failed - error flag set")

        except Exception as ocr_error:
            logger.error(f"Single-image OCR processing failed: {ocr_error}", exc_info=True)
            logger.info("Falling back to original batch OCR processing...")

            # Clear CUDA cache to free memory before fallback
            try:
                import torch
                torch.cuda.empty_cache()
            except:
                pass  # torch may not be available

            # Fallback to original batch processing method
            try:
                ocr_manager = get_ocr_manager()
                batch_input = [BatchInputItem(image=pil_img, prompt=None, prompt_type="ocr")]
                batch_output = ocr_manager.generate(batch_input)
                ocr_time = (time.time() - ocr_start) * 1000

                if batch_output and len(batch_output) > 0:
                    ocr_out = batch_output[0]
                    ocr_result = OCRResult(
                        markdown=ocr_out.markdown,
                        html=ocr_out.html,
                        raw=ocr_out.raw,
                        token_count=ocr_out.token_count,
                        error=ocr_out.error,
                        chunks=ocr_out.chunks if ocr_out.chunks else {},
                        images=ocr_out.images if ocr_out.images else {},
                    )
                    logger.info(
                        f"Fallback OCR complete: tokens={ocr_out.token_count}, error={ocr_out.error}, time={ocr_time:.0f}ms"
                    )
                else:
                    raise Exception("Fallback OCR returned empty output")

            except Exception as fallback_error:
                logger.error(f"Fallback OCR processing also failed: {fallback_error}", exc_info=True)
                # Clear CUDA cache again
                try:
                    import torch
                    torch.cuda.empty_cache()
                except:
                    pass  # torch may not be available

                ocr_result = OCRResult(
                    markdown="",
                    html="",
                    raw="",
                    token_count=0,
                    error=True,
                    chunks={},
                    images={},
                )
                ocr_time = (time.time() - ocr_start) * 1000

        # Quality analysis response
        quality_response = QualityAnalysisResponse(
            quality_tier=result.quality_analysis.quality_tier,
            sharpness=float(result.quality_analysis.sharpness),
            exposure_score=float(result.quality_analysis.exposure_score),
            saturation_mean=float(result.quality_analysis.saturation_mean),
            dark_ratio=float(result.quality_analysis.dark_ratio),
            clipped_ratio=float(result.quality_analysis.clipped_ratio),
        )

        total_time = (time.time() - overall_start) * 1000

        logger.info(
            f"Full pipeline complete: img_time={img_time:.0f}ms, "
            f"ocr_time={ocr_time:.0f}ms, total={total_time:.0f}ms"
        )

        return LabelProcessWithOCRResponse(
            status="success",
            enhanced_image_base64=enhanced_b64,
            quality_analysis=quality_response,
            stages_applied=result.stages_applied,
            timings=result.timings,
            total_processing_ms=img_time,
            ocr_result=ocr_result,
            ocr_time_ms=ocr_time,
            total_time_ms=total_time,
            message=f"Processing and OCR complete: {len(result.stages_applied)} img stages, "
                    f"tokens={ocr_result.token_count if ocr_result else 0}"
        )

    except Exception as e:
        logger.error(f"OCR processing error: {e}", exc_info=True)
        total_time = (time.time() - overall_start) * 1000

        return LabelProcessWithOCRResponse(
            status="error",
            enhanced_image_base64="",
            quality_analysis=QualityAnalysisResponse(
                quality_tier="poor",
                sharpness=0.0,
                exposure_score=0.0,
                saturation_mean=0.0,
                dark_ratio=1.0,
                clipped_ratio=0.0,
            ),
            stages_applied=[],
            timings={},
            total_processing_ms=0.0,
            ocr_result=None,
            ocr_time_ms=0.0,
            total_time_ms=total_time,
            message=f"Processing failed: {str(e)}"
        )


@router.get("/health")
async def label_processor_health():
    """Health check for label processing service."""
    try:
        processor = get_processor()
        ocr_status = "not_initialized"
        try:
            _ = get_ocr_manager()
            ocr_status = "ready"
        except Exception as e:
            ocr_status = f"error: {str(e)}"

        return {
            "status": "healthy",
            "processor_ready": processor is not None,
            "ocr_status": ocr_status,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
