from pathlib import Path

import gdown
import pandas as pd


DATASET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1op5pVvniPLiL88I-HxvgWKKqM0AA2PsP/export?format=csv"
)


def download_dataset(file_path: Path) -> None:
    """Скачивает исходный CSV, если файл ещё не существует."""
    if file_path.is_file():
        return

    file_path.parent.mkdir(parents=True, exist_ok=True)

    result = gdown.download(
        DATASET_URL,
        str(file_path),
        quiet=False,
    )

    if result is None or not file_path.is_file():
        raise RuntimeError("Не удалось скачать исходный датасет")


def read_dataset(file_path: Path) -> pd.DataFrame:
    """Читает CSV и возвращает DataFrame."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    return pd.read_csv(file_path)
