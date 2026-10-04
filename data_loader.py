import os
import gdown
import pandas as pd

def load_and_show_data():

    url = "https://docs.google.com/spreadsheets/d/1op5pVvniPLiL88I-HxvgWKKqM0AA2PsP/edit"
    
    output = "dataset_for_DME.csv"

    if not os.path.exists(output):
        gdown.download(url, output, quiet=False)

    df = pd.read_csv(output)

    print(df.head(10))

    return df
