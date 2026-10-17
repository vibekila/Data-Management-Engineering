import os
import gdown
import pandas as pd

DATASET_URL = "https://docs.google.com/spreadsheets/d/1op5pVvniPLiL88I-HxvgWKKqM0AA2PsP/export?format=csv"


def cast_types(df):
    numeric_columns = [
        'Ti(s)', 'Te(s)', 'PIF', 'PEF', 'volbal', 'F', 'vt', 
        'mv', 'EF50', 'EIP', 'EEp', 'Penh', 'AV', 'TR', 'Rpef'
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def load_and_show_data(path="dataset_for_DME.csv", parquet_path="dataset_for_DME.parquet"):
    part_path = path + ".part"

    if not os.path.exists(path):
        gdown.download(DATASET_URL, part_path, quiet=False)
        df = pd.read_csv(part_path, sep=None, engine='python')
        os.rename(part_path, path)
    else:
        df = pd.read_csv(path, sep=None, engine='python')

    df = cast_types(df)

    df.to_parquet(parquet_path, index=False)

    print(df.head(10))
    
    return df

if __name__ == "__main__":
    load_and_show_data()
