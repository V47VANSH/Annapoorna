import os
import random
import shutil
from PIL import Image, ImageEnhance, ImageOps
from tqdm import tqdm

def augment_image(img):
    # Basic augmentation: flip + color enhance
    if random.random() > 0.5:
        img = ImageOps.mirror(img)
    if random.random() > 0.5:
        img = ImageEnhance.Color(img).enhance(random.uniform(0.8, 1.2))
    if random.random() > 0.5:
        img = ImageEnhance.Brightness(img).enhance(random.uniform(0.8, 1.2))
    return img

def get_all_classes(base_dir):
    return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

def get_image_files(folder):
    return [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

def average_image_count(base_dir):
    classes = get_all_classes(base_dir)
    counts = []
    for cls in classes:
        img_files = get_image_files(os.path.join(base_dir, cls))
        counts.append(len(img_files))
    return int(sum(counts) / len(counts))

def augment_dataset(base_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    avg_n = average_image_count(base_dir)
    print(f"Average images per class: {avg_n}")

    for cls in tqdm(get_all_classes(base_dir), desc="Processing classes"):
        src_folder = os.path.join(base_dir, cls)
        dst_folder = os.path.join(output_dir, cls)
        os.makedirs(dst_folder, exist_ok=True)

        img_files = get_image_files(src_folder)
        count = len(img_files)

        if count > avg_n:
            # Keep only n random images
            selected = random.sample(img_files, avg_n)
            for f in selected:
                shutil.copy(os.path.join(src_folder, f), os.path.join(dst_folder, f))

        elif count < avg_n:
            # Copy all original images
            for f in img_files:
                shutil.copy(os.path.join(src_folder, f), os.path.join(dst_folder, f))
            # Augment once for each image until we reach close to avg_n
            extra_needed = avg_n - count
            i = 0
            while i < extra_needed:
                f = random.choice(img_files)
                img_path = os.path.join(src_folder, f)
                img = Image.open(img_path).convert("RGB")
                img_aug = augment_image(img)
                aug_name = f"aug_{i}_{f}"
                img_aug.save(os.path.join(dst_folder, aug_name))
                i += 1

        else:
            # Just copy
            for f in img_files:
                shutil.copy(os.path.join(src_folder, f), os.path.join(dst_folder, f))

# Example usage
augment_dataset("..\\data\\MergedDataset", "..\\data\\train_augmented")
