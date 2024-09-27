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
from projtables import RowMajorBlockID

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
    Procedure to iteratively parse row major blocks
    (parse a raw table containing two blocks)
    JDL 9/26/24
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

    if False: print_tables(row_maj_tbl1_survey)

def test_survey_ReadBlocksProcedure2(row_maj_tbl1_survey):
    """
    Procedure to iteratively parse row major blocks
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

    if False: print_tables(row_maj_tbl1_survey)

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

def test_survey_FindFlagEndBound(row_maj_tbl1_survey):
    """
    Find index of flag_end_bound row
    JDL 9/25/24
    """
    #Locate the start bound indices and truncate to just first
    SetListFirstStartBoundIndex(row_maj_tbl1_survey)
    assert row_maj_tbl1_survey.idx_start_current == 3

    row_maj_tbl1_survey.FindFlagEndBound()
    assert row_maj_tbl1_survey.idx_end_bound == 9

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
Example with one block
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

    #Specify one item tuple to extract a block ID value from above the block
    dParseParams['block_id_vars'] = ('stuff', -4, 2)

    return dParseParams

@pytest.fixture
def tbl1(files, dParseParams_tbl1):
    """
    Table object for survey data
    JDL 9/25/24
    """
    pf = files.path_data + 'tbl1_raw.xlsx'
    tbl = Table(pf, 'Table1', 'raw_table', 'idx', \
                dParseParams_tbl1, import_dtype=None)
    tbl.import_col_map = {'idx_raw':'idx', 'col #1':'col_1', 'col #2':'col_2'}
    tbl.ImportExcelRaw()
    return tbl

@pytest.fixture
def row_maj_tbl1(tbl1):
    """
    Instance RowMajorTbl parsing class for Table1 data
    JDL 9/26/24
    """
    return RowMajorTbl(tbl1)

"""
================================================================================
"""
def test_ReadBlocksProcedure(row_maj_tbl1):
    """
    Procedure to iteratively parse row major blocks
    (parse a raw table containing one block)
    JDL 9/26/24
    """
    row_maj_tbl1.ReadBlocksProcedure()

    #Check the final state of the table
    check_tbl1_values(row_maj_tbl1)

    if False: print_tables(row_maj_tbl1)


def test_SetDefaultIndex(row_maj_tbl1):
    """
    Set default index and check the final state of the table.
    JDL 3/4/24
    """
    # Precursor methods (ReadBlocksProcedure)
    row_maj_tbl1.AddTrailingBlankRow()
    row_maj_tbl1.SetStartBoundIndices()
    for i in row_maj_tbl1.start_bound_indices:
        row_maj_tbl1.idx_start_current = i
        row_maj_tbl1.ParseBlockProcedure()

    row_maj_tbl1.SetDefaultIndex()

    #Extract block_id value specified in dParseParams
    row_maj_tbl1.tbl.df, row_maj_tbl1.lst_block_ids = \
        RowMajorBlockID(row_maj_tbl1.tbl, row_maj_tbl1.idx_start_data).ExtractBlockIDs
    
    #Check the final state of the table
    check_tbl1_values(row_maj_tbl1)

    if False: print_tables(row_maj_tbl1)

def check_tbl1_values(row_maj_tbl1):
    """
    Check the final state of the table.
    JDL 3/4/24
    """
    #Check index name and column names 
    assert row_maj_tbl1.tbl.df.index.name == 'idx'
    assert list(row_maj_tbl1.tbl.df.columns) == ['stuff', 'col_1', 'col_2']

    #Check resulting .tbl.df relative to tbl1_raw.xlsx
    assert len(row_maj_tbl1.tbl.df) == 5
    assert list(row_maj_tbl1.tbl.df.loc[1]) == ['Stuff in C', 10, 'a']
    assert list(row_maj_tbl1.tbl.df.loc[5]) == ['Stuff in C', 50, 'e']

def test_RenameCols(row_maj_tbl1):
    """
    Use tbl.import_col_map to rename columns.
    JDL 3/4/24; Modified 9/26/24
    """
    #Locate the start bound idx    
    row_maj_tbl1.SetStartBoundIndices()
    row_maj_tbl1.idx_start_current = row_maj_tbl1.start_bound_indices[0]

    # Block specific methods
    row_maj_tbl1.FindFlagEndBound()
    row_maj_tbl1.ReadHeader()
    row_maj_tbl1.SubsetDataRows()
    row_maj_tbl1.SubsetCols()
    row_maj_tbl1.RenameCols()

    # Assert that column names are correct after renaming
    lst_expected = ['idx', 'col_1', 'col_2']
    assert list(row_maj_tbl1.df_block.columns) == lst_expected

def test_SubsetCols(row_maj_tbl1):
    """
    Use tbl.import_col_map to subset columns based on header
    JDL 3/4/24; Modified 9/26/24
    """
    #Locate the start bound idx    
    row_maj_tbl1.SetStartBoundIndices()
    row_maj_tbl1.idx_start_current = row_maj_tbl1.start_bound_indices[0]

    # Block specific methods
    row_maj_tbl1.FindFlagEndBound()
    row_maj_tbl1.ReadHeader()
    row_maj_tbl1.SubsetDataRows()
    row_maj_tbl1.SubsetCols()

    # Assert that column names are correct before renaming
    lst_expected =['idx_raw', 'col #1', 'col #2']
    assert list(row_maj_tbl1.df_block.columns) == lst_expected

def test_SubsetDataRows(row_maj_tbl1):
    """
    Subset rows based on flags and idata_rowoffset_from_flag.
    JDL 3/4/24; Modified 9/26/24
    """
    #Locate the start bound idx    
    row_maj_tbl1.SetStartBoundIndices()
    row_maj_tbl1.idx_start_current = row_maj_tbl1.start_bound_indices[0]

    # Block specific methods
    row_maj_tbl1.FindFlagEndBound()
    row_maj_tbl1.ReadHeader()
    row_maj_tbl1.SubsetDataRows()

    # Check resulting .tbl.df relative to tbl1_raw.xlsx
    assert len(row_maj_tbl1.df_block) == 5
    lst_expected = [None, None, 1, 10, 'a']
    check_series_values(row_maj_tbl1.df_block.iloc[0], lst_expected)

    lst_expected = [None, None, 5, 50, 'e']
    check_series_values(row_maj_tbl1.df_block.iloc[-1], lst_expected)

def test_ReadHeader(row_maj_tbl1):
    """
    Read header based on iheader_rowoffset_from_flag.
    JDL 3/4/24; Modified 9/26/24
    """
    #Locate the start bound idx    
    row_maj_tbl1.SetStartBoundIndices()
    row_maj_tbl1.idx_start_current = row_maj_tbl1.start_bound_indices[0]

    # Block specific methods
    row_maj_tbl1.FindFlagEndBound()
    row_maj_tbl1.ReadHeader()

    # Check header row index was set correctly
    assert row_maj_tbl1.idx_header_row == 5

    # Check block's column names
    lst_expected = [None, None, 'idx_raw', 'col #1', 'col #2']
    check_series_values(row_maj_tbl1.cols_df_block, lst_expected)

def test_FindFlagEndBound(row_maj_tbl1):
    """
    Find index of flag_end_bound row
    JDL 3/4/24; Modified 9/26/24
    """
    #Locate the start bound idx    
    row_maj_tbl1.SetStartBoundIndices()
    row_maj_tbl1.idx_start_current = row_maj_tbl1.start_bound_indices[0]

    # Call the method and check result for tbl1_raw.xlsx
    row_maj_tbl1.FindFlagEndBound()
    assert row_maj_tbl1.idx_end_bound == 11

def test_SetStartBoundIndices(row_maj_tbl1):
    """
    Populate .start_bound_indices list of row indices where
    flag_start_bound is found
    JDL 9/26/24
    """
    row_maj_tbl1.SetStartBoundIndices()

    # Expected indices where 'Answer Choices' is found
    expected_indices = [4]

    assert row_maj_tbl1.start_bound_indices == expected_indices

def test_AddTrailingBlankRow(row_maj_tbl1):
    """
    Add a trailing blank row to self.df_raw (to ensure last <blank> flag to
    terminate last block)
    JDL 9/26/24
    """
    assert row_maj_tbl1.df_raw.shape == (13, 5)
    row_maj_tbl1.AddTrailingBlankRow()
    assert row_maj_tbl1.df_raw.shape == (14, 5)

def test_tbl1_fixture(tbl1):
    """
    Test that Table1 data imported correctly
    JDL 9/26/24
    """
    assert tbl1.df_raw.shape == (13, 5)

def test_files_fixture(files):
    """
    Test that the files object was created correctly
    JDL 9/24/24
    """
    assert files.path_data.split(os.sep)[-3:] == ['tests', 'test_data', '']
    assert files.path_scripts.split(os.sep)[-2:] == ['libs', '']
    assert files.path_root.split(os.sep)[-2:] == ['tests', '']
    assert files.path_tests.split(os.sep)[-2:] == ['tests', '']

"""
================================================================================
Helper methods for testing
================================================================================
"""
def print_tables(row_maj_tbl1_survey):
    """
    Helper function to print raw and parsed tables
    JDL 9/25/24
    """
    print('\n\nraw imported table\n', row_maj_tbl1_survey.df_raw)
    print('\nparsed table\n', row_maj_tbl1_survey.tbl.df, '\n\n')

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

"""
================================================================================
RowMajorBlockID Class - sub to RowMajorTbl for extracting block_id values
JDL 9/27/24
================================================================================
"""
def test_blockids_ExtractBlockIDsProcedure1(row_maj_tbl1):
    """
    Procedure to extract block ID values from df_raw
    (One Block_ID variable input as tuple)
    JDL 9/27/24
    """
    #Parse the block's row major data to populate .tbl.df
    create_tbl_df(row_maj_tbl1)

    #Call property to extract block IDs
    tbl = row_maj_tbl1.tbl
    idx_start_data = row_maj_tbl1.idx_start_data
    df, lst = RowMajorBlockID(tbl, idx_start_data).ExtractBlockIDs
    assert lst == ['stuff']
    assert len(df) == 5
    assert list(df.columns) == ['stuff', 'idx', 'col_1', 'col_2']

def test_blockids_ExtractBlockIDsProcedure2(row_maj_tbl1):
    """
    Procedure to extract block ID values from df_raw
    (Two Block_ID variables input as list)
    JDL 9/27/24
    """
    #Parse the block's row major data to populate .tbl.df
    create_tbl_df(row_maj_tbl1)

    #Override default parsing instruction
    lst = [('stuff', -4, 2), ('stuff2', -2, 1)]
    row_maj_tbl1.tbl.dParseParams['block_id_vars'] = lst
        
    #Call property to extract block IDs
    tbl = row_maj_tbl1.tbl
    idx_start_data = row_maj_tbl1.idx_start_data
    df, lst = RowMajorBlockID(tbl, idx_start_data).ExtractBlockIDs

    assert lst == ['stuff', 'stuff2']
    assert len(df) == 5
    assert list(df.columns) == ['stuff', 'stuff2', 'idx', 'col_1', 'col_2']
    assert all(df['stuff'] == 'Stuff in C') 
    assert all(df['stuff2'] == 'flag') 

def test_blockids_ReorderColumns(row_maj_tbl1):
    """
    If only one block_id, it can be specified as tuple; otherwise it's
    a list of tuples.
    JDL 9/27/24
    """
    #Parse the block's row major data to populate .tbl.df
    create_tbl_df(row_maj_tbl1)

    #Instance of RowMajorBlockID
    row_maj_block_id = RowMajorBlockID(row_maj_tbl1.tbl, row_maj_tbl1.idx_start_data)

    #Call methods
    row_maj_block_id.ConvertTupleToList()
    row_maj_block_id.SetBlockIDValue(row_maj_tbl1.tbl.dParseParams['block_id_vars'][0])
    row_maj_block_id.ReorderColumns()
    assert list(row_maj_block_id.tbl.df.columns) == ['stuff', 'idx', 'col_1', 'col_2']

def test_blockids_SetBlockIDValue(row_maj_tbl1):
    """
    If only one block_id, it can be specified as tuple; otherwise it's
    a list of tuples.
    JDL 9/27/24
    """
    #Parse the block's row major data to populate .tbl.df
    create_tbl_df(row_maj_tbl1)

    #Instance of RowMajorBlockID
    row_maj_block_id = RowMajorBlockID(row_maj_tbl1.tbl, row_maj_tbl1.idx_start_data)

    #Call methods
    row_maj_block_id.ConvertTupleToList()
    row_maj_block_id.SetBlockIDValue(row_maj_tbl1.tbl.dParseParams['block_id_vars'][0])

    assert row_maj_block_id.block_id_names == ['stuff']
    assert list(row_maj_block_id.tbl.df.columns) == ['idx', 'col_1', 'col_2', 'stuff']
    assert all(row_maj_block_id.tbl.df['stuff'] == 'Stuff in C') 

def create_tbl_df(row_maj_tbl):
    """
    Helper function to parse raw data to row_maj_tbl.tbl.df
    JDL 9/27/24
    """
    SetListFirstStartBoundIndex(row_maj_tbl)
    row_maj_tbl.ParseBlockProcedure()
    assert len(row_maj_tbl.tbl.df) == 5

def test_blockids_ConvertTupleToList(tbl1):
    """
    If only one block_id, it can be specified as tuple; otherwise it's
    a list of tuples.
    JDL 9/27/24
    """
    #Simulate call after ParseBlockProcedure to set idx_start_data
    row_maj_block_id = RowMajorBlockID(tbl1, 6)

    #Check input from dParseParams fixture
    assert isinstance(tbl1.dParseParams['block_id_vars'], tuple)

    #Call method and check conversion to list
    row_maj_block_id.ConvertTupleToList()
    assert isinstance(tbl1.dParseParams['block_id_vars'], list)

