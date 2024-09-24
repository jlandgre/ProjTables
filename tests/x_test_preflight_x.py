#Version 9/3/24
#python -m pytest test_projtables.py -v -s
import sys, os
import pandas as pd
import pytest
import inspect

# Import the classes to be tested
pf_thisfile = inspect.getframeinfo(inspect.currentframe()).filename
path_libs = os.sep.join(os.path.abspath(pf_thisfile).split(os.sep)[0:-2]) + os.sep + 'libs' + os.sep
if not path_libs in sys.path: sys.path.append(path_libs)

from projfiles import Files
from projtables import ProjectTables
from projtables import CheckInputs
import pd_util

#from preflight import CheckExcelFiles
from preflight import CheckTblDataFrame
#from error_handling import ErrorHandle

"""
================================================================================
Tests of ProjectTables class
================================================================================
"""
subdir_tests = 'tbls_test_data'

@pytest.fixture
def files():
    return Files('tbls', IsTest=True, subdir_tests=subdir_tests)

@pytest.fixture
def tbls(files):
    tbls = ProjectTables(files, ['tbl1.xlsx', 'tbl2.xlsx'])
    tbls.ImportInputs()
    return tbls

@pytest.fixture
def df_errs(files):
    """
    Return error_codes file as a DataFrame for use in checking messages
    JDL Modified 2/7/24
    """
    return pd.read_excel(files.pathfile_error_codes, sheet_name='Errors_').set_index('iCode')

@pytest.fixture
def ckinp(tbls):
    return CheckInputs(tbls, IsPrint=True)

@pytest.fixture
def ckinp_tbl1(ckinp, files, tbls):
    """
    Instance preflight.CheckTblDataFrame for tbls.tbl1.df
    Set custom error code lookup key
    """
    ckinp.ckdf = CheckTblDataFrame(files.path_data, tbls.tbl1, 
                                   IsCustomCodes=True, IsPrint=ckinp.IsPrint)
    ckinp.ckdf.errs.Locn = 'tbl1Procedure'
    return ckinp

@pytest.fixture
def ckinp_tbl2(ckinp, files, tbls):
    """
    Instance preflight.CheckTblDataFrame for tbls.tbl2.df
    Set custom error code lookup key
    """
    ckinp.ckdf = CheckTblDataFrame(files.path_data, tbls.tbl2, 
                                   IsCustomCodes=True, IsPrint=ckinp.IsPrint)
    ckinp.ckdf.errs.Locn = 'tbl2Procedure'
    return ckinp



"""
================================================================================
"""

def test_tbl1_ContainsRequiredCols1(ckinp_tbl1):
    """
    tbls.tbl1.df has required columns (case where no error)
    JDL 2/16/24
    """
    assert ckinp_tbl1.ckdf.ContainsRequiredCols()
    assert ckinp_tbl1.ckdf.errs.IsErr == False

def test_tbl1_ContainsRequiredCols2(ckinp_tbl1, files, df_errs):
    """
    tbls.tbl1.df has required columns (error due to missing column)
    JDL 2/16/24
    """
    set_alt_tbl_df(ckinp_tbl1.ckdf.tbl, files, 'tbl1_1.xlsx', 'first_sheet')

    assert not ckinp_tbl1.ckdf.ContainsRequiredCols()
    check_result(ckinp_tbl1, True, 501, 'col_2', df_errs)

    assert ckinp_tbl1.ckdf.errs.IsErr == True

def test_tbl1_NoDuplicateCols1(ckinp_tbl1):
    """
    tbls.tbl1.df does not have duplicate columns (case where no error)
    JDL 2/16/24
    """
    assert ckinp_tbl1.ckdf.NoDuplicateCols()
    assert ckinp_tbl1.ckdf.errs.IsErr == False

def test_tbl1_NoDuplicateCols2(ckinp_tbl1, files, df_errs):
    """
    tbls.tbl1.df does not have duplicate columns (error due to duplicate column exists)
    JDL 2/16/24
    """
    set_alt_tbl_df(ckinp_tbl1.ckdf.tbl, files, 'tbl1_2.xlsx', 'first_sheet')

    assert not ckinp_tbl1.ckdf.NoDuplicateCols()
    check_result(ckinp_tbl1, True, 502, 'col_1', df_errs)

def test_tbl1_NoDuplicateIndices1(ckinp_tbl1):
    """
    tbls.tbl1.df does not have duplicate row indices (case where no error)
    JDL 2/16/24
    """
    #Set the index and check for duplicates
    ckinp_tbl1.ckdf.tbl.ResetDefaultIndex()
    assert ckinp_tbl1.ckdf.NoDuplicateIndices()
    assert ckinp_tbl1.ckdf.errs.IsErr == False

def test_tbl1_NoDuplicateIndices2(ckinp_tbl1, files, df_errs):
    """
    tbls.tbl1.df does not have duplicate row indices (error due to duplicate index)
    JDL 2/16/24
    """
    set_alt_tbl_df(ckinp_tbl1.ckdf.tbl, files, 'tbl1_3.xlsx', 'first_sheet')

    #Set the index and check for duplicates
    ckinp_tbl1.ckdf.tbl.ResetDefaultIndex()
    assert not ckinp_tbl1.ckdf.NoDuplicateIndices()
    check_result(ckinp_tbl1, True, 503, 'Duplicate indices: 2', df_errs)

def test_tbl1_ColPopulated1(ckinp_tbl1):
    """
    tbls.tbl1.df no blank values in specified column (case where no error)
    JDL 2/16/24
    """
    #Check for blanks in an individual column
    assert ckinp_tbl1.ckdf.ColPopulated('idx')
    assert ckinp_tbl1.ckdf.errs.IsErr == False

def test_tbl1_ColPopulated2(ckinp_tbl1, files, df_errs):
    """
    tbls.tbl1.df no blank values in specified column (error due to blank value)
    JDL 2/16/24
    """
    set_alt_tbl_df(ckinp_tbl1.ckdf.tbl, files, 'tbl1_4.xlsx', 'first_sheet')

    #Check for blanks in an individual column
    assert not ckinp_tbl1.ckdf.ColPopulated('col_2')
    check_result(ckinp_tbl1, True, 504, 'col_2', df_errs)

def test_tbl1_LstColsPopulated1(ckinp_tbl1):
    """
    list of tbl.populated_cols populated with non-blank values (case where no error)
    JDL 2/16/24
    """
    #Iterate over tbl.populated_cols and check for blanks in all columns
    assert ckinp_tbl1.ckdf.LstColsPopulated()
    assert ckinp_tbl1.ckdf.errs.IsErr == False

def test_tbl1_LstColsPopulated2(ckinp_tbl1, files, df_errs):
    """
    list of tbl.populated_cols populated with non-blank values  (error due to blank value)
    JDL 2/16/24
    """

    set_alt_tbl_df(ckinp_tbl1.ckdf.tbl, files, 'tbl1_4.xlsx', 'first_sheet')
    ckinp_tbl1.ckdf.tbl.populated_cols = ['idx', 'col_2']

    #Iterate over tbl.populated_cols and check for blanks in all columns
    assert not ckinp_tbl1.ckdf.LstColsPopulated()
    check_result(ckinp_tbl1, True, 504, 'col_2', df_errs)

def test_tbl1_ColumnsContainListVals1(ckinp_tbl1):
    """
    tbls.tbl1.df column names contain specified values (case where no error)
    JDL 2/16/24
    """
    lst = ['col_1', 'col_2']

    #Set the index and check for lst values in column names
    ckinp_tbl1.ckdf.tbl.ResetDefaultIndex()
    assert ckinp_tbl1.ckdf.ColumnsContainListVals(lst)
    assert ckinp_tbl1.ckdf.errs.IsErr == False

def test_tbl1_ColumnsContainListVals2(ckinp_tbl1, df_errs):
    """
    tbls.tbl1.df column names contain specified values (error due val not in column names)
    JDL 2/16/24
    """
    lst = ['col_4']

    #Set the index and check for lst values in column names
    ckinp_tbl1.ckdf.tbl.ResetDefaultIndex()
    assert not ckinp_tbl1.ckdf.ColumnsContainListVals(lst)
    check_result(ckinp_tbl1, True, 505, 'Missing: col_4', df_errs)

def test_tbl1_IndexContainsListVals1(ckinp_tbl1):
    """
    tbls.tbl1.df index contains specified values (case where no error)
    JDL 2/16/24
    """
    lst = [1, 2]

    #Set the index and check for duplicates
    ckinp_tbl1.ckdf.tbl.ResetDefaultIndex()
    assert ckinp_tbl1.ckdf.IndexContainsListVals(lst)
    assert ckinp_tbl1.ckdf.errs.IsErr == False

def test_tbl1_IndexContainsListVals2(ckinp_tbl1, df_errs):
    """
    tbls.tbl1.df index contains specified values (error due val not in omdex)
    JDL 2/16/24
    """
    lst = [1, 2, 10]

    #Set the index and check for duplicates
    ckinp_tbl1.ckdf.tbl.ResetDefaultIndex()
    assert not ckinp_tbl1.ckdf.IndexContainsListVals(lst)
    check_result(ckinp_tbl1, True, 506, 'Missing: 10', df_errs)

def test_tbl1_ColNonBlank1(ckinp_tbl1):
    """
    tbls.tbl1.df has at least one non-blank in specified column (case where no error)
    JDL 2/16/24
    """
    #Check that individual column is non-blank
    assert ckinp_tbl1.ckdf.ColNonBlank('col_1')
    assert ckinp_tbl1.ckdf.errs.IsErr == False

def test_tbl1_ColNonBlank2(ckinp_tbl1, files, df_errs):
    """
    tbls.tbl1.df has at least one non-blank in specified column 
    (case where error due to all blank)
    JDL 2/16/24
    """
    set_alt_tbl_df(ckinp_tbl1.ckdf.tbl, files, 'tbl1_5.xlsx', 'first_sheet')

    #Check for blanks in an individual column
    assert not ckinp_tbl1.ckdf.ColNonBlank('col_1')
    check_result(ckinp_tbl1, True, 507, 'col_1', df_errs)

def test_tbl1_LstColsAllNonBlank1(ckinp_tbl1):
    """
    list of tbl.populated_cols populated with non-blank values (case where no error)
    JDL 2/16/24
    """
    #Iterate over tbl.populated_cols and check for blanks in all columns
    assert ckinp_tbl1.ckdf.LstColsAllNonBlank()
    assert ckinp_tbl1.ckdf.errs.IsErr == False

def test_tbl1_LstColsAllNonBlank2(ckinp_tbl1, files, df_errs):
    """
    list of tbl.populated_cols populated with non-blank values  (error due to blank value)
    JDL 2/16/24
    """
    set_alt_tbl_df(ckinp_tbl1.ckdf.tbl, files, 'tbl1_5.xlsx', 'first_sheet')

    #Iterate over tbl.populated_cols and check for blanks in all columns
    assert not ckinp_tbl1.ckdf.LstColsAllNonBlank()
    check_result(ckinp_tbl1, True, 507, 'col_1', df_errs)

def test_tbl1_ColNumeric1(ckinp_tbl1):
    """
    tbls.tbl1.df specified column contains all numeric values (case where no error)
    JDL 2/16/24
    """
    #Check that values in individual column are all numeric
    assert ckinp_tbl1.ckdf.ColNumeric('col_1')
    assert ckinp_tbl1.ckdf.errs.IsErr == False

def test_tbl1_ColNumeric2(ckinp_tbl1, files, df_errs):
    """
    tbls.tbl1.df specified column contains all numeric values
    (case where error due non-numeric value)
    JDL 2/16/24
    """
    set_alt_tbl_df(ckinp_tbl1.ckdf.tbl, files, 'tbl1_6.xlsx', 'first_sheet')

    #Check that values in individual column are all numeric
    assert not ckinp_tbl1.ckdf.ColNumeric('col_1')
    check_result(ckinp_tbl1, True, 508, 'col_1', df_errs)

def test_tbl1_LstColsAllNumeric1(ckinp_tbl1):
    """
    list of tbl.numeric_cols all populated with numeric values (case where no error)
    JDL 2/16/24
    """
    #Iterate over tbl.populated_cols and check for blanks in all columns
    assert ckinp_tbl1.ckdf.LstColsAllNumeric()
    assert ckinp_tbl1.ckdf.errs.IsErr == False

def test_tbl1_LstColsAllNumeric2(ckinp_tbl1, files, df_errs):
    """
    tbls.tbl1.df specified column values are within a specified numeric range
    JDL 2/16/24
    """
    set_alt_tbl_df(ckinp_tbl1.ckdf.tbl, files, 'tbl1_6.xlsx', 'first_sheet')

    #Iterate over tbl.populated_cols and check for blanks in all columns
    assert not ckinp_tbl1.ckdf.LstColsAllNumeric()
    check_result(ckinp_tbl1, True, 508, 'col_1', df_errs)

def test_tbl1_ColValsInNumericRange1(ckinp_tbl1):
    """
    tbls.tbl1.df specified column values are within a specified numeric range
    JDL 2/19/24
    """
    #Column values are within a numeric range (less than or equal; greater than or equal)
    llim, ulim = 0, 100
    assert ckinp_tbl1.ckdf.ColValsInNumericRange('col_1', llim, ulim)
    assert ckinp_tbl1.ckdf.errs.IsErr == False

def test_tbl1_ColValsInNumericRange2(ckinp_tbl1, files, df_errs):
    """
    tbls.tbl1.df specified column values are within a specified numeric range
    (case where no error)
    JDL 2/19/24
    """
    #Contains value less than or equal to llim
    set_alt_tbl_df(ckinp_tbl1.ckdf.tbl, files, 'tbl1_7.xlsx', 'first_sheet')

    #Check for out-of-range values
    ll, ul = 0, 50
    assert not ckinp_tbl1.ckdf.ColValsInNumericRange('col_1', llim=ll, ulim=ul)
    check_result(ckinp_tbl1, True, 509, 'col_1', df_errs)

def test_tbl1_ColValsInNumericRange3(ckinp_tbl1, files, df_errs):
    """
    tbls.tbl1.df specified column values are within a specified numeric range
    (case where error due to value less than llim)
    JDL 2/19/24
    """
    set_alt_tbl_df(ckinp_tbl1.ckdf.tbl, files, 'tbl1_8.xlsx', 'first_sheet')

    #Check for out-of-range values
    ll, ul = 0, 50
    assert not ckinp_tbl1.ckdf.ColValsInNumericRange('col_1', llim=ll, ulim=ul)
    check_result(ckinp_tbl1, True, 509, 'col_1', df_errs)

def test_tbl1_ColValsInNumericRange4(ckinp_tbl1, files, df_errs):
    """
    tbls.tbl1.df specified column values are within a specified numeric range
    (case where llim not specified; error due to value greater than ulim)
    JDL 2/19/24
    """
    set_alt_tbl_df(ckinp_tbl1.ckdf.tbl, files, 'tbl1_8.xlsx', 'first_sheet')

    #Check for out-of-range values
    ul = 50
    assert not ckinp_tbl1.ckdf.ColValsInNumericRange('col_1', ulim=ul)
    check_result(ckinp_tbl1, True, 509, 'col_1', df_errs)

def test_tbl1_LstColsAllInNumericRange1(ckinp_tbl1, tbls):
    """
    tbls.tbl1.df list of columns' values are within a specified numeric range
    JDL 2/19/24
    """
    #Set attributes to hard-coded values with tuple syntax (col_list, (ll, ul))
    tbls.SetCustomRangeChecks()
    lst = ['idx', 'col_1']
    ll, ul = tbls.tbl1.check_0to50_numeric_range[1]
    assert lst == ['idx', 'col_1']
    assert ll == 0
    assert ul == 50

    #Iterate over tbl.populated_cols and check values for lst are within specified range
    assert ckinp_tbl1.ckdf.LstColsAllInNumericRange(lst, llim=ll, ulim=ul)
    assert ckinp_tbl1.ckdf.errs.IsErr == False

def test_tbl1_LstColsAllInNumericRange2(ckinp_tbl1, files, df_errs):
    """
    tbls.tbl1.df list of columns' values are within a specified numeric range
    (case where llim not specified; error due to value greater than ulim)
    JDL 2/19/24
    """
    set_alt_tbl_df(ckinp_tbl1.ckdf.tbl, files, 'tbl1_7.xlsx', 'first_sheet')

    #Iterate over tbl.populated_cols and check values for lst are within specified range
    ll, ul = 0, 50
    assert not ckinp_tbl1.ckdf.LstColsAllInNumericRange(['idx', 'col_1'], llim=ll, ulim=ul)
    check_result(ckinp_tbl1, True, 509, 'col_1', df_errs)

def test_tbl2_ColValsMatchRegex1(ckinp_tbl2, files, tbls):
    """
    .tbl2.df to check that values match specified regex pattern (case where no error)
    JDL 3/1/24
    """
    #Check for values in individual column that match regex pattern
    assert ckinp_tbl2.ckdf.ColValsMatchRegex('col_2', r'FC [TB] \w+', 
                                             IgnoreCase=True)
    assert ckinp_tbl2.ckdf.errs.IsErr == False

def test_tbl2_ColValsMatchRegex2(ckinp_tbl2, files, df_errs):
    """
    .tbl2.df to check that values match specified regex pattern (case where no error)
    JDL 3/1/24
    """
    set_alt_tbl_df(ckinp_tbl2.ckdf.tbl, files, 'tbl2_1.xlsx', 'first_sheet')

    #Check for values in individual column that match regex pattern
    assert not ckinp_tbl2.ckdf.ColValsMatchRegex('col_2', r'FC [TB] \w+', 
                                             IgnoreCase=True)
    check_result(ckinp_tbl2, True, 530, 'col_2', df_errs)
"""
================================================================================
"""
def test_tbl1_CustomSelectionFilters(tbls):
    """
    Check ability to set a custom selection filter based on tbl1 values
    JDL 2/19/24
    """
    #Test hard-coded filter for col_1 values gt 10 and lt 40
    tbls.SetCustomSelectionFilters()
    assert list(tbls.tbl1.fil_selection.values) == [False, True, True, False, False]

"""
================================================================================
"""
def check_result(ckinp, IsError, err_code, errParam='', df_errs=None):
    """
    Check preflight results
    JDL 2/16/24
    """
    #No error
    if not IsError:
        assert not ckinp.ckdf.errs.IsErr
        assert ckinp.ckdf.errs.Msgs_Accum == ''

    #Error occurred and Msgs_Accum is populated 
    else:
        assert ckinp.ckdf.errs.IsErr
        msg = ckinp.ckdf.errs.Msgs_Accum
        assert msg.startswith(df_errs.loc[err_code, 'Msg_String'])
        assert msg.endswith(errParam)  

def set_alt_tbl_df(tbl, files, testfile, sht):
    """
    Import alternate tbl DataFrame for testing (raw import with range index)
    JDL 2/16/24
    """
    fpath = files.path_data + testfile
    tbl.df = pd_util.dfExcelImport(fpath, sht=sht, IsDeleteBlankCols=True)

"""
#### Steps to Test:
* Instance files = Files() for project
* instance tbls = ProjectTables for lst_files
* instance ckinp = CheckInputs for path_err_codes (based on files) and tbls

#### Procedure Test
* [set_alt_tbl_df(tbls, ckinp.errs, spf, sht)
* assert ckinp.procedure() [pass] or assert not ckinp.procedure() [fail]

#### Individual Check
* ckinp.errs.Locn = 'xxx'
* instance ckdf = preflight.CheckDataFrame(tbls.tbl1.df, ckinp.errs, IsCustomCodes=True)
* assert ckinp.ckdf.method() if simple check with direct call to preflight method
* [or] assert ckinp.method() if more complicated

Can use ckinp.errs.IsErr to track whether an error occurred
"""
def test_files_fixture(files):
    """
    files.path_data is set correctly for testing
    JDL 2/16/24
    """
    lst_path_data = files.path_data.split(os.sep)
    assert lst_path_data[-1] == ''
    assert lst_path_data[-4:-1] == ['Python_ErrorHandling', 'tests', subdir_tests]

def test_tbls_fixture(tbls):
    """
    Test tbls.tbl1.df is imported correctly
    JDL 2/16/24
    """
    assert type(tbls.tbl1.df) == pd.DataFrame
    assert tbls.tbl1.df.shape == (5, 3)

def test_ckinp_fixture(ckinp):
    """
    Check instancing of projtables.CheckInputs fixture for testing
    JDL 2/16/24
    """
    assert ckinp.IsPrint == True

def test_ckinp_tbl1_fixture(ckinp_tbl1):
    """
    Test ckinp_tbl1 fixture
    JDL 2/16/24
    """
    assert ckinp_tbl1.ckdf.errs.Locn == 'tbl1Procedure'
    assert ckinp_tbl1.ckdf.IsCustomCodes == True
    assert ckinp_tbl1.ckdf.IsPrint == True
    assert ckinp_tbl1.ckdf.errs.df_errs.shape[0] > 0
    assert ckinp_tbl1.ckdf.tbl.df.shape == (5, 3)
    assert ckinp_tbl1.ckdf.tbl.required_cols == ['idx', 'col_1', 'col_2']


