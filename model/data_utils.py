# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 15:25:04 2022

@author: Thomas Ball
"""
import os
import pandas as pd
import sys

def file_list(**kwargs): 
    """
    Lists the complete path of all files. Will explore all directories in the
    parent directory.
    target_dir = "$directory_path"  # target a specific directory, otherwise
                                    # uses working directory
    search = "$search_terms"    # returns files containing the string only, if
                                # a list is passed, uses AND not OR.
    """
    f = []
    if "target_dir" in kwargs.keys():
        target_dir = kwargs["target_dir"]
    else:
        target_dir = os.getcwd()
    for path, subdirs, files in os.walk(target_dir):
        for name in files:
            f.append(os.path.join(path, name))
    if "search" in kwargs.keys():
        if type(kwargs["search"]) == str:
            f = [file for file in f if kwargs["search"] in file]
        if type(kwargs["search"]) == list:
            for term in kwargs["search"]:
                f = [file for file in f if term in file]
    return f

def get_item_codes(datPath):
    item_code_path = os.path.join(datPath, 
                                  "dat", "SUA_Crops_Livestock_E_ItemCodes.csv")
    codes = pd.read_csv(os.path.join(item_code_path), encoding = "latin-1")
    return codes
    
def get_area_codes(datPath):
    """
    from https://www.fao.org/nocs/en/
    Filtering this dataset seems to alter the order that they appear in the
    .csv, so only use a 'freshly' downloaded version
    """
    nocs_file = os.path.join(datPath,
                             "dat","nocsDataExport_20220822-151738.xlsx")
    codes = pd.read_excel(nocs_file)
    return codes

def get_provenance_matrix_feed(year, datPath):
    """
    Checks for and then loads the consumption-provenance matrix for a given
    year, as calculated using the R-scripts provided in the SOM of 
    https://doi.org/10.1007/s11625-022-01138-7

    """
    prefix = "TradeMatrixFeed_import_dry_matter_"
    year_str = str(year)
    file_name = prefix + year_str + ".csv"
    file_path = os.path.join(datPath,"dat",file_name)
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        sys.exit(f"""Couldn't find {file_name} in {datPath}""")
    return df

def get_provenance_matrix_nofeed(year, datPath):
    """
    Checks for and then loads the consumption-provenance matrix for a given
    year, as calculated using the R-scripts provided in the SOM of 
    https://doi.org/10.1007/s11625-022-01138-7

    """
    prefix = "TradeMatrix_import_dry_matter_"
    year_str = str(year)
    file_name = prefix + year_str + ".csv"
    file_path = os.path.join(datPath,"dat",file_name)
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        sys.exit(f"""Couldn't find {file_name} in {datPath}""")
    return df

def get_wwf_pbd(datPath):
    file_name = "Planet-Based Diets - Data and Viewer.xlsx"
    sheet_name = "DATA - Product Level"
    file_path = os.path.join(datPath,"dat", file_name)
    if os.path.exists(file_path):
        df = pd.read_excel(file_path, sheet_name = sheet_name)
    else:
        sys.exit(f"""Couldn't find {file_name} in {os.path.join(datPath, "dat")}""")
    return df

def fbs_sua_item_codes(datPath):
    try:
        import model._create_code_list as _create_code_list
    except ModuleNotFoundError:
        import _create_code_list
    code_list = _create_code_list.return_list(datPath)
    return code_list

def split_item_str(string):
    replace = ["/"," ","and","(",")","&",",",";"]
    for item in replace:
        string = string.replace(item, ".")
    splits = string.split(".")
    while "" in splits:
        splits.remove("")
    return splits

        
    