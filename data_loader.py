import pandas as pd

def load_and_show_data(path="dataset_for_DME.cvs"):

    df = pd.read_csv(path)

    print(df.head(10))
    
    return df

if __name__ == "__main__":
    load_and_show_data()
