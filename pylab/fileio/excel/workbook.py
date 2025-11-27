import os

import logging
logger = logging.getLogger(__name__)

from .application import Application
from .cellmath import from_address, to_address, increment_column, increment_row, validate_address

class Workbook:
    def __init__(self, filepath, increment_col=0, increment_row=0, open_now=False, read_only=False):
        self.filepath = filepath
        self.workbook = None
        self.increment_col = increment_col
        self.increment_row = increment_row

        self._is_open = False
        self._read_only = read_only
        self._selected_sheet = None

        if open_now:
            self.open(read_only=read_only)

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
    
    def add_sheet(self, name=None, before=None, after=None, select=True):
        """
        Add a new sheet to the workbook.
        
        Args:
            name: Optional name for the new sheet
            before: Optional sheet name or index to insert before
            after: Optional sheet name or index to insert after
            select: If True, select the new sheet after creation

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
        
        if select:
            self.sheet = new_sheet.Name

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
    
    def _parse_cell_address(self, address):
        """Normalize a single-cell address into (row, col)."""
        if isinstance(address, str):
            parsed = from_address(address)
            if len(parsed) != 2:
                raise ValueError("Address must reference a single cell like 'A1'")
            return parsed
        if isinstance(address, tuple) and len(address) == 2:
            row, col = address
            validate_address(row, col)
            return row, col
        raise TypeError("Address must be a string or a (row, col) tuple")
    
    def _parse_range_address(self, range_address):
        """Normalize a range address into (start_row, start_col, end_row, end_col)."""
        if isinstance(range_address, str):
            parsed = from_address(range_address)
            if len(parsed) == 4:
                return parsed
            if len(parsed) == 2:
                row, col = parsed
                return row, col, row, col
            raise ValueError("Range address must be in format like 'A1:C3'")
        if (
            isinstance(range_address, tuple)
            and len(range_address) == 2
            and all(isinstance(item, tuple) and len(item) == 2 for item in range_address)
        ):
            (start_row, start_col), (end_row, end_col) = range_address
            validate_address(start_row, start_col)
            validate_address(end_row, end_col)
            return start_row, start_col, end_row, end_col
        raise TypeError("Range must be a string or ((r1, c1), (r2, c2)) tuple")
    
    def read(self, address):
        """
        Read a value from a cell.
        
        Args:
            address: Excel address string (e.g., "A1") or (row, col) tuple
        
        Returns:
            Cell value
        """
        if not self._is_open or not self.workbook:
            raise RuntimeError("Workbook is not open")
        if self._selected_sheet is None:
            raise RuntimeError("No sheet selected")
        
        row, col = self._parse_cell_address(address)
        return self._selected_sheet.Cells(row, col).Value
    
    def read_range(self, range_address):
        """
        Read a range of cells.
        
        Args:
            range_address: Excel range address string (e.g., "A1:C3") or ((r1, c1), (r2, c2)) tuple
        
        Returns:
            tuple: (values, next_address) where values is a 2D list and next_address is the incremented address
        """
        if not self._is_open or not self.workbook:
            raise RuntimeError("Workbook is not open")
        if self._selected_sheet is None:
            raise RuntimeError("No sheet selected")
        
        start_row, start_col, end_row, end_col = self._parse_range_address(range_address)
        
        range_obj = self._selected_sheet.Range(
            self._selected_sheet.Cells(start_row, start_col),
            self._selected_sheet.Cells(end_row, end_col)
        )
        
        values = range_obj.Value
        
        if values is None:
            result_values = [[None]]
        elif isinstance(values, tuple):
            if len(values) > 0 and isinstance(values[0], tuple):
                result_values = [list(row) for row in values]
            else:
                result_values = [list(values)]
        else:
            result_values = [[values]]
        
        result_address = to_address(start_row, start_col, end_row, end_col)
        if self.increment_col != 0:
            result_address = increment_column(result_address, self.increment_col)
        if self.increment_row != 0:
            result_address = increment_row(result_address, self.increment_row)
        
        return result_values, result_address
    
    def write(self, address, value=None, format=None):
        """
        Write a value to a cell.
        
        Args:
            address: Excel address string (e.g., "A1") or (row, col) tuple
            value: Value to write
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
        
        row_num, col_num = self._parse_cell_address(address)
        
        cell = self._selected_sheet.Cells(row_num, col_num)
        cell.Value = value
        if format is not None:
            cell.NumberFormat = format
        result_address = to_address(row_num, col_num)
        
        if self.increment_col != 0:
            result_address = increment_column(result_address, self.increment_col)
        if self.increment_row != 0:
            result_address = increment_row(result_address, self.increment_row)
        
        return result_address
    
    def write_range(self, range_address, values, format=None):
        """
        Write a range of cells.
        
        Args:
            range_address: Excel range address string (e.g., "A1:C3") or ((r1, c1), (r2, c2)) tuple
            values: 2D list of values to write
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
        
        start_row_num, start_col_num, end_row_num, end_col_num = self._parse_range_address(range_address)
        
        if not isinstance(values, list):
            raise ValueError("Values must be a 2D list")
        
        if len(values) > 0 and not isinstance(values[0], list):
            values = [values]
        
        range_obj = self._selected_sheet.Range(
            self._selected_sheet.Cells(start_row_num, start_col_num),
            self._selected_sheet.Cells(end_row_num, end_col_num)
        )
        
        values_tuple = tuple(tuple(row) if isinstance(row, list) else (row,) for row in values)
        range_obj.Value = values_tuple
        
        if format is not None:
            range_obj.NumberFormat = format
        
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
