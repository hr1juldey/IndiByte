import sys
import os
import cv2
import numpy as np

# Add the Bytelense path to the system path so we can import our new module
sys.path.append('/home/riju279/Documents/Projects/IndiByte/IndiByte')

from tile_based_image_quality_assessment import assess_image_quality_locally, visualize_tile_assessment

def test_tile_based_assessment():
    """
    Test the tile-based image quality assessment on the food label test images.
    """
    # Define the paths to the test images
    test_images = [
        '/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/data/food_labels/test_real.jpeg',
        '/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/data/food_labels/test_ocr.jpeg',
        '/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/data/food_labels/test_processed_1.jpeg',
        '/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/data/food_labels/test_clean.jpeg',
        '/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/data/food_labels/test_ocr_clean.jpeg'
    ]
    
    print("Testing tile-based image quality assessment...")
    print("=" * 80)
    
    for image_path in test_images:
        if not os.path.exists(image_path):
            print(f"Image not found: {image_path}")
            continue
        
        print(f"\nAnalyzing: {os.path.basename(image_path)}")
        print("-" * 50)
        
        try:
            # Perform tile-based quality assessment
            assessment = assess_image_quality_locally(
                image_path, 
                tile_size=64,
                overlap=16
            )
            
            print(f"Composite Score: {assessment['composite_score']:.2f}")
            print(f"Quality Category: {assessment['quality_category']}")
            print(f"Number of Tiles: {assessment['num_tiles']}")
            print(f"OCR Recommended: {assessment['ocr_recommended']}")
            
            print("Processing Recommendations:")
            for rec in assessment['processing_recommendations']:
                print(f"  - {rec}")

            # Print some aggregated metrics
            print("\nAggregated Metrics:")
            print(f"  Sharpness (mean): {assessment['aggregated_metrics']['sharpness_mean']:.2f}")
            print(f"  Contrast (mean): {assessment['aggregated_metrics']['contrast_mean']:.2f}")
            print(f"  Brightness (mean): {assessment['aggregated_metrics']['brightness_mean']:.2f}")
            print(f"  Glare (mean): {assessment['aggregated_metrics']['glare_mean']:.4f}")
            print(f"  Noise (mean): {assessment['aggregated_metrics']['noise_mean']:.4f}")

            # Print information about good tile clusters
            print(f"  Good tile clusters: {len(assessment['good_tile_clusters'])}")
            if assessment['good_tile_clusters']:
                best_cluster = max(assessment['good_tile_clusters'], key=lambda x: x['quality_score'])
                print(f"  Best cluster quality score: {best_cluster['quality_score']:.2f}")
                print(f"  Best cluster area ratio: {best_cluster['area_ratio']:.2f}")

            # Generate visualization
            vis_path = f"tile_assessment_visualization_{os.path.basename(image_path)}"
            vis_path = os.path.join('/home/riju279/Documents/Projects/IndiByte/IndiByte/Bytelense/tests', vis_path)
            visualize_tile_assessment(image_path, output_path=vis_path)
            print(f"Visualization saved to: {vis_path}")

        except Exception as e:
            print(f"Error analyzing {image_path}: {e}")
    
    print("\n" + "=" * 80)
    print("Tile-based assessment test completed.")

if __name__ == "__main__":
    test_tile_based_assessment()