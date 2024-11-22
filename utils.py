# utils.py
import os
from pathlib import Path

# Константы, пути
DATASET_PATH = Path(r"C:\Users\denis\.cache\kagglehub\datasets\aryashah2k\mobile-captured-pharmaceutical-medication-packages\versions\1\Mobile-Captured Pharmaceutical Medication Packages")
CLARINASE_PATH = DATASET_PATH / "Clarinase 14 repetabs"
CLARITINE_PATH = DATASET_PATH / "Claritine 20 tablets"
REFERENCE_CLARINASE = "iphone xs max 47.JPG"
REFERENCE_CLARITINE = "iphone xs max 358.JPG"
OUTPUT_DIR = Path("results")  # Папка для сохранения результатов
OUTPUT_DIR.mkdir(exist_ok=True)

SIMILARITY_THRESHOLD = 90.0  # Порог схожести для выделения различий
