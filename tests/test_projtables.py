#Version 9/3/24
#python -m pytest test_projtables.py -v -s
#2345678901234567890123456789012345678901234567890123456789012345678901234567890

import sys, os
import pandas as pd
import pytest
import inspect

# Import the class to be tested and mockup driver class
current_dir = os.path.dirname(os.path.abspath(__file__))
libs_dir = os.path.dirname(current_dir) +  os.sep + 'libs' + os.sep
if not libs_dir in sys.path: sys.path.append(libs_dir)
from projtables import ProjectTables, Table
from projtables import RowMajorTbl
from projfiles import Files


"""
=========================================================================
Tests of ProjectTables class and methods

=========================================================================
"""
import pytest

@pytest.fixture
def files():
    """
    Instance files class to track file names/paths
    """
    proj_abbrev = ''
    subdir_home, subdir_tests = 'test_data', 'test_data'
    return Files(proj_abbrev, subdir_home=subdir_home, IsTest=True, \
                 subdir_tests=subdir_tests)
@pytest.fixture
def tbls():
    pf = 'test_data/demo.xlsx'
    sht1, sht2, sht3 = 'raw_table', 'first_sheet', 'second_sheet'
    idx_col_name = 'idx'
"""
=========================================================================
"""
#Stop 9/3/24 15:00
# ready for additional tests of ProjectTables class
# 1. instance class
# 2. import tables
# 3. import and parse raw table

def test_ProjectTables_files(files):
    """
    files fixture
    """
    #Check tests folder path and data folder path
    lst_path_tests = files.path_tests.split(os.sep)
    lst_expected_tests = ['Python_ProjTables', 'tests', '']
    assert lst_path_tests[-3:] == lst_expected_tests    

    lst_path_data = files.path_data.split(os.sep)
    lst_expected_data = ['Python_ProjTables', 'tests', 'test_data', '']
    assert lst_path_data[-4:] == lst_expected_data    
"""
=========================================================================
Tests of Table class and methods
=========================================================================
"""
@pytest.fixture
def Table2():
    """
    three-column table
    """
    pf = 'test_data/demo.xlsx'
    name, sht, idx_col_name = 'Table2', 'second_sheet', 'idx'
    return Table(pf, name, sht, idx_col_name)

@pytest.fixture
def Table3():
    """
    three-column table with extraneous Excel formatting/.UsedRange
    """
    pf = 'test_data/demo.xlsx'
    name, sht, idx_col_name = 'Table2', 'third_sheet', 'idx'
    return Table(pf, name, sht, idx_col_name)

@pytest.fixture
def Table4():
    """
    three-column table with extraneous data columns after last_col
    (dParseParams['col_last_df'] specifies last column to retain)
    """
    pf = 'test_data/demo.xlsx'
    name, sht, idx_col_name = 'Table2', 'fourth_sheet', 'idx'
    dParseParams = {}
    dParseParams['col_last_df'] = 'col_2'
    return Table(pf, name, sht, idx_col_name, dParseParams)
"""
=========================================================================
"""
def test_Table_ResetDefaultIndex1(Table2):
    """
    Set or Reset df index to the default defined for the table
    (Case where idx_col_name is specified)
    JDL 9/3/24
    """
    Table2.ImportExcelDf()
    Table2.ResetDefaultIndex()
    assert Table2.df.index.name == 'idx'
    assert list(Table2.df.columns) == ['col_1', 'col_2']

def test_Table_ResetDefaultIndex2(Table2):
    """
    Set or Reset df index to the default defined for the table
    (Case where idx_col_name is None)
    JDL 9/3/24
    """
    Table2.ImportExcelDf()
    Table2.idx_col_name = None
    Table2.ResetDefaultIndex()
    assert Table2.df.index.name is None
    assert list(Table2.df.columns) == ['idx', 'col_1', 'col_2']

def test_Table_ResetDefaultIndex3(Table2):
    """
    Set or Reset df index to the default defined for the table
    (Case where 'col_1' is initially set as index. It gets dropped)
    JDL 9/3/24
    """
    #Import to .df and set non-default index
    Table2.ImportExcelDf()
    Table2.df.set_index('col_1', inplace=True)

    #Reset to default index with IsDrop=True; col_1 should be dropped
    Table2.ResetDefaultIndex()
    assert Table2.df.index.name == 'idx'
    assert list(Table2.df.columns) == ['col_2']

def test_Table_ResetDefaultIndex4(Table2):
    """
    Set or Reset df index to the default defined for the table
    (Case where 'col_1' is initially set as index. IsDrop=False)
    JDL 9/3/24
    """

    #Import to .df and set non-default index
    Table2.ImportExcelDf()
    Table2.df.set_index('col_1', inplace=True)

    #Reset to default index with IsDrop=False; col_1 should be retained
    Table2.ResetDefaultIndex(IsDrop=False)
    assert Table2.df.index.name == 'idx'
    assert list(Table2.df.columns) == ['col_1','col_2']

def test_Table_ImportExcelDf2(Table2):
    """
    Import rows/cols homed table data from Excel to .df
    JDL 9/3/24
    """
    Table2.ImportExcelDf()
    assert list(Table2.df.columns) == ['idx', 'col_1', 'col_2']
    assert len(Table2.df) == 5

def test_Table_ImportExcelDf3(Table3):
    """
    Import rows/cols homed table data from Excel to .df
    (Case where extraneous Excel formatting/.UsedRange)
    JDL 9/3/24
    """
    #Check effect of extraneous formatting
    df = pd.read_excel(Table3.pf, sheet_name=Table3.sht)
    assert list(df.columns) == ['idx', 'col_1', 'col_2', 'Unnamed: 3', 'Unnamed: 4']
    
    #Import with use of pd_util.dfExcelImport to drop extraneous columns
    Table3.ImportExcelDf()
    assert list(Table3.df.columns) == ['idx', 'col_1', 'col_2']
    assert len(Table3.df) == 5

def test_Table_ImportExcelDf4(Table4):
    """
    Import rows/cols homed table data from Excel to .df
    (Case where dParseParams truncates columns)
    JDL 9/3/24
    """
    #Check effect of extraneous formatting
    df = pd.read_excel(Table4.pf, sheet_name=Table4.sht)
    assert list(df.columns) == ['idx', 'col_1', 'col_2', 'extra_1', 'extra_2']

    Table4.ImportExcelDf()
    assert list(Table4.df.columns) == ['idx', 'col_1', 'col_2']
    assert len(Table4.df) == 5

def test_Table_initialization_Table2(Table2):
    """
    Test initialization of Table2 instance
    JDL 9/3/24
    """
    assert isinstance(Table2, Table)
    assert Table2.pf == 'test_data/demo.xlsx'
    assert Table2.name == 'Table2'
    assert Table2.sht == 'second_sheet'
    assert Table2.idx_col_name == 'idx'
    assert Table2.dParseParams is None