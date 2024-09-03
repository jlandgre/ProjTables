import os, sys
import pandas as pd
import logging
logging.basicConfig(level=logging.ERROR, filename='demo.log', format='%(message)s')

path_libs = os.getcwd() + os.sep + 'libs' + os.sep
if not path_libs in sys.path: sys.path.append(path_libs)
import pd_util

#Add the libs subdirectory to sys.path and import the libraries
#from projfiles import Files
#from error_handling import ErrorHandle
#from preflight import CheckDataFrame

class ProjectTables():
    """
    Collection of imported or generated data tables for a project
    """
    def __init__(self, files, lst_files):

        #Create an example table
        self.spf_input1 = files.path_data + lst_files[0]
        self.spf_input2 = files.path_data + lst_files[1]
        self.tbl1 = Table(self.spf_input1, 'Table1', 'first_sheet', 'idx')
        self.tbl2 = Table(self.spf_input2, 'Table2', 'first_sheet', 'idx')

        #Set lists of inputs and outputs
        self.lstImports = [self.tbl1, self.tbl2]
        self.lstOutputs = []

        #Initialize Output DataFrames to have the right type
        for tbl in self.lstOutputs:
            tbl.df = pd.DataFrame()

        #Set hard-coded lists of df characteristics
        self.SetColLists()

    def SetColLists(self):
        """
        Set the required columns for each table
        """
        self.tbl1.required_cols = ['idx', 'col_1', 'col_2']
        self.tbl1.numeric_cols = ['idx', 'col_1']
        self.tbl1.populated_cols = ['idx', 'col_2']
        self.tbl1.nonblank_cols = ['idx', 'col_1']
    
    def SetCustomRangeChecks(self):
        """
        Example check values within numeric range for list of tbl1 columns -- This demonstrates
        how to initialize a range check for multiple table column values by presetting arguments  
        for preflight.CheckTblDataFrame.LstColsAllInNumericRange method
        JDL 2/19/24
        """
        #Set attribute with tuple syntax (col_list, (ll, ul))
        self.tbl1.check_0to50_numeric_range = (['idx','col_1'], (0, 50))

    def SetCustomSelectionFilters(self):
        """
        Example set a custom selection filter for tbl1 - This demonstrates how to hard-code a
        filter for a table to use in selecting values in other tables etc.
        JDL 2/19/24
        """
        #Example returns a filter True for two rows
        self.tbl1.fil_selection = (self.tbl1.df['col_1'] > 10) & (self.tbl1.df['col_1'] < 40)

    def ImportInputs(self):
        """
        Read each table's raw data - use pd_util.ImportExcel() to avoid importing blank columns
        in sheet's Excel Used Range
        """
        for tbl in self.lstImports:
            tbl.df = pd_util.dfExcelImport(tbl.sPF, sht=tbl.sht, IsDeleteBlankCols=True)

            #Optionally, drop columns after lastcol
            if not tbl.name_lastcol is None:
                try:
                    idx = tbl.df.columns.get_loc(tbl.name_lastcol)
                    tbl.df = tbl.df.iloc[:, :idx+1]
                except KeyError:
                    raise ValueError(f"Column {tbl.name_lastcol} not found in", tbl.name)

class Table():
    """
    Attributes for a data table including import instructions. Table instances
    are attributes of ProjectTables Class to allow iteration over tables
    JDL Modified 8/27/24 add _cols list attribute initialization
    """
    def __init__(self, sPF, name, sht, ColNameIdx, name_lastcol=None):
                
        #Import info: Path+File (sPF), Excel sheet name for import
        self.sPF = sPF
        self.sht = sht

        #Optional name of last column --to drop extraneous columns if needed
        self.name_lastcol = name_lastcol

        #Table name (string) and name of default index column
        self.name = name #Table name
        self.ColNameIdx = ColNameIdx

        #DataFrame and transposed DataFrame
        self.df = None

        self.required_cols = []
        self.numeric_cols = []
        self.populated_cols = []
        self.nonblank_cols = []

    def ResetDefaultIndex(self, IsDrop=True):
        """
        Set or Reset df index to the default defined for the table
        JDL 2/20/24
        """
        if self.ColNameIdx is None: return self.df
        if self.df.index.name is None:
            self.df = self.df.set_index(self.ColNameIdx)
        else:
            self.df = self.df.reset_index(self.ColNameIdx, drop=IsDrop)

class CheckInputs:
    """
    Check the tbls dataframes for errors
    """
    def __init__(self, tbls, IsPrint=True):
        self.tbls = tbls
        self.IsPrint = IsPrint

        #preflight.CheckDataFrame Class --instanced as needed in methods below
        self.ckdf = None    
