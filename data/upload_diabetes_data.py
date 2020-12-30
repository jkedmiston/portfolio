"""
Functions to upload the demonstration data based on the diabetes dataset. Some light reconstruction of the code to support categorical naming is used. 
"""
import os
import pandas as pd
from google_functions.google_sheets import upload_df_to_google_sheets


def map_int_to_gender(x):
    gender_map = {1: 'Female',
                  2: 'Male'}
    return gender_map[x]


def upload_diabetes_data():
    """
    The diabetes dataset in sklearn has this as its original source
    https://scikit-learn.org/stable/datasets/toy_dataset.html#diabetes-dataset
    https://web.stanford.edu/~hastie/Papers/LARS/diabetes.data

    This is used as a demo example. 
    """
    df = pd.read_csv("data/diabetes.csv", delimiter="\t")
    url = os.environ["DIABETES_DATA_URL"]
    df["SEX"] = df["SEX"].apply(map_int_to_gender)
    df = df[["AGE", "BMI", "BP", "SEX"]]
    info = upload_df_to_google_sheets(df, url, "Diabetes")
    if info["exit_code"] == 0:
        return
    else:
        print(info["error_message"])
        return


if __name__ == "__main__":
    upload_diabetes_data()
