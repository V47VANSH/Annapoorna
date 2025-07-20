import os
from PIL import Image
import numpy as np
from tqdm import tqdm

# Path to your dataset folder
root_dir = 'data/train_augmented'

def convert_image_to_rgba(image_path):
    """Convert palette images with transparency to RGBA format"""
    try:
        # Try to open and verify the image first
        img = Image.open(image_path)
        img.verify()  # Verify the image is valid
        
        # Reopen the image since verify() may have closed it
        img = Image.open(image_path)
        
        # Check if image format is supported by TensorFlow
        name, ext = os.path.splitext(image_path)
        if ext.lower() not in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            print(f"Unsupported format, removing: {image_path}")
            os.remove(image_path)
            return
        
        # Convert to numpy array to check if image has valid data
        img_array = np.array(img)
        if img_array.size == 0:
            raise ValueError("Empty image array")
        
        # Check if image has valid dimensions (minimum 32x32)
        if len(img_array.shape) < 2 or min(img_array.shape[:2]) < 32:
            raise ValueError("Invalid image dimensions - too small")
        
        # Check for corrupted or invalid pixel data
        if img_array.max() == img_array.min():
            raise ValueError("Image has no variation in pixel values")
        
        # Always convert to RGB for consistency in training
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Force save as high-quality JPEG for TensorFlow compatibility
        new_path = name + '.jpg'
        img.save(new_path, 'JPEG', quality=98, optimize=True)
        
        # Remove original if extension changed
        if image_path != new_path:
            os.remove(image_path)
            print(f"Converted and saved as JPEG: {new_path}")
        else:
            print(f"Converted to RGB: {image_path}")
            
    except Exception as e:
        print(f"Error with {image_path}: {e}")
        # Try to remove corrupted file
        try:
            os.remove(image_path)
            print(f"Removed corrupted file: {image_path}")
        except:
            print(f"Could not remove corrupted file: {image_path}")

# Image file extensions to process
image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif'}

# Count total image files first
total_images = 0
for folder, subfolders, files in os.walk(root_dir):
    for filename in files:
        name, ext = os.path.splitext(filename)
        if ext.lower() in image_extensions:
            total_images += 1

# Convert images with progress bar
with tqdm(total=total_images, desc="Converting images", unit="image") as pbar:
    for folder, subfolders, files in os.walk(root_dir):
        for filename in files:
            name, ext = os.path.splitext(filename)
            
            # Convert image to RGBA if needed
            if ext.lower() in image_extensions:
                image_path = os.path.join(folder, filename)
                convert_image_to_rgba(image_path)
                pbar.update(1)

print("Image conversion completed. Now you can zip and upload to Kaggle.")