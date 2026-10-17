import os
import pandas as pd
from pygbif import occurrences

BEETLES_ORDER_KEY = 1470

def fetch_beetles_data():
    print("Запрос данных из открытой научной базы GBIF")
    
    try:
        response = occurrences.search(orderKey=BEETLES_ORDER_KEY, limit=100, hasCoordinate=True)
        results = response.get("results", [])
    except Exception as e:
        print(f"Не удалось получить данные из API GBIF: {e}")
        return pd.DataFrame()

    records = []
    for row in results:
        records.append({"scientific_name": row.get("scientificName"),
            "family": row.get("family", "Unknown"),
            "genus": row.get("genus", "Unknown"),
            "country": row.get("country"),
            "latitude": row.get("decimalLatitude"),
            "longitude": row.get("decimalLongitude"),
            "year": row.get("year")})

    df = pd.DataFrame(records)
    
    if not df.empty:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    
    return df

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "beetles_dataset.csv")

    df_beetles = fetch_beetles_data()

    if not df_beetles.empty:
        df_beetles.to_csv(output_path, index=False)
        print(df_beetles.head(18))
      
