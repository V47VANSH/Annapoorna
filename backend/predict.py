"""Crop disease classification from a leaf image."""

import io
import logging
import threading

import numpy as np
from PIL import Image, UnidentifiedImageError

import config

logger = logging.getLogger(__name__)

CLASS_NAMES = [
    "American Bollworm on Cotton",
    "Anthracnose on Cotton",
    "Army worm",
    "Becterial Blight in Rice",
    "Brownspot",
    "Common_Rust",
    "Cotton Aphid",
    "Flag Smut",
    "Gray_Leaf_Spot",
    "Healthy Maize",
    "Healthy Wheat",
    "Healthy cotton",
    "Leaf Curl",
    "Leaf smut",
    "Mosaic sugarcane",
    "RedRot sugarcane",
    "RedRust sugarcane",
    "Rice Blast",
    "Sugarcane Healthy",
    "Tungro",
    "Wheat Brown leaf Rust",
    "Wheat Stem fly",
    "Wheat aphid",
    "Wheat black rust",
    "Wheat leaf blight",
    "Wheat mite",
    "Wheat powdery mildew",
    "Wheat scab",
    "Wheat___Yellow_Rust",
    "Wilt",
    "Yellow Rust Sugarcane",
    "bacterial_blight in Cotton",
    "bollrot on Cotton",
    "bollworm on Cotton",
    "cotton mealy bug",
    "cotton whitefly",
    "maize ear rot",
    "maize fall armyworm",
    "maize stem borer",
    "pink bollworm in cotton",
    "red cotton bug",
    "thirps on  cotton",
]



class ModelUnavailable(RuntimeError):
    """Raised when the classifier weights cannot be loaded."""


_model = None
_lock = threading.Lock()


def _get_model():
    """Load the model on first use (the file is ~300MB)."""
    global _model
    if _model is not None:
        return _model

    if config.OFFLINE_MODE:
        raise ModelUnavailable("OFFLINE_MODE is enabled; the classifier is disabled.")
    if not config.MODEL_PATH.exists():
        raise ModelUnavailable(
            f"Model weights not found at {config.MODEL_PATH}. "
            "Run 'git lfs pull' to fetch them, or set MODEL_PATH."
        )

    with _lock:
        if _model is None:
            # tensorflow is slow to import
            from tensorflow.keras.models import load_model

            logger.info("Loading crop disease model from %s", config.MODEL_PATH)
            _model = load_model(str(config.MODEL_PATH))
    return _model


def predict_disease(img_bytes: bytes) -> str:
    """Classify a leaf image, returning the predicted disease label."""
    label, _ = predict_disease_with_confidence(img_bytes)
    return label


def preprocess(img_bytes: bytes) -> np.ndarray:
    """Resize to 224x224 RGB and scale to [0, 1], same as in training."""
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Uploaded file could not be decoded as an image.") from exc

    size = config.MODEL_IMAGE_SIZE
    img = img.resize((size, size))

    img_array = np.asarray(img, dtype=np.float32) / 255.0
    return np.expand_dims(img_array, axis=0)


def predict_top_k(img_bytes: bytes, k: int = 3) -> list[tuple[str, float]]:
    """The ``k`` most likely classes as ``(label, probability)``, best first."""
    model = _get_model()
    probabilities = model.predict(preprocess(img_bytes), verbose=0)[0]
    best = np.argsort(probabilities)[::-1][:k]
    return [(CLASS_NAMES[i], float(probabilities[i])) for i in best]


def predict_disease_with_confidence(img_bytes: bytes) -> tuple[str, float]:
    """Classify a leaf image, returning ``(label, confidence)``."""
    return predict_top_k(img_bytes, k=1)[0]


def is_ready() -> bool | None:
    """True if loaded, False if the file exists, None if it's missing."""
    if _model is not None:
        return True
    return False if config.MODEL_PATH.exists() else None


def main(argv: list[str] | None = None) -> int:
    """Usage: uv run python predict.py leaf.jpg [more.jpg ...] [--top 5]"""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="Classify crop leaf images with the Annapoorna CNN."
    )
    parser.add_argument("images", nargs="+", type=Path, help="image files to classify")
    parser.add_argument(
        "--top", type=int, default=3, help="number of classes to show (default 3)"
    )
    args = parser.parse_args(argv)

    try:
        _get_model()
    except ModelUnavailable as exc:
        print(f"error: {exc}")
        return 1

    status = 0
    for path in args.images:
        try:
            results = predict_top_k(path.read_bytes(), k=args.top)
        except (OSError, ValueError) as exc:
            print(f"{path}: error: {exc}")
            status = 1
            continue

        print(path)
        for rank, (label, probability) in enumerate(results, start=1):
            print(f"  {rank}. {label:<30} {probability:6.1%}")
    return status


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.WARNING)
    sys.exit(main())
