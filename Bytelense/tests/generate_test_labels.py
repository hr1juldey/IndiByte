#!/usr/bin/env python3
"""
Generate synthetic food label images for testing OCR functionality.
"""

import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

def create_food_label_image(filename, text_content, label_color="white", text_color="black", width=400, height=600):
    """
    Create a synthetic food label image with text content.
    
    Args:
        filename: Output filename
        text_content: Text content for the food label
        label_color: Background color of the label
        text_color: Text color
        width: Image width
        height: Image height
    """
    # Create a blank image with specified background color
    image = Image.new('RGB', (width, height), color=label_color)
    draw = ImageDraw.Draw(image)
    
    try:
        # Use default font
        font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Add text to the image
    y_offset = 20
    for line in text_content.split('\n'):
        draw.text((20, y_offset), line, fill=text_color, font=font)
        y_offset += 20
    
    # Add some additional label elements
    draw.rectangle([10, 10, width-10, height-10], outline=text_color, width=2)
    
    # Save the image
    image.save(filename)
    print(f"Generated: {filename}")


def add_noise_blur(img_path, output_path, noise_type='gaussian', blur=False, blur_amount=1):
    """
    Add noise and/or blur to make image more realistic for OCR testing.
    """
    img = cv2.imread(img_path)
    
    # Add noise
    if noise_type == 'gaussian':
        noise = np.random.normal(0, 25, img.shape).astype(np.uint8)
        img = cv2.add(img, noise)
    elif noise_type == 'salt_pepper':
        prob = 0.01
        random_matrix = np.random.random(img.shape[:2])
        img[random_matrix < prob] = 0
        img[random_matrix > 1 - prob] = 255
    
    # Add blur
    if blur:
        kernel_size = 2 * blur_amount + 1
        img = cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)
    
    cv2.imwrite(output_path, img)


def main():
    # Create directory for test images
    os.makedirs('data/food_labels', exist_ok=True)
    
    # Sample food label contents
    labels = [
        ("cereal_label.jpg", """Product: Whole Grain Cereal
Brand: Healthy Start
Net Weight: 500g

NUTRITION FACTS
Serving Size: 1 cup (30g)
Servings Per Container: About 16

Amount Per Serving
Calories 120           % Daily Value*
Total Fat 1g           2%
Saturated Fat 0g       0%
Trans Fat 0g
Cholesterol 0mg        0%
Sodium 150mg           6%
Total Carbohydrate 25g 9%
Dietary Fiber 3g       11%
Total Sugars 8g
  Includes 4g Added Sugars   8%
Protein 3g

Vitamin D 2mcg    10%
Calcium 100mg     8%
Iron 4.5mg       25%
Vitamin C 0mg     0%

*Percent Daily Values are based on a 2,000 calorie diet.""", "white", "black"),
        
        ("chocolate_label.jpg", """Premium Dark Chocolate
Ingredients: 
Cocoa mass, sugar, cocoa butter, 
emulsifier: soya lecithin, 
natural vanilla flavoring.
Cocoa solids: 70% minimum
May contain traces of milk and nuts.

NUTRITION INFORMATION
Per 100g: Energy 2300kJ/550kcal
Fat 43g of which saturates 26g
Carbohydrate 24g of which sugars 23g
Fiber 11g
Protein 8g
Salt 0.01g

Store in a cool, dry place.""", "brown", "white"),
        
        ("sauce_label.jpg", """Organic Tomato Sauce
Ingredients: Organic tomatoes, 
organic onions, organic herbs, 
sea salt, organic spices.
No preservatives added.

NUTRITION FACTS (per 100g)
Energy: 85kJ/20kcal
Protein: 1.0g
Carbohydrate: 3.8g
  of which sugars: 3.0g
Fat: 0.2g
  of which saturates: 0.0g
Fiber: 1.2g
Sodium: 0.4g

Best before: See lid
Keep refrigerated after opening
Use within 3 days""", "red", "white"),
        
        ("juice_label.jpg", """Orange Juice Fresh
Ingredients: 100% orange juice
from concentrate
Vitamin C: 60mg per 100ml

NUTRITION INFORMATION
Per 100ml: Energy 180kJ/43kcal
Fat: 0.2g
  of which saturates: 0.0g
Carbohydrate: 9.5g
  of which sugars: 8.9g
Fiber: 0.2g
Protein: 0.5g
Salt: 0.01g

Shake well before use
Consume within 3 days of opening""", "orange", "black"),
        
        ("soup_label.jpg", """Creamy Mushroom Soup
Ingredients: Mushrooms (40%), 
vegetable stock, cream (milk), 
onions, wheat flour, butter (milk), 
yeast extract, salt, herbs.

NUTRITION (per 100g)
Energy 250kJ/60kcal
Fat 2.5g of which saturates 1.5g
Carbohydrate 7.0g of which sugars 2.0g
Protein 2.0g
Salt 0.8g

Suitable for vegetarians""", "white", "black"),
    ]
    
    # Generate the basic food label images
    for filename, text, bg_color, text_color in labels:
        full_path = f"data/food_labels/{filename}"
        create_food_label_image(full_path, text, bg_color, text_color)
    
    # Create additional versions with noise and blur to simulate real conditions
    for filename, text, bg_color, text_color in labels:
        input_path = f"data/food_labels/{filename}"
        
        # Create blurred version
        blurred_path = f"data/food_labels/blurred_{filename}"
        add_noise_blur(input_path, blurred_path, blur=True, blur_amount=1)
        
        # Create noisy version
        noisy_path = f"data/food_labels/noisy_{filename}"
        add_noise_blur(input_path, noisy_path, noise_type='gaussian')
        
        # Create low contrast version
        low_contrast_path = f"data/food_labels/low_contrast_{filename}"
        add_noise_blur(input_path, low_contrast_path, blur=True, blur_amount=0.5)


if __name__ == "__main__":
    main()