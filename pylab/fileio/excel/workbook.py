import os

import logging
logger = logging.getLogger(__name__)

from .application import Application
from .cellmath import from_address, to_address, increment_column, increment_row

class Workbook:
    def __init__(self, filepath, increment_col=0, increment_row=0):
        self.filepath = filepath
        self.workbook = None
        self._is_open = False
        self._read_only = False
        self._selected_sheet = None
        self.increment_col = increment_col
        self.increment_row = increment_row

    def open(self, read_only=False):
        if self._is_open:
            logger.warning(f"Context manager but is already open... returning. Did you forget to close?")
            return self.workbook
        
        self._read_only = read_only
        
        if os.path.exists(self.filepath):
            self.workbook = Application.open_workbook(self.filepath, read_only)
        else:
            if read_only:
                raise FileNotFoundError(f"Cannot open non-existent file in read-only mode: {self.filepath}")
            self.workbook = Application.create_workbook(self.filepath)
        
        self._is_open = True
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
                raise ValueError("Cannot read from range address, use single cell")
        
        return self._selected_sheet.Cells(row, col).Value
    
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
                raise ValueError("Cannot write to range address, use single cell")
        else:
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