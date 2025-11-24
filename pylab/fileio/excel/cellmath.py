"""
Utilities for converting between Excel cell addresses and row/column indices.
"""

def validate_address(row, col):
    """
    Validate that row and column are positive integers.
    
    Args:
        row: Row number to validate
        col: Column number to validate
    
    Raises:
        ValueError: If row or col are not positive integers
    """
    if not isinstance(row, int) or row < 1:
        raise ValueError("Row must be a positive integer (1-indexed)")
    if not isinstance(col, int) or col < 1:
        raise ValueError("Column must be a positive integer (1-indexed)")

def to_address(row, col, row2=None, col2=None):
    """Convert row/column indices to Excel address string."""
    def col_to_letter(col_num):
        """Convert column number to Excel letter(s)."""
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(col_num % 26 + ord('A')) + result
            col_num //= 26
        return result
    
    start_cell = f"{col_to_letter(col)}{row}"
    
    if row2 is not None and col2 is not None:
        end_cell = f"{col_to_letter(col2)}{row2}"
        return f"{start_cell}:{end_cell}"
    
    return start_cell


def from_address(address):
    """Convert Excel address string to row/column indices."""
    def letter_to_col(letters):
        """Convert Excel letter(s) to column number."""
        col = 0
        for char in letters.upper():
            col = col * 26 + (ord(char) - ord('A') + 1)
        return col
    
    def parse_cell(cell):
        """Parse single cell reference into row, col."""
        letters = ""
        numbers = ""
        for char in cell:
            if char.isalpha():
                letters += char
            elif char.isdigit():
                numbers += char
        
        col = letter_to_col(letters)
        row = int(numbers)
        return row, col
    
    # Check if it's a range
    if ':' in address:
        start, end = address.split(':')
        row1, col1 = parse_cell(start)
        row2, col2 = parse_cell(end)
        return row1, col1, row2, col2
    else:
        return parse_cell(address)


def increment_column(address, offset=1):
    """Increment the column in an Excel address."""
    if ':' in address:
        row1, col1, row2, col2 = from_address(address)
        return to_address(row1, col1 + offset, row2, col2 + offset)
    else:
        row, col = from_address(address)
        return to_address(row, col + offset)


def increment_row(address, offset=1):
    """Increment the row in an Excel address."""
    if ':' in address:
        row1, col1, row2, col2 = from_address(address)
        return to_address(row1 + offset, col1, row2 + offset, col2)
    else:
        row, col = from_address(address)
        return to_address(row + offset, col)