import os
import sys
import pandas as pd
from dotenv import load_dotenv
import psycopg2

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
    print(f"Файл датасета не найден по пути {parquet_path}")
    sys.exit(1)

df = pd.read_parquet(parquet_path)
df_100 = df.head(100)

host = os.getenv('DB_HOST') or "85.193.80.59"
port = os.getenv('DB_PORT') or "5432"
user = os.getenv('DB_USER') or "deexpert"
password = os.getenv('DB_PASS') or "what_a_Wonderful_Day!"
database = os.getenv('DB_NAME') or "homeworks"

conn = None
cursor = None

try:
    print(f"Попытка подключения к PostgreSQL.")
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        connect_timeout=10
    )
    cursor = conn.cursor()
    print("Успешное подключение.")

    clean_columns = [col.replace('(', '_').replace(')', '_').replace('.', '_').lower() for col in df_100.columns]
    
    create_columns_sql = ", ".join([f"{col} DOUBLE PRECISION" for col in clean_columns])
    create_table_query = f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} (id SERIAL PRIMARY KEY, {create_columns_sql});"
    
    cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
    cursor.execute(create_table_query)
    print(f"Таблица '{TABLE_NAME}' успешно пересоздана в PostgreSQL.")

    placeholders = ", ".join(["%s"] * len(clean_columns))
    insert_query = f"INSERT INTO {TABLE_NAME} ({', '.join(clean_columns)}) VALUES ({placeholders});"
    
    for index, row in df_100.iterrows():
        cursor.execute(insert_query, tuple(row))
        
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
