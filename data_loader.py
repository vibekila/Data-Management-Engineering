
import os
from pathlib import Path

import gdown
import pandas as pd


DATASET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1op5pVvniPLiL88I-HxvgWKKqM0AA2PsP/export?format=csv"
)


def cast_types(df: pd.DataFrame) -> pd.DataFrame:
    """Приводит числовые признаки датасета к числовым типам."""
    df = df.copy()

    numeric_columns = [
        "Ti(s)", "Te(s)", "PIF", "PEF", "volbal", "F", "vt", "mv",
        "EF50", "EIP", "EEp", "Penh", "AV", "TR", "Rpef",
    ]

    for col in numeric_columns:
        if col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str).str.replace(
                    ",", ".", regex=False
                )

            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def load_and_show_data(
    path: Path,
    parquet_path: Path,
) -> pd.DataFrame:
    """Загружает датасет, приводит типы и сохраняет Parquet."""
    path = Path(path)
    parquet_path = Path(parquet_path)

    path.parent.mkdir(parents=True, exist_ok=True)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    if parquet_path.is_file():
        df = pd.read_parquet(parquet_path)

    else:
        if not path.is_file():
            part_path = path.with_name(path.name + ".part")

            gdown.download(
                DATASET_URL,
                str(part_path),
                quiet=False,
            )

            if not part_path.is_file():
                raise FileNotFoundError(
                    "Не удалось скачать исходный датасет"
                )

            os.replace(part_path, path)

        df = pd.read_csv(path, sep=",", decimal=",")

    df = cast_types(df)
    df.to_parquet(parquet_path, index=False)

    print(df.head(10))
    
    return df


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"

    csv_file = data_dir / "dataset_for_DME.csv"
    parquet_file = data_dir / "dataset_for_DME.parquet"

    load_and_show_data(csv_file, parquet_file)
