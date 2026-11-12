
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection as PGConnection


BASE_DIR = Path(__file__).resolve().parent.parent

CREDS_FILE = BASE_DIR / "data" / "creds.db"
PARQUET_FILE = BASE_DIR / "data" / "dataset_for_DME.parquet"

DB_NAME = "homeworks"
TABLE_NAME = "giniyatullinadm"
ROWS_COUNT = 100


def load_dataset(file_path: Path, rows_count: int) -> pd.DataFrame:
    """Загружает первые rows_count строк из Parquet."""
    if not file_path.is_file():
        raise FileNotFoundError(
            f"Файл датасета не найден: {file_path}"
        )

    df = pd.read_parquet(file_path)

    if len(df) < rows_count:
        raise ValueError(
            f"Требуется {rows_count} строк, найдено {len(df)}"
        )

    return df.head(rows_count).copy()


def load_credentials(
    creds_file: Path,
    db_name: str,
) -> dict[str, str]:
    """Читает параметры подключения из SQLite."""
    if not creds_file.is_file():
        raise FileNotFoundError(
            f"Файл с реквизитами не найден: {creds_file}"
        )

    with closing(sqlite3.connect(creds_file)) as connection:
        connection.row_factory = sqlite3.Row

        row = connection.execute(
            """
            SELECT url, port, user, pass, db_name
            FROM access
            WHERE db_name = ?
            """,
            (db_name,),
        ).fetchone()

    if row is None:
        raise ValueError(
            f"Реквизиты для базы {db_name} не найдены"
        )

    return dict(row)


def connect_to_db(credentials: dict[str, str]) -> PGConnection:
    """Устанавливает соединение с PostgreSQL."""
    return psycopg2.connect(
        host=credentials["url"],
        port=credentials["port"],
        user=credentials["user"],
        password=credentials["pass"],
        database=credentials["db_name"],
        connect_timeout=10,
    )


def prepare_columns(
    df: pd.DataFrame,
) -> tuple[list[str], list[sql.Composable]]:
    """Подготавливает названия столбцов и SQL-типы."""
    clean_columns = [
        str(col).replace("(", "_")
        .replace(")", "_")
        .replace(".", "_")
        .lower()
        for col in df.columns
    ]

    sql_columns_parts = []

    for col_old, col_clean in zip(df.columns, clean_columns):
        if pd.api.types.is_numeric_dtype(df[col_old]):
            type_sql = sql.SQL("DOUBLE PRECISION")
        else:
            type_sql = sql.SQL("TEXT")

        sql_columns_parts.append(
            sql.SQL("{} {}").format(
                sql.Identifier(col_clean),
                type_sql,
            )
        )

    return clean_columns, sql_columns_parts


def write_dataframe(
    conn: PGConnection,
    df: pd.DataFrame,
    table_name: str,
) -> None:
    """Пересоздаёт таблицу и записывает в неё DataFrame."""
    clean_columns, sql_columns_parts = prepare_columns(df)

    try:
        with conn.cursor() as cursor:
            print(f"Пересоздание таблицы '{table_name}'.")

            cursor.execute(
                sql.SQL("DROP TABLE IF EXISTS {};").format(
                    sql.Identifier(table_name)
                )
            )

            create_table_query = sql.SQL(
                "CREATE TABLE {} (id SERIAL PRIMARY KEY, {});"
            ).format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(sql_columns_parts),
            )

            cursor.execute(create_table_query)

            placeholders = sql.SQL(", ").join(
                [sql.Placeholder()] * len(clean_columns)
            )

            insert_query = sql.SQL(
                "INSERT INTO {} ({}) VALUES ({});"
            ).format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(
                    sql.Identifier(col) for col in clean_columns
                ),
                placeholders,
            )

            data_records = [
                tuple(row)
                for _, row in df.iterrows()
            ]

            cursor.executemany(insert_query, data_records)

        conn.commit()

        print(
            f"Успешно записано {len(df)} строк "
            f"в таблицу '{table_name}'."
        )

    except Exception:
        conn.rollback()
        raise


if __name__ == "__main__":
    conn = None

    try:
        df_100 = load_dataset(PARQUET_FILE, ROWS_COUNT)
        credentials = load_credentials(CREDS_FILE, DB_NAME)

        print(f"Подготовлено строк: {len(df_100)}")
        print(f"База данных: {DB_NAME}")

        print("Подключение к PostgreSQL...")
        conn = connect_to_db(credentials)
        print("Подключение успешно.")

        write_dataframe(conn, df_100, TABLE_NAME)

    except Exception as error:
        print(f"Ошибка выполнения: {error}")
        raise

    finally:
        if conn is not None:
            conn.close()
            print("Соединение с PostgreSQL закрыто.")
