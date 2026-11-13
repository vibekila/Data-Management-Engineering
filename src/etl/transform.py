import pandas as pd


NUMERIC_COLUMNS = [
    "Ti(s)", "Te(s)", "PIF", "PEF", "volbal", "F", "vt", "mv",
    "EF50", "EIP", "EEp", "Penh", "AV", "TR", "Rpef",
]


def cast_types(df: pd.DataFrame) -> pd.DataFrame:
    """Преобразует числовые столбцы к подходящим типам данных."""
    df = df.copy()

    missing_columns = set(NUMERIC_COLUMNS) - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"Отсутствуют столбцы: {sorted(missing_columns)}"
        )

    for col in NUMERIC_COLUMNS:
        if not pd.api.types.is_numeric_dtype(df[col]):
            values = df[col].astype("string").str.replace(
                ",", ".", regex=False
            )
            df[col] = pd.to_numeric(values, errors="coerce")

    return df


def validate_data(df: pd.DataFrame) -> bool:
    """Проверяет структуру и результат преобразования данных."""
    if df.empty:
        print("Ошибка: датасет пустой.")
        return False

    missing_columns = set(NUMERIC_COLUMNS) - set(df.columns)

    if missing_columns:
        print(f"Отсутствуют столбцы: {sorted(missing_columns)}")
        return False

    for col in NUMERIC_COLUMNS:
        if not pd.api.types.is_numeric_dtype(df[col]):
            print(f"Столбец {col} не является числовым.")
            return False

    # Проверка пропусков после преобразования типов
    missing_values = df[NUMERIC_COLUMNS].isna().sum()

    if missing_values.sum() > 0:
        print("Ошибка: обнаружены пропущенные или некорректные значения:")
        print(missing_values[missing_values > 0])
        return False

    return True
