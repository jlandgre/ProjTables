#Version 9/3/24 JDL
import os, sys
import pandas as pd
from openpyxl import load_workbook

path_libs = os.getcwd() + os.sep + 'libs' + os.sep
if not path_libs in sys.path: sys.path.append(path_libs)
import pd_util

"""
================================================================================
ProjectTables Class -- this can be initialized as tbls to manage all data
tables for a project. __init__ instances a Table class for each table and
initializes lists column name mapping and for preflight checks

JDL 9/3/24
================================================================================
"""

class ProjectTables():
    """
    Collection of imported or generated data tables for a project
    Customized for importing raw data

    For demo
    * pf_input1 is path + filename to Excel workbook with two sheets
    * Table1 imported from 'raw_table' sheet. It requires parsing (row major raw data)
    * Table2 imported from 'first_sheet' sheet. It requires no parsing
    * Table3 is for validation only. It is same as Table2 but with formatted blank
      cells that cause .UsedRange to include blank columns.

    JDL 9/3/24
    """
    def __init__(self, files, lst_files, IsPrint=False):

        self.IsPrint = IsPrint

        #Create example tables (see demo.ipynb or tests_projtables.py for usage
        self.pf_input1 = files.path_data + lst_files[0]
        self.Table1 = Table(self.spf_input1, 'Table1', 'raw_table', 'idx')
        self.Table2 = Table(self.spf_input2, 'Table2', 'first_sheet', 'idx')
        self.Table3 = Table(self.spf_input2, 'Table3', 'second_sheet', 'idx')

        #Set lists of inputs and outputs
        self.lstImports = [self.Table2]
        self.lstRawImports = [self.Table1]
        self.lstOutputs = []

        #Initialize Output DataFrames
        for tbl in self.lstOutputs:
            tbl.df = pd.DataFrame()

        #Set hard-coded lists of df characteristics
        self.SetColLists()

    def SetColLists(self):
        """
        Set the required columns for each table
        """
        #Map raw data import names to table column names
        self.Table1.import_col_map = {'idx_raw':'idx', 'col #1':'col_1', 'col #2':'col_2'}

        #Lists for preflight checks (example configuration only
        #See https://github.com/jlandgre/Python_ErrorHandling for preflight demos)
        self.Table1.required_cols = ['idx', 'col_1', 'col_2']
        self.Table1.numeric_cols = ['idx', 'col_1']
        self.Table1.populated_cols = ['idx', 'col_2']
        self.Table1.nonblank_cols = ['idx', 'col_1']
    
    def ImportInputs(self):
        """
        Read rows/cols input data - use pd_util.ImportExcel() to avoid importing 
        blank columns in sheet's Excel .UsedRange. Specify 
        tbl.dParseParams['col_last_df'] to specify where to truncate columns
        JDL refactored 9/3/24
        """
        print('\nin import', self.lstImports)
        for tbl in self.lstImports:
            tbl.ImportExcelDf()

            if self.IsPrint:
                print('\nImported', tbl.name, tbl.sPF, tbl.sht)
                print(tbl.df)
    
    def ImportRawInputs(self):
        """
        Read each table's raw data using openpyxl to work on sheets whose data 
        may not start at A1
        JDL 3/4/24
        """
        for tbl in self.lstRawImports:

            #Create workbook object and select sheet
            wb = load_workbook(filename=tbl.sPF, read_only=True)
            ws = wb[tbl.sht]

            # Convert the data to a list and convert to a DataFrame
            data = ws.values
            tbl.df = pd.DataFrame(data)

class Table():
    """
    Attributes for a data table including import instructions and other
    metadaeta. Table instances are attributes of ProjectTables Class
    JDL Modified 8/27/24 add _cols list attribute initialization
    """
    def __init__(self, pf, name, sht, idx_col_name, dParseParams=None):
                
        #Import info: Path+File (sPF), Excel sheet name for import
        self.pf = pf
        self.sht = sht

        #Optional dictionary of parsing parameters for .df or .df_raw
        self.dParseParams = dParseParams

        #Table name (string) and name of default index column
        self.name = name #Table name
        self.idx_col_name = idx_col_name

        #DataFrame and transposed DataFrame
        self.df = None

        self.required_cols = []
        self.numeric_cols = []
        self.populated_cols = []
        self.nonblank_cols = []

    def ImportExcelDf(self):
        """
        Import rows/cols homed table data from Excel to .df
        JDL 9/3/24
        """
        self.df = pd_util.dfExcelImport(self.pf, sht=self.sht, \
                                        IsDeleteBlankCols=True)
        
        #Optionally, drop columns after specified last column
        if self.dParseParams is not None and 'col_last_df' in self.dParseParams:
            col_last = self.dParseParams['col_last_df']
            try:
                idx_last = self.df.columns.get_loc(col_last)
                self.df = self.df.iloc[:, :idx_last+1]
            except KeyError:
                raise ValueError(f"Column {col_last} not found in", self.name)

    def ResetDefaultIndex(self, IsDrop=True):
        """
        Set or Reset df index to the default defined for the table
        JDL 2/20/24; Fix bug with else branch 9/3/24
        """
        if self.idx_col_name is None: return self.df
        if self.df.index.name is None:
            self.df = self.df.set_index(self.idx_col_name)
        else:
            self.df = self.df.reset_index(drop=IsDrop)
            self.df = self.df.set_index(self.idx_col_name)

class CheckInputs:
    """
    Check the tbls dataframes for errors
    (dummy initialization of preflight check)
    """
    def __init__(self, tbls, IsPrint=True):
        self.tbls = tbls
        self.IsPrint = IsPrint

        #preflight.CheckDataFrame Class --instanced as needed in methods below
        self.ckdf = None    

"""
================================================================================
RowMajorTbl Class - for parsing row major raw data
================================================================================
"""
class RowMajorTbl():
    """
    Description and Parsing Row Major Table initially embedded in tbl.df
    (imported with tbls.ImportInputs() or .ImportRawInputs() methods
    JDL 3/4/24
    """
    def __init__(self, dParseParams, tbl):

        #Parsing params (inputs and found during parsing)
        self.dParseParams = dParseParams

        #Raw DataFrame and column list parsed from raw data
        self.df_raw = tbl.df
        self.lst_df_raw_cols = []

        #Table whose df is to be populated by parsing
        self.tbl = tbl

    def ParseTblProcedure(self):
        """
        Parse the table and set self.df resulting DataFrame
        """
        self.FindFlagStartBound()
        self.FindFlagEndBound()
        self.ReadHeader()
        self.SubsetDataRows()
        self.SubsetCols()
        self.RenameCols()

    def FindFlagStartBound(self):
        """
        Find index of flag_start_bound
        JDL 3/4/24
        """
        flag, icol = self.dParseParams['flag_start_bound'], self.dParseParams['icol_start_bound']
        
        # Find the first row index where the flag_start_bound is found
        self.dParseParams['idx_start_bound'] = self.df_raw.iloc[:, icol].eq(flag).idxmax()
        
    def FindFlagEndBound(self):
        """
        Find index of flag_end_bound
        JDL 3/4/24
        """
        flag, icol = self.dParseParams['flag_end_bound'], self.dParseParams['icol_end_bound']

        #Start the search at the first data row based on idata_rowoffset_from_flag
        idx_start = self.dParseParams['idx_start_bound'] + \
            self.dParseParams['idata_rowoffset_from_flag']

        # if flag string indicates search for first null
        if flag == '<blank>':
            idx_end_bound = self.df_raw.iloc[idx_start:, icol].isnull().idxmax()
        else:
            idx_end_bound = self.df_raw.iloc[idx_start:, icol].eq(flag).idxmax()
        self.dParseParams['idx_end_bound'] = idx_end_bound

    def ReadHeader(self):
        """
        Read header based on iheader_rowoffset_from_flag.
        JDL 3/4/24
        """
        # Calculate the header row index
        idx_start = self.dParseParams['idx_start_bound']
        iheader_offset = self.dParseParams['iheader_rowoffset_from_flag']
        idx_header_row =  idx_start + iheader_offset

        # Set the column names
        self.lst_df_raw_cols = list(self.df_raw.iloc[idx_header_row])
        self.dParseParams['idx_header_row'] = idx_header_row

    def SubsetDataRows(self):
        """
        Subset rows based on flags and idata_rowoffset_from_flag.
        JDL 3/4/24
        """
        # Calculate the start index for the data
        idx_start_data = self.dParseParams['idx_start_bound'] + \
            self.dParseParams['idata_rowoffset_from_flag']
        idx_end_bound = self.dParseParams['idx_end_bound']

        # Subset the data rows and set columns
        self.tbl.df = self.df_raw.iloc[idx_start_data:idx_end_bound]
        self.tbl.df.columns = self.lst_df_raw_cols

    def SubsetCols(self):
        """
        Use tbl.import_col_map to subset columns based on header.
        JDL 3/4/24
        """
        cols_keep = list(self.tbl.import_col_map.keys())
        self.tbl.df = self.tbl.df[cols_keep]

    def RenameCols(self):
        """
        Use tbl.import_col_map to rename columns.
        JDL 3/4/24
        """
        self.tbl.df.rename(columns=self.tbl.import_col_map, inplace=True)

    def SetDefaultIndex(self):
        """
        Set the table's default index
        JDL 3/4/24
        """
        self.tbl.df = self.tbl.df.set_index(self.tbl.ColNameIdx)