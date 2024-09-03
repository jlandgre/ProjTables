#Version 9/3/24 JDL
import pandas as pd
import numpy as np

def dfExcelImport(sPF, sht=0, skiprows=None, IsDeleteBlankCols=False):
    """
    Import an Excel file optionally from specified sheet; delete extraneous columns
    Modified 12/5/23 to convert column names to strings in case they are integers
    """
    df = pd.read_excel(sPF, sheet_name=sht, skiprows=skiprows)

    #Delete Unnamed columns that result from Excel UsedRange bigger than detected data
    if IsDeleteBlankCols:
        lst_drop = [c for c in df.columns if str(c).startswith('Unnamed:')]
        df = df.drop(lst_drop, axis=1)
    return df

def Df_Roundup(df, n_decimals):
    """
    Roundup df values based on n_decimals precision
    JDL 2/20/23
    """
    df_scale = df * 10**n_decimals
    return np.ceil(df_scale) * 10**(-n_decimals)