"""
Examples of creating and opening Excel files using pywin32 with a single application instance.
"""

import win32com.client
import os
import atexit

import logging
logger = logging.getLogger(__name__)

class _app_singleton:
    """
    Singleton-like class to manage a single Excel application instance.
    Reuses the same Excel instance for all workbook operations.
    """
    
    _instance = None
    _excel = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._excel is None:
            self._excel = win32com.client.Dispatch("Excel.Application")
            self._excel.DisplayAlerts = False  # Suppress prompts
            atexit.register(self.quit)
    
    @property
    def app(self):
        """Get the Excel application instance."""
        return self._excel
    
    @property
    def visible(self):
        """Get visibility state."""
        return self._excel.Visible
    
    @visible.setter
    def visible(self, value):
        """Set visibility of Excel application."""
        self._excel.Visible = value
    
    def create_workbook(self, filepath=None):
        workbook = self._excel.Workbooks.Add()
        
        if filepath:
            workbook.SaveAs(os.path.abspath(filepath))
            logger.info(f"Created new Excel file: {filepath}")
        
        return workbook
    
    def open_workbook(self, filepath, read_only=False):
        """
        Open an existing workbook.
        """
        abs_path = os.path.abspath(filepath)
        workbook = self._excel.Workbooks.Open(abs_path, ReadOnly=read_only)
        logger.info(f"Opened Excel file: {filepath}")
        return workbook
    
    def close_workbook(self, workbook, save_changes=True):
        """
        Close a specific workbook.
        """
        try:
            workbook.Close(SaveChanges=save_changes)
        except Exception as e:
            logger.error(f"Error closing workbook: {e}")
    
    def quit(self):
        """Quit the Excel application and clean up."""
        if self._excel:
            try:
                self._excel.Quit()
                self._excel = None
                logger.info("Excel application closed")
            except Exception as e:
                logger.error(f"Error quitting Excel: {e}")
    
    def workbook_count(self):
        """Get number of currently open workbooks."""
        return self._excel.Workbooks.Count

Application = _app_singleton()
