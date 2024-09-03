import os, sys
import pandas as pd
from openpyxl import load_workbook
import logging
logging.basicConfig(level=logging.ERROR, filename='demo.log', format='%(message)s')

path_libs = os.getcwd() + os.sep + 'libs' + os.sep
if not path_libs in sys.path: sys.path.append(path_libs)
import pd_util
from projtables import Table

"""
================================================================================
ProjectTables Class
================================================================================
"""

class ProjectTables():
    """
    Collection of imported or generated data tables for a project
    Customized for importing raw data
    """
    def __init__(self, files, lst_files):

        #Create an example table
        self.spf_input1 = files.path_data + lst_files[0]
        self.tbl1 = Table(self.spf_input1, 'Table1', 'raw_table', 'idx')

        #Set lists of inputs and outputs
        self.lstImports = []
        self.lstRawImports = [self.tbl1]
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
        self.tbl1.import_col_map = {'idx_raw':'idx', 'col #1':'col_1', 'col #2':'col_2'}
        self.tbl1.required_cols = ['idx', 'col_1', 'col_2']
        self.tbl1.numeric_cols = ['idx', 'col_1']
        self.tbl1.populated_cols = ['idx', 'col_2']
        self.tbl1.nonblank_cols = ['idx', 'col_1']
    
    def ImportInputs(self):
        """
        Read each table's raw data - use pd_util.ImportExcel() to avoid importing blank columns
        in sheet's Excel Used Range
        """
        print('\nin import', self.lstImports)
        for tbl in self.lstImports:
            tbl.df = pd_util.dfExcelImport(tbl.sPF, sht=tbl.sht, IsDeleteBlankCols=True)

            print('\nImported', tbl.name, tbl.sPF, tbl.sht)
            print(tbl.df)
            #Optionally, drop columns after lastcol
            if not tbl.name_lastcol is None:
                try:
                    idx = tbl.df.columns.get_loc(tbl.name_lastcol)
                    tbl.df = tbl.df.iloc[:, :idx+1]
                except KeyError:
                    raise ValueError(f"Column {tbl.name_lastcol} not found in", tbl.name)
    
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