"""Set OFFLINE_MODE before the app is imported so tests never hit the network."""

import os
import sys
from pathlib import Path

os.environ.setdefault("OFFLINE_MODE", "true")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:3000")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
