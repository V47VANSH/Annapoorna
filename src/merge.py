import os
import shutil
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm  # Add tqdm for progress bar

# Path configuration
source_dirs = [
    "..\\data\\PlantVillage\\PlantVillage",
    "..\\data\\PlantLeafCNN\\PlantLeafCNN",
    "..\\data\\20k-Crop-Disease\\20k-multi-class-crop-disease-images\\train",
    "..\\data\\PlantDoc\\PlantDoc-Dataset-master"
]
target_base = "..\\data\\MergedDataset"

# Create if not exist
os.makedirs(target_base, exist_ok=True)

# Manual mapping of similar folders -> unified target folder
mapping = {
    # Tomato
    "Tomato_Bacterial_spot": "Tomato___Bacterial_spot",
    "Tomato___Bacterial_spot": "Tomato___Bacterial_spot",
    "Tomato leaf bacterial spot": "Tomato___Bacterial_spot",

    "Tomato_Early_blight": "Tomato___Early_blight",
    "Tomato___Early_blight": "Tomato___Early_blight",
    "Tomato Early blight leaf": "Tomato___Early_blight",

    "Tomato_Late_blight": "Tomato___Late_blight",
    "Tomato___Late_blight": "Tomato___Late_blight",
    "Tomato leaf late blight": "Tomato___Late_blight",

    "Tomato_healthy": "Tomato___healthy",
    "Tomato___healthy": "Tomato___healthy",
    "Tomato leaf": "Tomato___healthy",

    "Tomato_Leaf_Mold": "Tomato___Leaf_Mold",
    "Tomato mold leaf": "Tomato___Leaf_Mold",

    "Tomato_Septoria_leaf_spot": "Tomato___Septoria_leaf_spot",
    "Tomato___Septoria_leaf_spot": "Tomato___Septoria_leaf_spot",
    "Tomato Septoria leaf spot": "Tomato___Septoria_leaf_spot",

    "Tomato_Spider_mites_Two_spotted_spider_mite": "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Spider_mites Two-spotted_spider_mite": "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato two spotted spider mites leaf": "Tomato___Spider_mites Two-spotted_spider_mite",

    "Tomato__Target_Spot": "Tomato___Target_Spot",
    "Tomato___Target_Spot": "Tomato___Target_Spot",

    "Tomato__Tomato_mosaic_virus": "Tomato___Tomato_mosaic_virus",
    "Tomato leaf mosaic virus": "Tomato___Tomato_mosaic_virus",

    "Tomato__Tomato_YellowLeaf__Curl_Virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato leaf yellow virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",

    # Potato
    "Potato___Early_blight": "Potato___Early_blight",
    "Potato leaf early blight": "Potato___Early_blight",

    "Potato___Late_blight": "Potato___Late_blight",
    "Potato leaf late blight": "Potato___Late_blight",

    "Potato___healthy": "Potato___healthy",
    "Potato leaf": "Potato___healthy",

    # Pepper Bell
    "Pepper__bell___Bacterial_spot": "Pepper_bell___Bacterial_spot",
    "Pepper,_bell___Bacterial_spot": "Pepper_bell___Bacterial_spot",
    "Bell_pepper leaf spot": "Pepper_bell___Bacterial_spot",

    "Pepper__bell___healthy": "Pepper_bell___healthy",
    "Pepper,_bell___healthy": "Pepper_bell___healthy",
    "Bell_pepper leaf": "Pepper,_bell___healthy",

    # Apple
    "Apple___Apple_scab": "Apple___Apple_scab",
    "Apple Scab Leaf": "Apple___Apple_scab",

    "Apple___Black_rot": "Apple___Black_rot",
    "Apple___Cedar_apple_rust": "Apple___Cedar_apple_rust",
    "Apple rust leaf": "Apple___Cedar_apple_rust",

    "Apple___healthy": "Apple___healthy",
    "Apple leaf": "Apple___healthy",

    # Blueberry
    "Blueberry___healthy": "Blueberry___healthy",
    "Blueberry leaf": "Blueberry___healthy",

    # Cherry
    "Cherry___Powdery_mildew": "Cherry___Powdery_mildew",
    "Cherry___healthy": "Cherry___healthy",
    "Cherry leaf": "Cherry___healthy",

    # Corn
    "Corn___Cercospora_leaf_spot Gray_leaf_spot": "Corn___Gray_Leaf_Spot",
    "Corn Gray leaf spot": "Corn___Gray_Leaf_Spot",
    "Gray_Leaf_Spot": "Corn___Gray_Leaf_Spot",

    "Corn___Northern_Leaf_Blight": "Corn___Northern_Leaf_Blight",
    "Corn leaf blight": "Corn___Northern_Leaf_Blight",

    "Corn___Common_rust": "Corn___Common_rust",
    "Corn rust leaf": "Corn___Common_rust",
    "Common_Rust": "Corn___Common_rust",

    "Corn___healthy": "Corn___healthy",
    "Healthy Maize": "Corn___healthy",

    # Grape
    "Grape___Black_rot": "Grape___Black_rot",
    "grape leaf black rot": "Grape___Black_rot",

    "Grape___Esca_(Black_Measles)": "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "grape leaf": "Grape___healthy",
    "Grape___healthy": "Grape___healthy",

    # Orange
    "Orange___Haunglongbing_(Citrus_greening)": "Orange___Haunglongbing_(Citrus_greening)",

    # Peach
    "Peach___Bacterial_spot": "Peach___Bacterial_spot",
    "Peach___healthy": "Peach___healthy",
    "Peach leaf": "Peach___healthy",

    # Raspberry
    "Raspberry___healthy": "Raspberry___healthy",
    "Raspberry leaf": "Raspberry___healthy",

    # Soybean
    "Soybean___healthy": "Soybean___healthy",
    "Soyabean leaf": "Soybean___healthy",

    # Squash
    "Squash___Powdery_mildew": "Squash___Powdery_mildew",
    "Squash Powdery mildew leaf": "Squash___Powdery_mildew",

    # Strawberry
    "Strawberry___Leaf_scorch": "Strawberry___Leaf_scorch",
    "Strawberry___healthy": "Strawberry___healthy",
    "Strawberry leaf": "Strawberry___healthy",

    # Sugarcane
    "RedRot sugarcane": "Sugarcane___RedRot",
    "RedRust sugarcane": "Sugarcane___RedRust",
    "Mosaic sugarcane": "Sugarcane___Mosaic",
    "Sugarcane Healthy": "Sugarcane___healthy",
    "Yellow Rust Sugarcane": "Sugarcane___Yellow_Rust",

    # Rice
    "Becterial Blight in Rice": "Rice___Bacterial_blight",
    "Rice Blast": "Rice___Blast",
    "Tungro": "Rice___Tungro",

    # Cotton
    "American Bollworm on Cotton": "Cotton___American_Bollworm",
    "Anthracnose on Cotton": "Cotton___Anthracnose",
    "bacterial_blight in Cotton": "Cotton___Bacterial_Blight",
    "bollrot on Cotton": "Cotton___Bollrot",
    "bollworm on Cotton": "Cotton___Bollworm",
    "cotton whitefly": "Cotton___Whitefly",
    "cotton mealy bug": "Cotton___Mealy_bug",
    "Cotton Aphid": "Cotton___Aphid",
    "red cotton bug": "Cotton___Red_Bug",
    "pink bollworm in cotton": "Cotton___Pink_Bollworm",
    "Healthy cotton": "Cotton___healthy",
    "thirps on  cotton": "Cotton___Thrips",
    "Leaf Curl": "Cotton___Leaf_Curl",

    # Wheat
    "Wheat aphid": "Wheat___Aphid",
    "Wheat black rust": "Wheat___Black_Rust",
    "Wheat Brown leaf Rust": "Wheat___Brown_Rust",
    "Wheat leaf blight": "Wheat___Leaf_Blight",
    "Wheat mite": "Wheat___Mite",
    "Wheat powdery mildew": "Wheat___Powdery_Mildew",
    "Wheat scab": "Wheat___Scab",
    "Wheat Stem fly": "Wheat___Stem_Fly",
    "Wheat___Yellow_Rust": "Wheat___Yellow_Rust",
    "Healthy Wheat": "Wheat___healthy",

    "Tomato___Leaf_Mold": "Tomato___Leaf_Mold",
    "Tomato___Tomato_mosaic_virus": "Tomato___Tomato_mosaic_virus",
    "Army worm": "Cotton___Armyworm",
    "Brownspot": "Rice___Brown_Spot",
    "Flag Smut": "Wheat___Flag_Smut",
    "Leaf smut": "Wheat___Leaf_Smut",
    "maize ear rot": "Corn___Ear_Rot",
    "maize fall armyworm": "Corn___Fall_Armyworm",
    "maize stem borer": "Corn___Stem_Borer",

    # Backgrounds
    "Background_without_leaves": "Background_without_leaves"
}
# mapping = {}

# Reverse mapping for quick lookup
reverse_mapping = defaultdict(list)
for k, v in mapping.items():
    reverse_mapping[v].append(k)

# Function to copy all images to merged folder
def merge_folders():
    # First, count total files to process for progress bar
    total_files = 0
    for source_dir in source_dirs:
        for subfolder in os.listdir(source_dir):
            full_path = os.path.join(source_dir, subfolder)
            if not os.path.isdir(full_path):
                continue
            target_folder = mapping.get(subfolder)
            if not target_folder:
                continue
            total_files += len([f for f in os.listdir(full_path) if os.path.isfile(os.path.join(full_path, f))])

    with tqdm(total=total_files, desc="Merging images", unit="img") as pbar:
        for source_dir in source_dirs:
            for subfolder in os.listdir(source_dir):
                full_path = os.path.join(source_dir, subfolder)
                if not os.path.isdir(full_path):
                    continue

                target_folder = mapping.get(subfolder)
                if not target_folder:
                    print(f"Skipping unmapped: {subfolder}")
                    continue

                dest_dir = os.path.join(target_base, target_folder)
                os.makedirs(dest_dir, exist_ok=True)

                for file in os.listdir(full_path):
                    src = os.path.join(full_path, file)
                    if os.path.isfile(src):
                        dst = os.path.join(dest_dir, file)
                        # Avoid overwriting
                        if not os.path.exists(dst):
                            shutil.copy2(src, dst)
                        pbar.update(1)

merge_folders()
print("✅ Merging done.")
