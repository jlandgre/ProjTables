#Version 9/26/24
#python -m pytest test_parsetables.py -v -s
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
from projtables import ProjectTables
from projtables import Table
from projtables import RowMajorTbl

"""
================================================================================
Importing/Parsing Raw Data with ProjectTables class 
================================================================================
"""
subdir_tests = 'test_data'

@pytest.fixture
def files():
    return Files('tbls', IsTest=True, subdir_tests=subdir_tests)

"""
================================================================================
RowMajorTbl Class - for parsing row major raw data
(Survey Monkey report format)
================================================================================
"""
@pytest.fixture
def dParseParams_tbl1_survey():
    """
    Dictionary of parameters for parsing survey data
    """
    dParseParams = {}
    dParseParams['flag_start_bound'] = 'Answer Choices'
    dParseParams['flag_end_bound'] = '<blank>'
    dParseParams['icol_start_bound'] = 0
    dParseParams['icol_end_bound'] = 0
    dParseParams['iheader_rowoffset_from_flag'] = 0
    dParseParams['idata_rowoffset_from_flag'] = 1
    return dParseParams

@pytest.fixture
def tbl1_survey(files, dParseParams_tbl1_survey):
    """
    Table object for survey data
    JDL 9/25/24
    """
    pf = files.path_data + 'tbl1_survey.xlsx'
    tbl = Table(pf, 'Table1', 'raw_table', 'Answer Choices', \
                dParseParams_tbl1_survey, import_dtype=str)
    tbl.ImportExcelRaw()
    return tbl

@pytest.fixture
def row_maj_tbl1_survey(tbl1_survey):
    """
    Instance RowMajorTbl parsing class for survey data
    JDL 9/25/24
    """
    return RowMajorTbl(tbl1_survey)

"""
================================================================================
"""
def test_survey_ReadBlocksProcedure1(row_maj_tbl1_survey):
    """
    Procedure to find flag_start_bound's and iteratively parse blocks
    (parse a raw table containing two blocks)
    JDL 9/25/24
    """
    row_maj_tbl1_survey.ReadBlocksProcedure()

    #Check that procedure found three blocks
    assert row_maj_tbl1_survey.start_bound_indices == [3, 14, 24]
    assert len(row_maj_tbl1_survey.tbl.df) == 11

    df_check = row_maj_tbl1_survey.tbl.df.reset_index(drop=False)

    lst_expected = ['Daily', '14.13%', '76', np.nan, np.nan, np.nan]
    check_series_values(df_check.iloc[0], lst_expected)
    lst_expected =  ['Improved cleaning', np.nan, np.nan, '18', '11', '17']
    check_series_values(df_check.iloc[-1], lst_expected)

    if True: print_tables(row_maj_tbl1_survey)

def test_survey_ReadBlocksProcedure2(row_maj_tbl1_survey):
    """
    Procedure to find flag_start_bound's and iteratively parse blocks
    (parse a raw table containing two blocks)
    Stack the parsed data
    JDL 9/25/24
    """
    row_maj_tbl1_survey.tbl.dParseParams['is_stack_parsed_cols'] = True
    row_maj_tbl1_survey.ReadBlocksProcedure()

    assert len(row_maj_tbl1_survey.tbl.df) == 25

    # Check values in first two and last two rows
    df_check = row_maj_tbl1_survey.tbl.df.reset_index(drop=False)
    lst_expected = ['Daily', 'Response Percent', '14.13%']
    check_series_values(df_check.iloc[0], lst_expected)
    lst_expected = ['Daily', 'Responses', '76']
    check_series_values(df_check.iloc[1], lst_expected)

    lst_expected =  ['Improved cleaning', '3', '17']
    check_series_values(df_check.iloc[-1], lst_expected)
    lst_expected =  ['Improved cleaning', '2', '11']
    check_series_values(df_check.iloc[-2], lst_expected)

    if True: print_tables(row_maj_tbl1_survey)

def test_survey_ParseBlockProcedure1(row_maj_tbl1_survey):
    """
    Parse the survey table and check the final state of the table.
    (1st block)
    JDL 9/25/24
    """

    SetListFirstStartBoundIndex(row_maj_tbl1_survey)
    row_maj_tbl1_survey.ParseBlockProcedure()

    #Check resulting .tbl.df relative to tbl1_survey.xlsx
    assert len(row_maj_tbl1_survey.tbl.df) == 5
    assert list(row_maj_tbl1_survey.tbl.df.iloc[0]) == ['Daily', '14.13%', '76']
    assert list(row_maj_tbl1_survey.tbl.df.iloc[-1]) == ['Rarely', '0.37%', '2']

    if False: print_tables(row_maj_tbl1_survey)

def test_survey_ParseBlockProcedure2(row_maj_tbl1_survey):
    """
    Parse the survey table and check the final state of the table.
    JDL 9/25/24; Modified 9/26/24
    """
    #Add a trailing blank row to .df_raw (last <blank> end flag)
    row_maj_tbl1_survey.AddTrailingBlankRow()

    #Set current start bound index to be last (third) block
    row_maj_tbl1_survey.SetStartBoundIndices()
    row_maj_tbl1_survey.idx_start_current = \
        row_maj_tbl1_survey.start_bound_indices[-1]
    assert row_maj_tbl1_survey.idx_start_current == 24

    row_maj_tbl1_survey.ParseBlockProcedure()

    #Check resulting .tbl.df relative to tbl1_survey.xlsx
    assert len(row_maj_tbl1_survey.tbl.df) == 3
    assert list(row_maj_tbl1_survey.tbl.df.iloc[0]) == ['Lower price point', '91', '33', '19']
    assert list(row_maj_tbl1_survey.tbl.df.iloc[-1]) == ['Improved cleaning', '18', '11', '17']

    if False: print_tables(row_maj_tbl1_survey)

def print_tables(row_maj_tbl1_survey):
    """
    Helper function to print raw and parsed tables
    JDL 9/25/24
    """
    print('\n\nraw imported table\n', row_maj_tbl1_survey.df_raw)
    print('\nparsed table\n', row_maj_tbl1_survey.tbl.df, '\n\n')

def test_survey_SubsetCols(row_maj_tbl1_survey):
    """
    Use tbl.import_col_map to subset columns based on header.
    JDL 9/24/24
    """
    SetListFirstStartBoundIndex(row_maj_tbl1_survey)
    row_maj_tbl1_survey.FindFlagEndBound()
    row_maj_tbl1_survey.ReadHeader()
    row_maj_tbl1_survey.SubsetDataRows()
    row_maj_tbl1_survey.SubsetCols()

    # Assert that column names are correct before renaming
    lst_expected = ['Answer Choices', 'Response Percent', 'Responses']
    assert list(row_maj_tbl1_survey.df_block.columns) == lst_expected

def test_survey_SubsetDataRows(row_maj_tbl1_survey):
    """
    Subset rows based on flags and idata_rowoffset_from_flag.
    JDL 9/24/24
    """
    SetListFirstStartBoundIndex(row_maj_tbl1_survey)
    row_maj_tbl1_survey.FindFlagEndBound()
    row_maj_tbl1_survey.ReadHeader()
    row_maj_tbl1_survey.SubsetDataRows()

    # Check resulting .tbl.df relative to tbl1_raw.xlsx
    assert len(row_maj_tbl1_survey.df_block) == 5
    lst_expected = ['Daily', '14.13%', '76', None, None, None]
    check_series_values(row_maj_tbl1_survey.df_block.iloc[0], lst_expected)

    lst_expected = ['Rarely', '0.37%', '2', None, None, None]
    check_series_values(row_maj_tbl1_survey.df_block.iloc[-1], lst_expected)

def test_survey_ReadHeader(row_maj_tbl1_survey):
    """
    Read header based on iheader_rowoffset_from_flag.
    JDL 9/24/24
    """
    SetListFirstStartBoundIndex(row_maj_tbl1_survey)
    row_maj_tbl1_survey.FindFlagEndBound()
    row_maj_tbl1_survey.ReadHeader()

    # Assert that the header row index was set correctly
    assert row_maj_tbl1_survey.idx_header_row == 3

    #  Check each column name, allowing for NaN comparisons
    lst_expected = ['Answer Choices', 'Response Percent', 'Responses', None, None, None]
    check_series_values(row_maj_tbl1_survey.cols_df_block, lst_expected)

def check_series_values(ser, lst_expected):
    """
    Helper function to check series values allowing for NaN comparisons
    JDL 9/25/24
    """
    for actual, expect in zip(ser, lst_expected):
        if isinstance(expect, float) and np.isnan(expect):
            assert np.isnan(actual)
        else:
            assert actual == expect

def test_survey_FindFlagEndBound(row_maj_tbl1_survey):
    """
    Find index of flag_end_bound row
    JDL 9/25/24
    """
    #Locate the start bound indices and truncate to just first
    SetListFirstStartBoundIndex(row_maj_tbl1_survey)
    assert row_maj_tbl1_survey.idx_start_current == 3

    row_maj_tbl1_survey.FindFlagEndBound()
    assert row_maj_tbl1_survey.tbl.dParseParams['idx_end_bound'] == 9

def SetListFirstStartBoundIndex(row_maj_tbl1_survey):
    """
    Helper test function - set .idx_start_current to first list item
    JDL 9/25/24
    """
    row_maj_tbl1_survey.SetStartBoundIndices()
    row_maj_tbl1_survey.idx_start_current = \
        row_maj_tbl1_survey.start_bound_indices[0]

def test_survey_SetStartBoundIndices(row_maj_tbl1_survey):
    """
    Populate .start_bound_indices list of row indices where
    flag_start_bound is found
    JDL 9/25/24
    """
    row_maj_tbl1_survey.SetStartBoundIndices()

    # Expected indices where 'Answer Choices' is found
    expected_indices = [3, 14, 24]

    assert row_maj_tbl1_survey.start_bound_indices == expected_indices

def test_survey_AddTrailingBlankRow(row_maj_tbl1_survey):
    """
    Add a trailing blank row to self.df_raw (to ensure last <blank> flag to
    terminate last block)
    JDL 9/26/24
    """
    assert row_maj_tbl1_survey.df_raw.shape == (28, 4)
    row_maj_tbl1_survey.AddTrailingBlankRow()
    assert row_maj_tbl1_survey.df_raw.shape == (29, 4)

def test_survey_row_maj_fixture(row_maj_tbl1_survey):    
    """
    Test that raw survey data imported correctly
    JDL 9/24/24
    """
    assert row_maj_tbl1_survey.tbl.df_raw.shape == (28, 4)

def test_survey_tbl1_fixture(tbl1_survey):
    """
    Test that survey data imported correctly
    JDL 9/25/24
    """
    assert tbl1_survey.df_raw.shape == (28, 4)

"""
================================================================================
RowMajorTbl Class - for parsing row major raw data
================================================================================
"""
@pytest.fixture
def tbls(files):
    """
    Using .ImportRawInputs() method to import sheet whose data may not start at A1
    """
    tbls = ProjectTables(files, ['tbl1_raw.xlsx'])
    tbls.ImportRawInputs()
    return tbls

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
    return RowMajorTbl(dParseParams_tbl1, tbls.Table1)

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
    assert tbls.Table1.df.shape == (13, 5)

def test_files_fixture(files):
    """
    Test that the files object was created correctly
    JDL 9/24/24
    """
    assert files.path_data.split(os.sep)[-3:] == ['tests', 'test_data', '']
    assert files.path_scripts.split(os.sep)[-2:] == ['libs', '']
    assert files.path_root.split(os.sep)[-2:] == ['tests', '']
    assert files.path_tests.split(os.sep)[-2:] == ['tests', '']
