import fs from 'fs/promises';
import path from 'path';

// Test OCR endpoint with real food label images
async function testOCR(): Promise<void> {
  // Read a test image
  const imagePath = path.join(process.cwd(), '..', 'data', 'food_labels', 'test_real.jpeg');
  console.log('Reading image from:', imagePath);
  
  let imageData: Buffer;
  try {
    imageData = await fs.readFile(imagePath);
    console.log('Image read successfully');
  } catch (error) {
    console.error('Error reading image:', error);
    return;
  }

  // Convert image to base64
  const base64Image = imageData.toString('base64');
  const dataUrl = `data:image/jpeg;base64,${base64Image}`;

  // Configure request
  const endpoint = 'http://localhost:8000/api/label/process-with-ocr';
  const metadata = {
    timestamp: Date.now(),
    source: 'test_integration',
    capture_method: 'burst_fusion',
    original_resolution: '250x350'
  };

  console.log('Sending request to:', endpoint);
  console.log('Image size:', imageData.length, 'bytes');
  
  try {
    // Make request to OCR endpoint
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        image_base64: dataUrl,
        metadata: metadata
      })
    });

    console.log('Response status:', response.status);
    
    if (!response.ok) {
      console.error('Request failed:', response.statusText);
      const errorText = await response.text();
      console.error('Error response:', errorText);
      return;
    }

    const result = await response.json();
    console.log('OCR Result received:');
    console.log('- Status:', result.status);
    console.log('- Message:', result.message);
    console.log('- Quality tier:', result.quality_analysis?.quality_tier);
    console.log('- Tokens extracted:', result.ocr_result?.token_count);
    console.log('- Error in OCR:', result.ocr_result?.error);
    
    if (result.status === 'success' && result.ocr_result && !result.ocr_result.error) {
      console.log('✅ OCR processing successful!');
      
      // Save enhanced image if available
      if (result.enhanced_image_base64) {
        console.log('Saving enhanced image...');
        const base64Data = result.enhanced_image_base64.replace(/^data:image\/jpeg;base64,/, "");
        const buffer = Buffer.from(base64Data, 'base64');
        await fs.writeFile('test_processed_1.jpeg', buffer);
        console.log('Enhanced image saved as test_processed_1.jpeg');
      }
      
      // Save OCR text if available
      if (result.ocr_result?.markdown) {
        await fs.writeFile('ocr_output.txt', result.ocr_result.markdown);
        console.log('OCR text saved as ocr_output.txt');
      }
    } else {
      console.log('⚠️ OCR processing completed with issues');
    }
  } catch (error) {
    console.error('Error making request:', error);
  }
}

// Run test
testOCR().catch(console.error);