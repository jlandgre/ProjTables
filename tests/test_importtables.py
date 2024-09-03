#Version 3/4/24
#python -m pytest test_importtables.py -v -s
import sys, os
import pandas as pd
import numpy as np
import pytest
import inspect

# Import the classes to be tested
pf_thisfile = inspect.getframeinfo(inspect.currentframe()).filename
path_libs = os.sep.join(os.path.abspath(pf_thisfile).split(os.sep)[0:-2]) + os.sep + 'libs' + os.sep
if not path_libs in sys.path: sys.path.append(path_libs)

print('\n', path_libs)
from projfiles import Files
from projtables_import import ProjectTables
from projtables_import import RowMajorTbl
import pd_util

"""
================================================================================
Importing Raw Data with ProjectTables class 
================================================================================
"""
subdir_tests = 'tbls_import_test_data'

@pytest.fixture
def files():
    return Files('tbls', IsTest=True, subdir_tests=subdir_tests)

@pytest.fixture
def tbls(files):
    """
    Using .ImportRawInputs() method to import sheet whose data may not start at A1
    """
    tbls = ProjectTables(files, ['tbl1_raw.xlsx'])
    tbls.ImportRawInputs()
    return tbls

"""
================================================================================
RowMajorTbl Class - for parsing row major raw data
================================================================================
"""

@pytest.fixture
def dParseParams_tbl1():
    """
    Return a dictionary of parameters for parsing the first table
    """
    dParseParams = {}
    dParseParams['flag_start_bound'] = 'flag'
    dParseParams['flag_end_bound'] = '<blank>'
    dParseParams['icol_start_bound'] = 1
    dParseParams['icol_end_bound'] = 2
    dParseParams['iheader_rowoffset_from_flag'] = 1
    dParseParams['idata_rowoffset_from_flag'] = 2
    return dParseParams

@pytest.fixture
def row_maj_tbl1(tbls, dParseParams_tbl1):
    """
    Return the first table to be tested
    """
    return RowMajorTbl(dParseParams_tbl1, tbls.tbl1)

def test_SetDefaultIndex(row_maj_tbl1):
    """
    Set default index and check the final state of the table.
    JDL 3/4/24
    """
    row_maj_tbl1.FindFlagStartBound()
    row_maj_tbl1.FindFlagEndBound()
    row_maj_tbl1.ReadHeader()
    row_maj_tbl1.SubsetDataRows()
    row_maj_tbl1.SubsetCols()
    row_maj_tbl1.RenameCols()
    row_maj_tbl1.SetDefaultIndex()
    ParseTblProcedureChecks(row_maj_tbl1)

    print('\n\nraw imported table\n')
    print(row_maj_tbl1.df_raw)
    print('\nparsed table\n')
    print(row_maj_tbl1.tbl.df)
    print('\n\n')

def ParseTblProcedureChecks(row_maj_tbl1):
    """
    Helper function to check final state of parsed tbl.df
    JDL 3/4/24
    """
    #Check index name and column names 
    assert row_maj_tbl1.tbl.df.index.name == 'idx'
    assert list(row_maj_tbl1.tbl.df.columns) == ['col_1', 'col_2']

    #Check df dimensions and values
    assert len(row_maj_tbl1.tbl.df) == 5
    assert list(row_maj_tbl1.tbl.df.loc[1]) == [10, 'a']
    assert list(row_maj_tbl1.tbl.df.loc[5]) == [50, 'e']

def test_RenameCols(row_maj_tbl1):
    """
    Use tbl.import_col_map to rename columns.
    JDL 3/4/24
    """
    row_maj_tbl1.FindFlagStartBound()
    row_maj_tbl1.FindFlagEndBound()
    row_maj_tbl1.ReadHeader()
    row_maj_tbl1.SubsetDataRows()
    row_maj_tbl1.SubsetCols()
    row_maj_tbl1.RenameCols()

    # Assert that column names are correct after renaming
    lst_expected = ['idx', 'col_1', 'col_2']
    assert list(row_maj_tbl1.tbl.df.columns) == lst_expected

def test_SubsetCols(row_maj_tbl1):
    """
    Use tbl.import_col_map to subset columns based on header.
    JDL 3/4/24
    """
    row_maj_tbl1.FindFlagStartBound()
    row_maj_tbl1.FindFlagEndBound()
    row_maj_tbl1.ReadHeader()
    row_maj_tbl1.SubsetDataRows()
    row_maj_tbl1.SubsetCols()

    # Assert that column names are correct before renaming
    lst_expected =['idx_raw', 'col #1', 'col #2']
    assert list(row_maj_tbl1.tbl.df.columns) == lst_expected

def test_SubsetDataRows(row_maj_tbl1):
    """
    Subset rows based on flags and idata_rowoffset_from_flag.
    JDL 3/4/24
    """
    row_maj_tbl1.FindFlagStartBound()
    row_maj_tbl1.FindFlagEndBound()
    row_maj_tbl1.ReadHeader()
    row_maj_tbl1.SubsetDataRows()

    # Check resulting .tbl.df relative to tbl1_raw.xlsx
    assert len(row_maj_tbl1.tbl.df) == 5
    assert list(row_maj_tbl1.tbl.df.iloc[0]) == [None, None, 1, 10, 'a']
    assert list(row_maj_tbl1.tbl.df.iloc[-1]) == [None, None, 5, 50, 'e']

def test_ReadHeader(row_maj_tbl1):
    """
    Read header based on iheader_rowoffset_from_flag.
    JDL 3/4/24
    """
    row_maj_tbl1.FindFlagStartBound()
    row_maj_tbl1.FindFlagEndBound()
    row_maj_tbl1.ReadHeader()

    # Assert that the header row index was set correctly
    assert row_maj_tbl1.dParseParams['idx_header_row'] == 5

    # Assert that the column names were read correctly
    lst_expected = [None, None, 'idx_raw', 'col #1', 'col #2']
    assert row_maj_tbl1.lst_df_raw_cols == lst_expected

def test_FindFlagEndBound(row_maj_tbl1):
    """
    Find index of flag_end_bound row
    JDL 3/4/24
    """
    #Locate the start bound idx    
    row_maj_tbl1.FindFlagStartBound()

    # Call the method and check result for tbl1_raw.xlsx
    row_maj_tbl1.FindFlagEndBound()
    assert row_maj_tbl1.dParseParams['idx_end_bound'] == 11

def test_FindFlagStartBound(row_maj_tbl1):
    """
    Find index of flag_start_bound row
    JDL 3/4/24
    """
    #Check the result for tbl1_raw.xlsx
    row_maj_tbl1.FindFlagStartBound()
    assert row_maj_tbl1.dParseParams['idx_start_bound'] == 4

def test_tbls_fixture(tbls):    
    """
    Test that the tbl1_raw.xlsx was imported correctly
    """
    assert tbls.tbl1.df.shape == (13, 5)

