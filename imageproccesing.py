# image_processing.py
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from skimage.util import img_as_float
from pathlib import Path
import matplotlib.pyplot as plt
from utils import SIMILARITY_THRESHOLD, OUTPUT_DIR

def load_and_preprocess_image(image_path: Path, target_size: tuple = (500, 500)) -> np.ndarray | None:
    """Загрузка, преобразование в оттенки серого и изменение размера изображения."""
    try:
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"Ошибка: не удалось загрузить изображение {image_path}")
            return None
        img = cv2.resize(img, target_size)
        return img
    except Exception as e:
        print(f"Ошибка при загрузке или обработке изображения {image_path}: {e}")
        return None

def calculate_similarity(img1: np.ndarray, img2: np.ndarray) -> tuple[float, np.ndarray]:
    """Вычисление схожести двух изображений с использованием SSIM."""
    score, diff = ssim(
        img_as_float(img1),
        img_as_float(img2),
        full=True,
        data_range=1.0  
    )
    return score * 100, diff

def visualize_differences(img1: np.ndarray, img2: np.ndarray, diff: np.ndarray, output_path: Path, threshold: float = 0.1):
    """Визуализация различий между изображениями с выделением области различий."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    axes[0].imshow(img1, cmap='gray')
    axes[0].set_title('Исходное изображение 1')
    axes[0].axis('off')

    axes[1].imshow(img2, cmap='gray')
    axes[1].set_title('Исходное изображение 2')
    axes[1].axis('off')

    axes[2].imshow(diff, cmap='gray')
    axes[2].set_title('Различия')
    axes[2].axis('off')

    # Выделение области различий
    diff_mask = diff > threshold
    if np.any(diff_mask):
        y_indices, x_indices = np.where(diff_mask)
        x_min, x_max = np.min(x_indices), np.max(x_indices)
        y_min, y_max = np.min(y_indices), np.max(y_indices)

        rect = plt.Rectangle((x_min, y_min), x_max - x_min, y_max - y_min,
                             edgecolor='red', facecolor='none', linewidth=2)
        axes[2].add_patch(rect)

    plt.savefig(output_path)
    plt.close(fig)
    return diff_mask
