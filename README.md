# 🌾 Agri-Vision-AI

## 🚀 Mission

Agri-Vision-AI is built to empower the agricultural community by leveraging artificial intelligence for early, accessible, and accurate **crop disease detection**. The goal is to:

-  Improve **crop yield**
-  Minimize **pesticide misuse**
-  Promote **sustainable farming practices**

---

## 🎯 Project Objectives

- **Disease Classification Model**  
  Develop a high-performance deep learning model to classify crop diseases from plant images.

- **User-Friendly Interface**  
  Build an intuitive platform allowing users to upload images for disease prediction.

- **LLM-Based Treatment Guidance**  
  Integrate a language model to provide reliable and personalized treatment suggestions based on detected diseases.

- **Inclusive Interaction**  
  Support **multilingual** and **voice-based** inputs to ensure accessibility across user demographics.

- **Real-World Scalability**  
  Optimize the system for robustness, efficiency, and deployment in diverse agricultural settings.

---

## 📊 Datasets Utilized

To ensure wide coverage of crop types and disease scenarios, we curated a diverse dataset by merging and processing multiple sources:

### 📁 1. [20K Multi-Class Crop Disease Images](https://www.kaggle.com/datasets/jawadali1045/20k-multi-class-crop-disease-images)
- Multi-crop dataset with real-world variations and multiple disease categories.

### 📁 2. [Plant Village Dataset](https://www.kaggle.com/datasets/emmarex/plantdisease)
- A standardized and widely used benchmark dataset for training and validation.

### 📁 3. [PlantDoc Dataset](https://github.com/pratikkayal/PlantDoc-Dataset)
- Realistic field images with complex backgrounds and natural lighting, ideal for generalization.

### 📁 4. [Identification of Plant Leaf Diseases Using a 9-layer Deep Convolutional Neural Network](https://data.mendeley.com/datasets/tywbtsjrjv/1)  

### 🧪 Final Unified Dataset Composition
- 🔢 **77 disease classes**
- 🖼️ ~**1,290 images per class**
- 🔁 Includes **augmentation and preprocessing** for consistency and robustness

  # Project Setup Instructions

Follow the steps below to set up the project environment and run the code:

---

## 1. Google Cloud Setup

- Create an account on [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project.
- In the backend directory, create a `.env.local` file and add the following:
  ```env
  PROJECT_ID="YOUR_PROJECT_ID"
  ```

---

## 2. Kaggle CLI Setup

- Setup Kaggle CLI according to the official documentation:  
  [https://github.com/Kaggle/kaggle-api](https://github.com/Kaggle/kaggle-api)
- Ensure you have your Kaggle API key saved as `kaggle.json` and configured properly.

---

## 3. Install Dependencies

### Python
- Install Python packages:
  ```bash
  pip install -r requirements.txt
  ```

### Node.js
- Download and install Node.js (LTS version) from the official site:  
  [https://nodejs.org/](https://nodejs.org/)
- Then install Node.js packages:
  ```bash
  npm install
  ```

---

## 4. Install `uv` and `astral`

### uv (Fast Python package manager)
- Install uv (recommended via pipx or curl):
  ```bash
  pipx install uv
  ```
  or
  ```bash
  curl -Ls https://astral.sh/uv/install.sh | bash
  ```
- Official docs: [https://astral.sh/uv](https://astral.sh/uv)

- Sync the environment:
  ```bash
  uv sync
  ```

- Install TensorFlow using uv:
  ```bash
  uv pip install tensorflow
  ```

---

## 5. Data Preparation

- Move into the data directory:
  ```bash
  cd data
  ```
- Download the data:
  ```bash
  python -m data_download
  ```
- Go back to root directory:
  ```bash
  cd ..
  ```

---

## 6. Preprocessing Scripts

- Move into the `src` directory:
  ```bash
  cd src
  ```
- Run the following scripts in order:
  ```bash
  python merge.py
  python augmentation.py
  python datacleaning.py
  ```

---

## 7. Model Training

- Open and run the **model training notebook** after preprocessing is complete.

---

## 8. Additional Tools

### FFmpeg

- Download and install FFmpeg from:  
  [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

---

> **Note:** Make sure all required paths and API credentials are correctly configured before training or deploying the model.

