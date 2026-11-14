import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection as PGConnection


def to_native(value: Any) -> Any:
    """Преобразует значения pandas и NumPy в типы Python."""
    if isinstance(value, (list, tuple, dict)):
        return value

    if pd.isna(value):
        return None

    return value.item() if isinstance(value, np.generic) else value


def save_parquet(df: pd.DataFrame, file_path: Path) -> None:
    """Сохраняет обработанный DataFrame в формате Parquet."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(file_path, index=False)


def load_credentials(
    creds_file: Path,
    db_name: str,
) -> dict[str, str]:
    """Читает реквизиты подключения из SQLite."""
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
    """Подключается к PostgreSQL."""
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
    """Подготавливает имена столбцов и их SQL-типы."""
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
    """Пересоздаёт таблицу PostgreSQL и записывает данные."""
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
                tuple(to_native(value) for value in row)
                for row in df.itertuples(index=False, name=None)
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
