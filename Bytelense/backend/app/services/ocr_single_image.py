"""
Single Image OCR Processing for Memory-Constrained Environments

This module provides an alternative OCR implementation that processes
single images more efficiently, suitable for constrained environments
like RTX 3060 with 12GB VRAM.
"""

from typing import Optional
import logging
import torch
from PIL import Image

from chandra.model.hf import process_batch_element, load_model
from chandra.model.schema import GenerationResult
from chandra.prompts import PROMPT_MAPPING
from chandra.model.util import scale_to_fit
from qwen_vl_utils import process_vision_info

logger = logging.getLogger(__name__)


class SingleImageOCRManager:
    """
    OCR Manager that processes single images efficiently to reduce memory usage.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_path = model_path or "datalab-to/chandra"  # Default model from Chandra settings
        self._load_model()
    
    def _load_model(self):
        """Load the model with memory-efficient settings."""
        try:
            logger.info("Loading model with memory-efficient settings...")
            
            # Set memory-efficient parameters
            device_map = "auto"
            torch_dtype = torch.float16  # Use FP16 to reduce memory
            
            # Load model with optimized settings
            from transformers import Qwen3VLForConditionalGeneration, Qwen3VLProcessor
            
            self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                self.model_path,
                torch_dtype=torch_dtype,
                device_map=device_map,
                low_cpu_mem_usage=True,
                attn_implementation="flash_attention_2" if torch.cuda.is_available() else None,
            )
            
            self.model = self.model.eval()
            
            # Load processor
            self.processor = Qwen3VLProcessor.from_pretrained(self.model_path)
            
            logger.info("Model loaded successfully with memory-efficient settings")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            # Fallback to CPU if CUDA fails
            try:
                logger.info("Attempting to load model on CPU...")
                from transformers import Qwen3VLForConditionalGeneration, Qwen3VLProcessor
                
                self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float16,  # Use FP16 even on CPU
                    device_map="cpu",
                    low_cpu_mem_usage=True,
                )
                
                self.model = self.model.eval()
                self.processor = Qwen3VLProcessor.from_pretrained(self.model_path)
                
                logger.info("Model loaded successfully on CPU")
            except Exception as cpu_error:
                logger.error(f"Failed to load model on CPU: {cpu_error}")
                raise
    
    def process_single_image(
        self, 
        image: Image.Image, 
        prompt_type: str = "ocr",
        max_output_tokens: int = 2048
    ) -> GenerationResult:
        """
        Process a single image efficiently.
        
        Args:
            image: PIL Image to process
            prompt_type: Type of prompt to use (default: "ocr")
            max_output_tokens: Maximum tokens to generate
            
        Returns:
            GenerationResult with the OCR output
        """
        try:
            # Clear cache before processing
            torch.cuda.empty_cache()
            
            # Scale image to fit memory constraints
            scaled_image = scale_to_fit(image)
            
            # Get the appropriate prompt
            prompt = PROMPT_MAPPING.get(prompt_type, PROMPT_MAPPING["ocr"])
            
            # Create message for single image
            content = []
            content.append({"type": "image", "image": scaled_image})
            content.append({"type": "text", "text": prompt})
            message = {"role": "user", "content": content}
            
            # Apply chat template
            text = self.processor.apply_chat_template(
                [message], tokenize=False, add_generation_prompt=True
            )
            
            # Process vision info (image)
            image_inputs, _ = process_vision_info([message])
            
            # Prepare inputs
            inputs = self.processor(
                text=[text],  # Wrap in list for batch processing
                images=image_inputs,
                padding=True,
                return_tensors="pt",
            )
            
            # Move to appropriate device
            device = next(self.model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Generate output
            with torch.inference_mode():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_output_tokens,
                    do_sample=False,
                    pad_token_id=self.processor.tokenizer.eos_token_id,
                )
            
            # Extract the generated text
            generated_ids_trimmed = generated_ids[0][len(inputs["input_ids"][0]):]
            output_text = self.processor.batch_decode(
                [generated_ids_trimmed],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]
            
            # Clean up memory
            del inputs
            del generated_ids
            del generated_ids_trimmed
            torch.cuda.empty_cache()
            
            return GenerationResult(
                raw=output_text,
                token_count=len(generated_ids_trimmed),
                error=False
            )
            
        except Exception as e:
            logger.error(f"Error processing single image: {e}")
            
            # Clean up on error
            torch.cuda.empty_cache()
            
            return GenerationResult(
                raw="",
                token_count=0,
                error=True
            )