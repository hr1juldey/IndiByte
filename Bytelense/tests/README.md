# DSPy Food Label OCR Implementation

This project implements a food label OCR system using DSPy with multimodal capabilities. Through extensive testing, we discovered important insights about DSPy's interaction with vision models.

## Architecture

The implementation consists of:

1. **LiteLLM OCR Module**: Handles the image-to-text extraction using Ollama qwen3-vl:8b
2. **DSPy Text Processing Modules**:
   - OCRModule: Processes OCR text
   - NutritionalInfoExtractor: Extracts nutritional data
   - ProductInfoExtractor: Extracts product details
   - QualityAssessor: Evaluates OCR quality

## Key Findings

Through testing, we found:

- DSPy's multimodal support can be inconsistent with Ollama's vision models
- LiteLLM provides more reliable access to Ollama's vision capabilities
- The approach of separating vision (LiteLLM) and text processing (DSPy) is most effective

## Usage

Run the final solution:
```bash
python final_ocr_solution.py
```

## Files

- `final_ocr_solution.py` - The main implementation combining LiteLLM for OCR with DSPy for text processing
- `test_dspy_file_url.py` - Working test showing DSPy image capabilities
- `test_comparison.py` - Comparison between DSPy and LiteLLM approaches
- `debug_test.py` - Basic functionality test

## Results

The system successfully extracts and processes food label information, combining the reliability of LiteLLM for image processing with DSPy's structured text processing capabilities.