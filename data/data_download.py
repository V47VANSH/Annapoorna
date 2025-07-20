import os
import zipfile
import requests
import subprocess
from pathlib import Path
import sys
from tqdm import tqdm  # Add tqdm for progress bar
import time

def ensure_dir(directory):
    Path(directory).mkdir(parents=True, exist_ok=True)

def download_kaggle(dataset, dest):
    print(f"\n>> Downloading {dataset} to {dest}")
    ensure_dir(dest)
    # Show spinner while subprocess runs
    from threading import Thread

    def spinner():
        while not spinner.stop:
            for c in "|/-\\":
                print(f"\rDownloading... {c}", end="", flush=True)
                time.sleep(0.1)
    spinner.stop = False
    t = Thread(target=spinner)
    t.start()
    try:
        subprocess.run([
            sys.executable, "-m", "kaggle", "datasets", "download", "-d", dataset,
            "-p", dest, "--unzip"
        ], check=True)
    except Exception as e:
        print(f"\nError downloading {dataset}: {e}")
        print("Make sure kaggle CLI is installed and the API key is set up.")
    finally:
        spinner.stop = True
        t.join()
        print("\rDownload complete.         ")

def download_file(url, dest):
    print(f"\n>> Downloading {url} to {dest}")
    ensure_dir(os.path.dirname(dest))
    with requests.get(url, stream=True, allow_redirects=True) as r:
        r.raise_for_status()
        total = int(r.headers.get('content-length', 0))
        with open(dest, "wb") as f, tqdm(
            total=total, unit='B', unit_scale=True, desc="Downloading", ncols=80
        ) as pbar:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

def extract_zip(zip_path, extract_to):
    # Only extract if it's truly a zip file
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            print(f">> Extracting {zip_path} to {extract_to}")
            zip_ref.extractall(extract_to)
    except zipfile.BadZipFile:
        print(f"ERROR: {zip_path} is not a valid ZIP file or may be incomplete!")

# ---- 1. 20k-Crop Disease ----
download_kaggle("jawadali1045/20k-multi-class-crop-disease-images", "20k-Crop-Disease")

# ---- 2. Plant Village ----
download_kaggle("emmarex/plantdisease", "PlantVillage")

# ---- 3. PlantDoc from GitHub ----
plantdoc_dir = "PlantDoc"
plantdoc_zip = os.path.join(plantdoc_dir, "PlantDoc.zip")
if not Path(plantdoc_zip).exists():
    download_file(
        "https://github.com/pratikkayal/PlantDoc-Dataset/archive/refs/heads/master.zip",
        plantdoc_zip
    )
    extract_zip(plantdoc_zip, plantdoc_dir)
else:
    print(f"\n>> {plantdoc_zip} already exists, skipping download.")

# ---- 4. Mendeley Plant Leaf Disease Dataset ----
mendeley_dir = "PlantLeafCNN"
mendeley_zip = os.path.join(mendeley_dir, "PlantLeafCNN.zip")
mendeley_url = "https://data.mendeley.com/public-files/datasets/tywbtsjrjv/files/d5652a28-c1d8-4b76-97f3-72fb80f94efc/file_downloaded"
if not Path(mendeley_zip).exists():
    download_file(mendeley_url, mendeley_zip)
    extract_zip(mendeley_zip, mendeley_dir)
else:
    print(f"\n>> {mendeley_zip} already exists, skipping download.")

print("\nAll downloads and extractions completed.")
