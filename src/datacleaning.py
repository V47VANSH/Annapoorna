import os
from PIL import Image
from tqdm import tqdm

# Configuration
DATA_DIR = "..\\data\\train_augmented"  # same directory as in train2.py
ALLOWED_FORMATS = ['jpeg', 'png', 'gif', 'bmp']

# Count total files for overall progress (optional)
total_files = sum(len(files) for _, _, files in os.walk(DATA_DIR))
print(f"Total files to check: {total_files}")

removed_files = 0
# Walk through directories and clean invalid images with a progress bar per folder
for root, dirs, files in os.walk(DATA_DIR):
    for file in tqdm(files, desc=f"Cleaning {root}", unit="file"):
        file_path = os.path.join(root, file)
        try:
            with Image.open(file_path) as img:
                fmt = img.format.lower() if img.format else None
            if fmt is None or fmt not in ALLOWED_FORMATS:
                os.remove(file_path)
                removed_files += 1
        except Exception as e:
            # File is not a valid image or other error occurred
            try:
                os.remove(file_path)
                removed_files += 1
            except:
                print(f"Failed to remove {file_path}: {e}")

print(f"Data cleaning completed. Removed {removed_files} invalid files out of {total_files}.")