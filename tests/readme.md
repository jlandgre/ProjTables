This project contains Python libraries for user messaging and for performing prechecks on inputs for Python projects. It also includes a module for use of a ProjectTables class and individual Table objects to manage multiple data sources for a project including each Table's DataFrame and various metadata such as how to index the df and how to precheck its structure and contents.

This project is about making it easy to manage multiple input and output tables and to include prechecks to prevent problems that would be mysterious to the user and difficult to troubleshoot. The code base also makes it relatively easy to add in-flight error trapping. Demo.ipynb gives examples of different approaches to incorporating these modules into a project's code.

A design goal is to have user messages  be a configuration (e.g. in ErrorCodes.xlsx) instead of needing to be hard coded. A related objective is to minimize extra code and clutter related to trapping and reporting errors in functions. Another objective is to make it possible to trap errors in nested functions where it may be desirable to return up the chain from where the error was detected --allowing an orderly shutdown of in-progress proceedings before reporting the error to the user and halting execution.

__error_handling.py__
error_handling.py and its ErrorHandle class manage reporting errors and warnings indexed by a local, integer code and a base error code for each function in a code project. A table of codes and corresponding message strings is stored in the ErrorCodes.xlsx file making it easy to add new messages or edit the existing ones. ErrorHandle is loosely based on this [VBA_ErrorHandling project](https://github.com/jlandgre/VBA_ErrorHandling) that has been used successfully in VBA consulting projects.

__preflight.py__
preflight.py uses the ErrorHandle class to precheck inputs for a project. The CheckExcelFiles class can check whether a user-specified list of files exists and contains a specified list of named sheets for each file.

__projfiles.py__
projfiles.py contains classes for managing multiple DataFrames and their metadata within a project in a concise and efficient way. The ProjectTables class can be instanced as tbls, which is a collection of all data sources and outputs. It instances a Table object for each input and output table. So, for example, the DataFrame for source, tbl1, can be referred to as tbls.tbl1.df, and its default index is tbls.tbl1.ColNameIdx. For preflight checks, other attributes list required columns, columns that contain numeric data etc.

The function below from preflight.py gives an example of trapping an error if a specified file at fpath doesn't exist. Here, self.errs is an instance of the ErrorHandle class --passed to the function as an attribute of the preflight.CheckExcelFiles class. This code relies on ErrorHandle.Locn having already been set in a calling function to specify how to look up the appropriate message from ErrorCodes. 
```
    def ExcelFileExists(self, idx):
        """
        Check if an Excel file exists based on specified list index for list of files to check
        (iteration over list in calling CheckFilesProcedure)
        JDL 1/4/24
        """
        fpath = self.lst_files[idx]
        if not self.errs.is_fail(not os.path.exists(fpath), 1, self.errs.Locn, '\n ' + fpath + '\n'): return True
        self.IsWbErr = True
        self.errs.RecordErr()
        return False
```
The ErrorHandle.is_fail() function checks the specified, Boolean argument and sets a local code, 1, and an optional string parameter to report with the message listed in ErrorCodes.xlsx. The .RecordErr() method looks up a base error code for errs.Locn and adds the local, 1, code to the base to look up the message to report. This lookup approach means that the local error codes within the code can be simple integers --counting up from 1 rather than needing to be globally unique within the project. That makes administration easier.

The errs.Locn argument is a pre-specified location that is the lookup key for the message. If this were not pre-specified, errs.Locn can be replaced with "inspect.currentframe().f_code.co_name" to get the current function name.

Using .is_fail() minimizes code clutter to check for an error. In the example, there is a multiline "if block," but, if the error condition will be reported later at the top of a stack of nested functions, the check can be single line and simply return if an error is detected. In this case, the .is_fail() call can conditionally return to the calling function.

For the above example, if the .is_fail() Boolean check (first argument) returns True, the errs.RecordErr()  will report the following message and either halt execution or continue depending on the value of an errs.IswWarning Boolean flag.
```
ERROR: Specified file not found: 
path_tofile\filename.ext
```

J.D. Landgrebe, Data Delve LLC
January 2024; Updated February 19, 2024