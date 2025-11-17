# End-to-End Testing for Bytelense Food Label Scanner

This document outlines the end-to-end testing procedures for the Bytelense food label scanning system, verifying the complete flow from image capture to OCR results.

## Test Objectives

- Verify the entire flow from frontend capture to backend OCR processing
- Test the integration between frontend burst capture and backend image processing
- Validate OCR accuracy and performance on real food labels
- Ensure UI properly displays processed images and OCR results

## Test Environment

- Backend running on `http://localhost:8000`
- Frontend with camera access capabilities
- Real food label images in `data/food_labels/`
- Chrome/Firefox browser with camera permissions

## Test Scenarios

### Scenario 1: Standard Food Label Processing

1. Open the frontend scan page
2. Allow camera permissions
3. Position a standard food label (clear text, good lighting) in view
4. Capture image using burst capture
5. Verify the image is sent to the `/api/label/process-with-ocr` endpoint
6. Verify the backend returns success response with enhanced image and OCR text
7. Verify OCR results are displayed in the frontend UI

**Expected Results:**
- Image captured successfully
- Backend responds with status: "success"
- Enhanced image returned
- OCR extracts nutritional information accurately (>85% accuracy)
- OCR response time under 5 seconds

### Scenario 2: Poor Quality Label Processing

1. Use a food label with poor contrast, glare, or blur
2. Follow same capture and processing steps as Scenario 1
3. Verify adaptive processing pipeline selection

**Expected Results:**
- Backend identifies image as "poor" quality
- Appropriate processing pipeline applied (more intensive processing)
- OCR still returns results, possibly with lower accuracy
- Processing time may be longer than standard labels

### Scenario 3: Burst Capture Optimization

1. Use burst capture feature (takes 5 frames rapidly)
2. Simulate slight hand movement between captures
3. Verify fusion algorithm creates optimized image
4. Compare OCR results with single-frame capture

**Expected Results:**
- Multiple frames captured rapidly
- Fused image has improved clarity over individual frames
- OCR accuracy improved compared to single-frame capture
- Processing time remains acceptable

### Scenario 4: Error Handling

1. Try with an invalid image format
2. Test with no internet connection
3. Verify proper error messages are displayed

**Expected Results:**
- Appropriate error messages shown to user
- UI gracefully handles errors
- No crashes or unhandled exceptions

## Performance Metrics

- **Image Processing Time**: Should be under 1 second for good quality images
- **OCR Inference Time**: Should be under 4 seconds (after initial model load)
- **Total Response Time**: Should be under 6 seconds for complete flow
- **OCR Accuracy**: Should maintain >85% accuracy on clear food labels
- **Success Rate**: Should achieve >95% success rate on standard food labels

## Test Execution

### Preparation
1. Ensure backend is running with OCR model loaded
2. Ensure test food label images are available
3. Ensure frontend dependencies are installed (`npm install` or `pnpm install`)

### Execution Steps

1. **Manual UI Testing**:
   - Navigate to the scan page
   - Perform manual capture and processing of 5-10 different food labels
   - Record success rate, processing time, and OCR accuracy

2. **API Testing**:
   - Directly call the `/api/label/process-with-ocr` endpoint with test images
   - Verify response format matches specifications
   - Test with different image sizes and qualities

3. **Integration Testing**:
   - Verify the connection between frontend and backend
   - Test error conditions where backend is unavailable

## Expected Outcomes

- All test scenarios complete successfully
- OCR results meet minimum accuracy requirements (>85%)
- Performance metrics stay within defined bounds
- Error handling works gracefully
- UI displays all required information correctly

## Known Limitations

- OCR accuracy may vary significantly with poor image quality
- First request to OCR endpoint may be slower due to model loading
- Mobile performance may differ from desktop
- Certain label designs may not be recognized properly by OCR model