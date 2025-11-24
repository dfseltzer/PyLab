import os

import logging
logger = logging.getLogger(__name__)

from .application import Application
from .cellmath import from_address, to_address, increment_column, increment_row, validate_address

class Workbook:
    def __init__(self, filepath, increment_col=0, increment_row=0):
        self.filepath = filepath
        self.workbook = None
        self.increment_col = increment_col
        self.increment_row = increment_row

        self._is_open = False
        self._read_only = False
        self._selected_sheet = None


    def open(self, read_only=False):
        if self._is_open:
            logger.warning(f"Attempted to open workbook '{self.filepath}' which is already open. If you intended to reopen, please close it first. Returning existing workbook instance.")
            return self.workbook
        
        self._read_only = read_only
        
        if os.path.exists(self.filepath):
            self.workbook = Application.open_workbook(self.filepath, read_only)
        else:
            if read_only:
                raise FileNotFoundError(f"Cannot open non-existent file in read-only mode: {self.filepath}")
            self.workbook = Application.create_workbook(self.filepath)
        
        self._is_open = True
        
        # Select first sheet by default
        self._selected_sheet = self.workbook.Worksheets(1)
        
        return self.workbook
    
    def save(self):
        """Save the workbook."""
        if not self._is_open or not self.workbook:
            raise RuntimeError("Workbook is not open")
        if self._read_only:
            raise PermissionError("Cannot save workbook opened in read-only mode")
        self.workbook.Save()
    
    def save_as(self, new_filepath):
        if not self._is_open or not self.workbook:
            raise RuntimeError("Workbook is not open")
        if self._read_only:
            raise PermissionError("Cannot save workbook opened in read-only mode")
        self.workbook.SaveAs(os.path.abspath(new_filepath))
        self.filepath = new_filepath
    
    def list_sheets(self):
        """
        List all sheet names in the workbook.
        
        Returns:
            list: List of sheet names
        """
        if not self._is_open or not self.workbook:
            raise RuntimeError("Workbook is not open")
        return [sheet.Name for sheet in self.workbook.Worksheets]
    
    def add_sheet(self, name=None, before=None, after=None):
        """
        Add a new sheet to the workbook.
        
        Args:
            name: Optional name for the new sheet
            before: Optional sheet name or index to insert before
            after: Optional sheet name or index to insert after
        
        Returns:
            str: Name of the created sheet
        """
        if not self._is_open or not self.workbook:
            raise RuntimeError("Workbook is not open")
        if self._read_only:
            raise PermissionError("Cannot add sheet to workbook opened in read-only mode")
        
        # Determine position
        if before is not None:
            if isinstance(before, str):
                before_sheet = self.workbook.Worksheets(before)
            else:
                before_sheet = self.workbook.Worksheets(before)
            new_sheet = self.workbook.Worksheets.Add(Before=before_sheet)
        elif after is not None:
            if isinstance(after, str):
                after_sheet = self.workbook.Worksheets(after)
            else:
                after_sheet = self.workbook.Worksheets(after)
            new_sheet = self.workbook.Worksheets.Add(After=after_sheet)
        else:
            # Add at the end
            new_sheet = self.workbook.Worksheets.Add(After=self.workbook.Worksheets(self.workbook.Worksheets.Count))
        
        # Set name if provided
        if name is not None:
            if name in self.list_sheets():
                raise ValueError(f"Sheet with name '{name}' already exists")
            new_sheet.Name = name
        
        return new_sheet.Name
    
    def delete_sheet(self, sheet):
        """
        Delete a sheet from the workbook.
        
        Args:
            sheet: Sheet name (str) or index (int, 1-indexed)
        """
        if not self._is_open or not self.workbook:
            raise RuntimeError("Workbook is not open")
        if self._read_only:
            raise PermissionError("Cannot delete sheet from workbook opened in read-only mode")
        
        if self.workbook.Worksheets.Count == 1:
            raise ValueError("Cannot delete the last sheet in the workbook")
        
        if isinstance(sheet, str):
            sheet_obj = self.workbook.Worksheets(sheet)
        elif isinstance(sheet, int):
            sheet_obj = self.workbook.Worksheets(sheet)
        else:
            raise TypeError("Sheet must be a string (name) or integer (index)")
        
        # Clear selected sheet if we're deleting it
        if self._selected_sheet is not None and self._selected_sheet.Name == sheet_obj.Name:
            self._selected_sheet = None
        
        sheet_obj.Delete()
    
    def rename_sheet(self, old_name, new_name):
        """
        Rename a sheet in the workbook.
        
        Args:
            old_name: Current sheet name (str) or index (int, 1-indexed)
            new_name: New name for the sheet
        """
        if not self._is_open or not self.workbook:
            raise RuntimeError("Workbook is not open")
        if self._read_only:
            raise PermissionError("Cannot rename sheet in workbook opened in read-only mode")
        
        if new_name in self.list_sheets():
            raise ValueError(f"Sheet with name '{new_name}' already exists")
        
        if isinstance(old_name, str):
            sheet_obj = self.workbook.Worksheets(old_name)
        elif isinstance(old_name, int):
            sheet_obj = self.workbook.Worksheets(old_name)
        else:
            raise TypeError("Old name must be a string (name) or integer (index)")
        
        sheet_obj.Name = new_name
    
    def activate_sheet(self, sheet):
        """
        Activate (make visible) a sheet in the Excel window.
        
        Args:
            sheet: Sheet name (str) or index (int, 1-indexed)
        
        Returns:
            bool: True if successful, False if workbook is not visible
        """
        if not self._is_open or not self.workbook:
            raise RuntimeError("Workbook is not open")
        
        # Check if Excel is visible
        excel_app = Application._app
        if not excel_app.Visible:
            logger.error("Cannot activate sheet: Excel application is not visible")
            return False
        
        # Get the sheet
        if isinstance(sheet, str):
            sheet_obj = self.workbook.Worksheets(sheet)
        elif isinstance(sheet, int):
            sheet_obj = self.workbook.Worksheets(sheet)
        else:
            raise TypeError("Sheet must be a string (name) or integer (index)")
        
        # Activate the sheet
        sheet_obj.Activate()
        return True
    
    @property
    def sheet(self):
        """Get the name of the currently selected sheet."""
        if self._selected_sheet is None:
            return None
        return self._selected_sheet.Name
    
    @sheet.setter
    def sheet(self, sheet):
        """
        Select a sheet to work with.
        
        Args:
            sheet: Sheet name (str) or index (int, 1-indexed)
        """
        if not self._is_open or not self.workbook:
            raise RuntimeError("Workbook is not open")
        
        if isinstance(sheet, str):
            self._selected_sheet = self.workbook.Worksheets(sheet)
        elif isinstance(sheet, int):
            self._selected_sheet = self.workbook.Worksheets(sheet)
        else:
            raise TypeError("Sheet must be a string (name) or integer (index)")
    
    def read(self, row, col=None):
        """
        Read a value from a cell.
        
        Args:
            row: Row number (1-indexed) or Excel address string (e.g., "A1")
            col: Column number (1-indexed), not needed if row is an address string
        
        Returns:
            Cell value
        """
        if not self._is_open or not self.workbook:
            raise RuntimeError("Workbook is not open")
        if self._selected_sheet is None:
            raise RuntimeError("No sheet selected")
        
        # If row is a string address, parse it
        if isinstance(row, str):
            parsed = from_address(row)
            if len(parsed) == 2:
                row, col = parsed
            else:
                raise ValueError("Cannot read from range address, use read_range() for ranges")
        else:
            validate_address(row, col)
        
        return self._selected_sheet.Cells(row, col).Value
    
    def read_range(self, start_row, start_col, end_row=None, end_col=None):
        """
        Read a range of cells.
        
        Args:
            start_row: Starting row (1-indexed) or Excel range address (e.g., "A1:C3")
            start_col: Starting column (1-indexed) or None if using address
            end_row: Ending row (1-indexed) or None if using address
            end_col: Ending column (1-indexed) or None if using address
        
        Returns:
            tuple: (values, next_address) where values is a 2D list and next_address is the incremented address
        """
        if not self._is_open or not self.workbook:
            raise RuntimeError("Workbook is not open")
        if self._selected_sheet is None:
            raise RuntimeError("No sheet selected")
        
        # If start_row is a string address, parse it
        if isinstance(start_row, str):
            parsed = from_address(start_row)
            if len(parsed) == 4:
                start_row, start_col, end_row, end_col = parsed
            else:
                raise ValueError("Range address must be in format 'A1:C3'")
        else:
            validate_address(start_row, start_col)
            if end_row is not None:
                validate_address(end_row, end_col)
        
        # Get the range
        range_obj = self._selected_sheet.Range(
            self._selected_sheet.Cells(start_row, start_col),
            self._selected_sheet.Cells(end_row, end_col)
        )
        
        # Read values - Excel returns tuple of tuples for multi-row, single tuple for single row
        values = range_obj.Value
        
        # Normalize to 2D list
        if values is None:
            result_values = [[None]]
        elif isinstance(values, tuple):
            if len(values) > 0 and isinstance(values[0], tuple):
                result_values = [list(row) for row in values]
            else:
                # Single row
                result_values = [list(values)]
        else:
            # Single cell
            result_values = [[values]]
        
        # Calculate incremented address
        result_address = to_address(start_row, start_col, end_row, end_col)
        if self.increment_col != 0:
            result_address = increment_column(result_address, self.increment_col)
        if self.increment_row != 0:
            result_address = increment_row(result_address, self.increment_row)
        
        return result_values, result_address
    
    def write(self, row, col, value=None, format=None):
        """
        Write a value to a cell.
        
        Args:
            row: Row number (1-indexed) or Excel address string (e.g., "A1")
            col: Column number (1-indexed) or value if row is an address string
            value: Value to write (not needed if using address string)
            format: Optional format string (e.g., "0.00", "#,##0", "mm/dd/yyyy")
        
        Returns:
            str: The incremented Excel address after applying increment_row and increment_col
        """
        if not self._is_open or not self.workbook:
            raise RuntimeError("Workbook is not open")
        if self._selected_sheet is None:
            raise RuntimeError("No sheet selected")
        if self._read_only:
            raise PermissionError("Cannot write to workbook opened in read-only mode")
        
        # If row is a string address, parse it
        if isinstance(row, str):
            parsed = from_address(row)
            if len(parsed) == 2:
                row_num, col_num = parsed
                # col parameter contains the value when using address string
                cell = self._selected_sheet.Cells(row_num, col_num)
                cell.Value = col
                if format is not None:
                    cell.NumberFormat = format
                # Return incremented address
                result_address = to_address(row_num, col_num)
            else:
                raise ValueError("Cannot write to range address, use write_range() for ranges")
        else:
            validate_address(row, col)
            
            cell = self._selected_sheet.Cells(row, col)
            cell.Value = value
            if format is not None:
                cell.NumberFormat = format
            # Return incremented address
            result_address = to_address(row, col)
        
        # Apply increments
        if self.increment_col != 0:
            result_address = increment_column(result_address, self.increment_col)
        if self.increment_row != 0:
            result_address = increment_row(result_address, self.increment_row)
        
        return result_address
    
    def write_range(self, start_row, start_col, values, end_row=None, end_col=None, format=None):
        """
        Write a range of cells.
        
        Args:
            start_row: Starting row (1-indexed) or Excel range address (e.g., "A1:C3")
            start_col: Starting column (1-indexed) or 2D list of values if using address
            values: 2D list of values to write (not needed if using address)
            end_row: Ending row (1-indexed) or None if using address
            end_col: Ending column (1-indexed) or None if using address
            format: Optional format string to apply to all cells in range
        
        Returns:
            str: The range address that was written to
        """
        if not self._is_open or not self.workbook:
            raise RuntimeError("Workbook is not open")
        if self._selected_sheet is None:
            raise RuntimeError("No sheet selected")
        if self._read_only:
            raise PermissionError("Cannot write to workbook opened in read-only mode")
        
        # If start_row is a string address, parse it
        if isinstance(start_row, str):
            parsed = from_address(start_row)
            if len(parsed) == 4:
                start_row_num, start_col_num, end_row_num, end_col_num = parsed
                # start_col contains the values when using address string
                values = start_col
            else:
                raise ValueError("Range address must be in format 'A1:C3'")
        else:
            validate_address(start_row, start_col)
            
            start_row_num = start_row
            start_col_num = start_col
            # Calculate end position from values if not provided
            if end_row is None or end_col is None:
                if not isinstance(values, list) or len(values) == 0:
                    raise ValueError("Values must be a non-empty 2D list")
                num_rows = len(values)
                num_cols = len(values[0]) if isinstance(values[0], list) else 1
                end_row_num = start_row_num + num_rows - 1
                end_col_num = start_col_num + num_cols - 1
            else:
                validate_address(end_row, end_col)
                end_row_num = end_row
                end_col_num = end_col
        
        # Validate values is a 2D list
        if not isinstance(values, list):
            raise ValueError("Values must be a 2D list")
        
        # Convert 1D list to 2D if needed
        if len(values) > 0 and not isinstance(values[0], list):
            values = [values]
        
        # Get the range
        range_obj = self._selected_sheet.Range(
            self._selected_sheet.Cells(start_row_num, start_col_num),
            self._selected_sheet.Cells(end_row_num, end_col_num)
        )
        
        # Convert to tuple of tuples for Excel
        values_tuple = tuple(tuple(row) if isinstance(row, list) else (row,) for row in values)
        
        # Write values
        range_obj.Value = values_tuple
        
        # Apply format if provided
        if format is not None:
            range_obj.NumberFormat = format
        
        # Return the range address
        return to_address(start_row_num, start_col_num, end_row_num, end_col_num)
    
    def close(self, save_changes=True):
        if not self._is_open:
            return
        
        if self.workbook:
            Application.close_workbook(self.workbook, save_changes)
            self.workbook = None
        
        self._is_open = False
    
    @property
    def is_open(self):
        """Check if workbook is currently open."""
        return self._is_open
    
    @property
    def read_only(self):
        """Check if workbook was opened in read-only mode."""
        return self._read_only
    
    # Context manager methods
    def __enter__(self):
        return self.open()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Save unless there was an exception
        save = exc_type is None
        self.close(save_changes=save)