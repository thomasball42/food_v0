# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 16:03:16 2022

@author: Thomas Ball
"""

import os
try:
    import offshoring.data_utils
except ModuleNotFoundError:
    import data_utils
import pandas as pd
import numpy as np

file_name = "FBS and SUA list.xlsx"
file_name_csv = file_name.split(".")[0] + ".csv"

def list_to_csv(datPath):
    file_path_csv = os.path.join(datPath,"dat", file_name_csv)
    df = pd.read_csv(file_path_csv)
    df[df ==""] = np.nan
    df = df.fillna(method = "ffill")
    df = df.dropna(axis = 0)
    df = df.rename(columns = {" Item name " : "Item"})
    df["Item"] = [x.strip() for x in df["Item"]]
    df = df[np.logical_not(df.duplicated("Item"))]
    df = df.drop(columns = "Unnamed: 0")
    file_out = os.path.join(datPath,"dat", "fbs_sua_codes_formatted.csv")
    df.to_csv(file_out)
    return df

def return_list(datPath):
    file_path_csv = os.path.join(datPath,"dat", file_name_csv)
    if os.path.exists(file_path_csv) == True:
        df = pd.read_csv(file_path_csv)
    else:
        df = list_to_csv(datPath)
    return df