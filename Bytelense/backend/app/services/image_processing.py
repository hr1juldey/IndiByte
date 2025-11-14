"""Image processing service for barcode detection and OCR."""

import io
import logging
import time
from typing import Optional, Tuple
from PIL import Image
import cv2
import numpy as np

from app.models.schemas import ImageProcessingResult

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Handles image preprocessing, barcode detection, and OCR."""

    def __init__(self):
        """Initialize image processor."""
        self.max_dimension = 1920  # Max width or height
        logger.info("Image processor initialized")

    async def process(self, image_bytes: bytes) -> ImageProcessingResult:
        """
        Process image: detect barcode or extract text via OCR.

        Args:
            image_bytes: Raw image bytes

        Returns:
            ImageProcessingResult with barcode or OCR text
        """
        start_time = time.time()

        try:
            # Preprocess image
            image = self._preprocess(image_bytes)

            # Try barcode detection first
            barcode = self._detect_barcode(image)

            if barcode:
                processing_time = int((time.time() - start_time) * 1000)
                return ImageProcessingResult(
                    barcode=barcode,
                    ocr_text=None,
                    confidence=0.95,
                    method_used="barcode",
                    processing_time_ms=processing_time
                )

            # Fallback to OCR
            ocr_text, confidence = await self._extract_text_ocr(image)

            processing_time = int((time.time() - start_time) * 1000)

            return ImageProcessingResult(
                barcode=None,
                ocr_text=ocr_text,
                confidence=confidence,
                method_used="ocr",
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"Image processing error: {e}")
            processing_time = int((time.time() - start_time) * 1000)
            return ImageProcessingResult(
                barcode=None,
                ocr_text=None,
                confidence=0.0,
                method_used="ocr",
                processing_time_ms=processing_time
            )

    def _preprocess(self, image_bytes: bytes) -> np.ndarray:
        """
        Preprocess image: resize, denoise, enhance contrast.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Preprocessed image as numpy array
        """
        # Load image with Pillow
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Resize if too large
        width, height = image.size
        max_dim = max(width, height)

        if max_dim > self.max_dimension:
            scale = self.max_dimension / max_dim
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert to numpy array for OpenCV
        image_np = np.array(image)

        # Apply denoising
        image_np = cv2.fastNlMeansDenoisingColored(image_np, None, 10, 10, 7, 21)

        logger.debug(f"Preprocessed image: {image_np.shape}")
        return image_np

    def _detect_barcode(self, image: np.ndarray) -> Optional[str]:
        """
        Detect and decode barcode using pyzbar.

        Args:
            image: Preprocessed image

        Returns:
            Barcode string if detected, None otherwise
        """
        try:
            from pyzbar import pyzbar
        except ImportError:
            logger.warning("pyzbar not installed, skipping barcode detection")
            return None

        try:
            # Convert to grayscale for better barcode detection
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11, 2
            )

            # Detect barcodes
            barcodes = pyzbar.decode(thresh)

            if barcodes:
                barcode_data = barcodes[0].data.decode("utf-8")
                logger.info(f"Barcode detected: {barcode_data}")
                return barcode_data

            # Try original image if thresholded version failed
            barcodes = pyzbar.decode(gray)
            if barcodes:
                barcode_data = barcodes[0].data.decode("utf-8")
                logger.info(f"Barcode detected (2nd attempt): {barcode_data}")
                return barcode_data

            logger.debug("No barcode detected")
            return None

        except Exception as e:
            logger.error(f"Barcode detection error: {e}")
            return None

    async def _extract_text_ocr(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extract text using Chandra OCR.

        Args:
            image: Preprocessed image

        Returns:
            Tuple of (extracted text, confidence score)
        """
        try:
            from transformers import AutoModel, AutoTokenizer
            from chandra_ocr import ChandraOCR

            # Initialize Chandra OCR (consider caching this)
            ocr = ChandraOCR()

            # Convert numpy array to PIL Image
            pil_image = Image.fromarray(image)

            # Extract text
            result = ocr.extract(pil_image)

            if result and "text" in result:
                text = result["text"].strip()
                confidence = result.get("confidence", 0.7)
                logger.info(f"OCR extracted: {text[:50]}... (confidence: {confidence})")
                return text, confidence

            logger.warning("OCR returned no text")
            return "", 0.0

        except ImportError:
            logger.error("chandra-ocr not installed")
            return "", 0.0
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return "", 0.0


# Global image processor instance
image_processor = ImageProcessor()
