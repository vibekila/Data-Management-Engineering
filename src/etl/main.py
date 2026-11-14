import argparse
from pathlib import Path

from etl.extract import download_dataset, read_dataset
from etl.load import (
    connect_to_db,
    load_credentials,
    save_parquet,
    write_dataframe,
)
from etl.transform import cast_types, validate_data


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


CSV_FILE = DATA_DIR / "dataset_for_DME.csv"
PARQUET_FILE = DATA_DIR / "etl_processed.parquet"
CREDS_FILE = DATA_DIR / "creds.db"

DB_NAME = "homeworks"
TABLE_NAME = "giniyatullinadm"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ETL-пайплайн для обработки датасета"
    )

    parser.add_argument(
        "--mode",
        choices=["prepare", "replace"],
        default="prepare",
        help="Режим работы: prepare или replace",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Количество строк для PostgreSQL в режиме replace (по умолчанию 100)",
    )

    args = parser.parse_args()

    if args.limit <= 0:
        parser.error("--limit должен быть положительным числом")

    # Извлечение
    print("--- Загрузка датасета ---")
    download_dataset(CSV_FILE)
    df = read_dataset(CSV_FILE)
    print(f"Выполнено: прочитано строк: {len(df)}")

    # Преобразование
    print("--- Преобразование данных ---")
    df = cast_types(df)
    print(f"Выполнено: обработано столбцов: {len(df.columns)}")

    print("--- Проверка данных ---")
    if not validate_data(df):
        raise ValueError("Ошибка: проверка данных не пройдена")
    print("Успешно: проверка данных пройдена")

    # Загрузка
    print("--- Сохранение Parquet ---")
    save_parquet(df, PARQUET_FILE)
    print(f"Файл сохранён: {PARQUET_FILE}")

    if args.mode == "replace":
        if args.limit > len(df):
            raise ValueError(
                "Ошибка: запрошено больше строк, чем имеется в датасете"
            )

        print("--- Загрузка в PostgreSQL ---")
        sample = df.head(args.limit).copy()

        credentials = load_credentials(CREDS_FILE, DB_NAME)
        conn = None

        try:
            conn = connect_to_db(credentials)
            print(f"Подключение к базе {DB_NAME} успешно")

            write_dataframe(conn, sample, TABLE_NAME)

        finally:
            if conn is not None:
                conn.close()
                print("Соединение с PostgreSQL закрыто")

    print("--- ETL завершен без ошибок ---")
