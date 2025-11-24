from pylab.fileio.excel import Workbook
from pylab.fileio.excel.application import Application

wb = Workbook("new.xlsx")
wb.open()
print(f"Workbook is_open={wb.is_open}, with sheets={wb.list_sheets()}")
print(f"Selected sheet is {wb.sheet}")
wb.write("A1","YO")
print(f"wrote, now read... {wb.read("A1")}")