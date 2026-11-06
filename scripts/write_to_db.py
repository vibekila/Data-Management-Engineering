import os
import sys
import pandas as pd
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

ROWS_COUNT = 100

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
env_path = os.path.join(project_root, '.env')
if not os.path.exists(env_path):
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    env_path = os.path.join(project_root, '.env')

load_dotenv(dotenv_path=env_path)

TABLE_NAME = 'giniyatullinadm' 

parquet_path = os.path.join(project_root, 'dataset_for_DME.parquet')
if not os.path.exists(parquet_path):
    parquet_path = 'dataset_for_DME.parquet'

if not os.path.exists(parquet_path):
    print(
        f"Файл датасета не найден по пути {parquet_path}",
        file=sys.stderr
    )
    sys.exit(1)

df = pd.read_parquet(parquet_path)
df_100 = df.head(ROWS_COUNT)

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

if not all([DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME]):
    raise RuntimeError("Заданы не все переменные окружения.")

conn = None
cursor = None

try:
    print("Попытка подключения к PostgreSQL.")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        connect_timeout=10
    )

    cursor = conn.cursor()
    print("Успешное подключение.")

    clean_columns = [col.replace('(', '_').replace(')', '_').replace('.', '_').lower() for col in df_100.columns]
    
    sql_columns_types = []
    for col_old, col_clean in zip(df_100.columns, clean_columns):
        if pd.api.types.is_numeric_dtype(df_100[col_old]):
            sql_columns_types.append(f"{col_clean} DOUBLE PRECISION")
        else:
            sql_columns_types.append(f"{col_clean} TEXT")

    print(f"Таблица '{TABLE_NAME}' будет удалена и пересоздана.")

    cursor.execute(
        sql.SQL("DROP TABLE IF EXISTS {};").format(
            sql.Identifier(TABLE_NAME)
        )
    )
    
    create_table_query = sql.SQL("CREATE TABLE {} (id SERIAL PRIMARY KEY, {});").format(
        sql.Identifier(TABLE_NAME),
        sql.SQL(", ").join(sql.SQL(col_type) for col_type in sql_columns_types)
    )
    cursor.execute(create_table_query)
    print(f"Таблица '{TABLE_NAME}' успешно пересоздана в PostgreSQL.")

    placeholders = sql.SQL(", ").join([sql.Placeholder()] * len(clean_columns))
    insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({});").format(
        sql.Identifier(TABLE_NAME),
        sql.SQL(", ").join(sql.Identifier(col) for col in clean_columns),
        placeholders
    )
    
    data_records = [tuple(row) for _, row in df_100.iterrows()]
    cursor.executemany(insert_query, data_records)
        
    conn.commit()
    print(f"\n100 строк датасета успешно записаны в удаленную таблицу PostgreSQL '{TABLE_NAME}'.")

except Exception as e:
    print(f"\nПроизошла ошибка при работе с PostgreSQL: {e}")
    if conn:
        conn.rollback()

finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
    print("Соединение с базой данных закрыто.")
