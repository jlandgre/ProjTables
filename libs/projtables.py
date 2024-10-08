#Version 9/26/24 JDL
import os, sys
import pandas as pd
import numpy as np
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

    JDL 9/26/24
    """
    def __init__(self, files, lst_files, IsPrint=False):

        self.IsPrint = IsPrint

        #Create example tables (see demo.ipynb or tests_projtables.py for usage
        self.pf_input1 = files.path_data + lst_files[0]
        self.pf_input2 = ''
        self.pf_input3 = ''

        self.Table1 = Table(self.pf_input1, 'Table1', 'raw_table', 'idx')
        self.Table2 = Table(self.pf_input1, 'Table2', 'first_sheet', 'idx')
        self.Table3 = Table(self.pf_input1, 'Table3', 'second_sheet', 'idx')

        #Set lists of inputs and outputs
        self.lstImports = [self.Table2] #structured Excel data imported to tbl.df
        self.lstRawImports = [self.Table1] #unstructured Excel data to tbl.df_raw
        self.lstOutputs = []

        #Initialize Output DataFrames
        #for tbl in self.lstOutputs:
        #    tbl.df = pd.DataFrame()

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
        for tbl in self.lstImports:
            tbl.ImportExcelDf()

            if self.IsPrint:
                print('\nImported Excel', tbl.name, tbl.pf, tbl.sht)
                print(tbl.df)
    
    def ImportRawInputs(self):
        """
        Read each table's raw data using openpyxl to work on sheets whose data 
        may not start at A1 (e.g. .df_raw requires parsing to .df)
        JDL 3/4/24; Modified 9/25/24
        """
        for tbl in self.lstRawImports:
            tbl.ImportExcelRaw()

            if self.IsPrint:
                print('\nImported Excel Raw', tbl.name, tbl.pf, tbl.sht)
                print(tbl.df)

class Table():
    """
    Attributes for a data table including import instructions and other
    metadaeta. Table instances are attributes of ProjectTables Class
    JDL Modified 9/26/24 add import_dtype argument
    """
    def __init__(self, pf, name, sht, idx_col_name, dParseParams=None, import_dtype=None):
                
        #Import info: Path+File (sPF), Excel sheet name for import
        self.pf = pf
        self.sht = sht

        #Table name (string) and name of default index column
        self.name = name #Table name
        self.idx_col_name = idx_col_name
        self.dParseParams = dParseParams
        self.import_col_map = {} #Map raw import names to df col names
        self.import_dtype = import_dtype #To force str type for imported values

        #Raw (non-parsed) and parsed DataFrames
        self.df_raw = pd.DataFrame()
        self.df = pd.DataFrame()

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

    def ImportExcelRaw(self):
        """
        Import unstructured data to .df_raw for parsing
        JDL Modified 9/26/24 to allow forcing str type for imported values
        """
        #Create workbook object and select sheet
        wb = load_workbook(filename=self.pf, read_only=True)
        ws = wb[self.sht]

        # Convert the data to a list and convert to a DataFrame
        data = ws.values
        self.df_raw = pd.DataFrame(data)

        #Negate Pandas inferring float data type for integers and NaNs for blanks
        if self.import_dtype == str:
            self.df_raw = self.df_raw.applymap(lambda x: None if pd.isna(x) \
                    else str(int(x)) if isinstance(x, float) and x.is_integer() \
                    else str(x))

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
RowMajorTbl Class - for parsing row major raw data single block
================================================================================
"""
class RowMajorTbl():
    """
    Description and Parsing Row Major Table initially embedded in tbl.df
    (imported with tbls.ImportInputs() or .ImportRawInputs() methods
    JDL 3/4/24; Modified 9/26/24
    """
    def __init__(self, tbl):

        #List of df indices for rows where flag_start_bound is found
        self.start_bound_indices = []

        #Raw DataFrame and column list parsed from raw data
        self.df_raw = tbl.df_raw

        #Table whose df is to be populated by parsing
        self.tbl = tbl
        self.lst_block_ids = []

        #Start, header, end, first data row indices for current block in loop
        self.idx_start_current = None
        self.idx_header_row = None
        self.idx_end_bound = None
        self.idx_start_data = None

        #Current block's columns and parsed data
        self.cols_df_block = []
        self.df_block = pd.DataFrame()
    """
    ================================================================================
    """
    def ReadBlocksProcedure(self):
        """
        Procedure to iteratively parse row major blocks
        JDL 9/26/24
        """
        # Append blank row at end of .df_raw (to ensure find last <blank> flag)
        self.AddTrailingBlankRow()

        #Create list of row indices with start bound flag
        self.SetStartBoundIndices()

        #Iteratively read blocks 
        for i in self.start_bound_indices:
            self.idx_start_current = i
            self.ParseBlockProcedure()

        #Extract block_id values if specified
        self.tbl.df, self.lst_block_ids = RowMajorBlockID(self.tbl, \
                                        self.idx_start_data).ExtractBlockIDs

        #set default index
        self.SetDefaultIndex()

        #Optionally stack parsed data (if .dParams['is_stack_parsed_cols']
        self.StackParsedCols()

    def AddTrailingBlankRow(self):
        """
        Add a trailing blank row to self.df_raw (to ensure last <blank> flag to
        terminate last block)
        JDL 9/26/24
        """
        blank_row = pd.Series([np.nan] * len(self.df_raw.columns), index=self.df_raw.columns)
        self.df_raw = pd.concat([self.df_raw, pd.DataFrame([blank_row])], ignore_index=True)

    def SetStartBoundIndices(self):
        """
        Populate list of row indices whereflag_start_bound is found
        JDL 9/25/24
        """
        flag= self.tbl.dParseParams['flag_start_bound']
        icol = self.tbl.dParseParams['icol_start_bound']

        fil = self.df_raw.iloc[:, icol] == flag
        self.start_bound_indices = self.df_raw[fil].index.tolist()

    def SetDefaultIndex(self):
        """
        Set the table's default index
        JDL 3/4/24
        """
        self.tbl.df = self.tbl.df.set_index(self.tbl.idx_col_name)
    
    def StackParsedCols(self):
        """
        Optionally stack parsed columns from row major blocks
        JDL 9/25/24
        """
        is_stack = self.tbl.dParseParams.get('is_stack_parsed_cols', False)

        if is_stack:
            self.tbl.df = self.tbl.df.stack().reset_index()

            #Respecify the index column name and set default index
            self.tbl.df.columns = [self.tbl.idx_col_name, 'Metric', 'Value']
            self.SetDefaultIndex()

    def ParseBlockProcedure(self):
        """
        Parse the table and set self.df resulting DataFrame
        JDL 9/25/24
        """
        self.FindFlagEndBound()
        self.ReadHeader()
        self.SubsetDataRows()
        self.SubsetCols()
        self.RenameCols()

        #Concatenate into tbl.df and re-initialize df_block
        self.tbl.df = pd.concat([self.tbl.df, self.df_block], axis=0)
        self.df_block = pd.DataFrame()

    def FindFlagEndBound(self):
        """
        Find index of flag_end_bound
        JDL 3/4/24; modified 9/26/24
        """
        flag = self.tbl.dParseParams['flag_end_bound']
        icol = self.tbl.dParseParams['icol_end_bound']
        ioffset = self.tbl.dParseParams['idata_rowoffset_from_flag']

        #Start the search at the first data row based on data offset from flag
        i = self.idx_start_current + ioffset

        # search for specifie flag string/<blank> below row i
        if flag == '<blank>':
            self.idx_end_bound = self.df_raw.iloc[i:, icol].isnull().idxmax()
        else:
            self.idx_end_bound = self.df_raw.iloc[i:, icol].eq(flag).idxmax()

    def ReadHeader(self):
        """
        Read header based on iheader_rowoffset_from_flag.
        JDL 3/4/24; modified 9/26/24
        """
        # Calculate the header row index
        iheader_offset = self.tbl.dParseParams['iheader_rowoffset_from_flag']
        self.idx_header_row =  self.idx_start_current + iheader_offset

        # Set the column names (drop columns with blank header)
        self.cols_df_block = self.df_raw.iloc[self.idx_header_row].values

    def SubsetDataRows(self):
        """
        Subset rows based on flags and idata_rowoffset_from_flag.
        JDL 3/4/24; Modified 9/26/24
        """
        # Calculate the start index for the data
        self.idx_start_data = self.idx_start_current + \
            self.tbl.dParseParams['idata_rowoffset_from_flag']

        # Create df with block's data rows
        self.df_block = self.df_raw.iloc[self.idx_start_data:self.idx_end_bound]

    def SubsetCols(self):
        """
        Use tbl.import_col_map to subset columns based on header.
        JDL 9/25/24
        """
        self.df_block.columns = self.cols_df_block

        #Use import_col_map if specified
        if len(self.tbl.import_col_map) > 0:
            cols_keep = list(self.tbl.import_col_map.keys())
            self.df_block = self.df_block[cols_keep]
        
        #Drop columns with blank (e.g. NaN) header
        else:
            self.df_block = self.df_block.dropna(axis=1, how='all')

    def RenameCols(self):
        """
        Optionally use tbl.import_col_map to rename columns.
        JDL 3/4/24; Modified 9/24/24
        """
        if len(self.tbl.import_col_map) > 0:
            self.df_block.rename(columns=self.tbl.import_col_map, inplace=True)

"""
================================================================================
RowMajorBlockID Class - sub to RowMajorTbl for extracting block_id values
================================================================================
"""
class RowMajorBlockID:
    def __init__(self, tbl, idx_start_data):
        self.tbl = tbl
        self.idx_start_data = idx_start_data

        #Within loop value for a block ID
        self.block_id_value = None

        #List of all block_id names
        self.df_cols_initial = self.tbl.df.columns.tolist()
        self.block_id_names = []

    @property
    def ExtractBlockIDs(self):
        """
        Property returns updated DataFrame and list of names.
        JDL 9/27/24
        """
        self.ExtractBlockIDsProcedure()
        return self.tbl.df, self.block_id_names
    """
    ============================================================================
    """
    def ExtractBlockIDsProcedure(self):
        """
        Procedure to extract block ID values from df_raw based on current block's
        data row index and dict list of block_id tuples: (block_id_name, row_offset,
        col_index) where row_offset is offset from idx_start_data and col_index is 
        absolute column index where each block_id value is found.
        JDL 9/27/24
        """
        #Convert to list if specified as one-item tuple
        self.ConvertTupleToList()

        #Iterate through block_id tuples and add columns to tbl.df
        for tup_block_id in self.tbl.dParseParams.get('block_id_vars', []):
            self.SetBlockIDValue(tup_block_id)
            self.ReorderColumns()

    def ConvertTupleToList(self):
        """
        If only one block_id, it can be specified as tuple; otherwise it's
        a list of tuples.
        JDL 9/27/24
        """
        if 'block_id_vars' in self.tbl.dParseParams:

            #If necessary, convert tuple to one-item list
            if isinstance(self.tbl.dParseParams['block_id_vars'], tuple):
                self.tbl.dParseParams['block_id_vars'] = \
                    [self.tbl.dParseParams['block_id_vars']]
            
    def SetBlockIDValue(self, tup_block_id):
        """
        Set internal values based current block_id tuple
        JDL 9/27/24
        """
        name, row_offset = tup_block_id[0], tup_block_id[1]
        idx_row, idx_col = self.idx_start_data + row_offset, tup_block_id[2]

        #Set the current value and add the name list
        value_block_id = self.tbl.df_raw.iloc[idx_row, idx_col]
        self.block_id_names.append(name)
        self.tbl.df[name] = value_block_id

    def ReorderColumns(self):
        """
        Reorder so that block_id columns are first
        9/27/24
        """
        self.tbl.df = self.tbl.df[self.block_id_names + self.df_cols_initial]

