import pandas as pd
from io import StringIO, BytesIO

def decode_bytes(content: bytes) -> str:
    """Try to decode bytes with common encodings."""
    for encoding in ("utf-8", "utf-8-sig", "latin1", "cp1252", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    # Fallback to ignoring errors if all fail
    return content.decode("utf-8", errors="ignore")


def _find_text_column(df: pd.DataFrame) -> str:
    """Find the best text column in the DataFrame, with robust fallbacks."""
    if df.empty or len(df.columns) == 0:
        raise ValueError("The uploaded file contains no data or columns.")

    # 1. Normalize column names (strip whitespace and surrounding quotes/brackets, lowercase)
    normalized_cols = {}
    for col in df.columns:
        # Convert to string to avoid issues if a column header is a number
        col_str = str(col).strip().strip("'\"[]()").lower()
        normalized_cols[col_str] = col

    # 2. Look for exact matches from our expanded keyword list
    expanded_keywords = [
        'review', 'reviews', 'text', 'texts', 'txt', 'comment', 'comments', 
        'feedback', 'feedbacks', 'message', 'messages', 'content', 'contents', 
        'body', 'sentence', 'sentences', 'tweet', 'tweets', 'post', 'posts', 
        'input', 'inputs', 'data', 'value', 'values', 'line', 'lines'
    ]
    for kw in expanded_keywords:
        if kw in normalized_cols:
            return normalized_cols[kw]

    # 3. Check for substring/partial matches (e.g. 'review_text', 'tweet_content', 'usercomment')
    for kw in expanded_keywords:
        for col_str, orig_col in normalized_cols.items():
            if kw in col_str:
                return orig_col

    # 4. If there is only one column, use it! (Very common for custom/no-header CSVs)
    if len(df.columns) == 1:
        return df.columns[0]

    # 5. Look for a column of 'object' (string) type
    for col in df.columns:
        if df[col].dtype == 'object':
            # Check if it actually has some non-empty strings
            non_empty = df[col].dropna()
            if not non_empty.empty and any(isinstance(val, str) and val.strip() for val in non_empty.head(10)):
                return col

    # 6. Fallback: Default to the first column
    return df.columns[0]


def parse_csv(file_content):
    """Parse CSV content from bytes or str."""
    if isinstance(file_content, bytes):
        file_content = decode_bytes(file_content)
    df = pd.read_csv(StringIO(file_content))
    text_col = _find_text_column(df)
    return df[text_col].fillna('').astype(str).tolist()


def parse_txt(file_content):
    """Parse a plain-text file: one text per line."""
    if isinstance(file_content, bytes):
        file_content = decode_bytes(file_content)
    lines = [line.strip() for line in file_content.splitlines() if line.strip()]
    return lines


def parse_excel(file_bytes: bytes, filename: str = ""):
    """Parse an Excel (.xlsx / .xls) file."""
    # Determine the appropriate engine based on file extension
    engine = None
    if filename:
        if filename.endswith(".xls"):
            engine = "xlrd"
        elif filename.endswith(".xlsx"):
            engine = "openpyxl"
    
    # Try reading with the determined engine, or auto-detect if engine is None
    try:
        if engine:
            df = pd.read_excel(BytesIO(file_bytes), engine=engine)
        else:
            df = pd.read_excel(BytesIO(file_bytes))
    except Exception as e:
        # If specific engine fails, try fallback without specifying engine
        try:
            df = pd.read_excel(BytesIO(file_bytes))
        except Exception as inner_err:
            raise ValueError(f"Failed to read Excel file: {str(inner_err)}. "
                             f"Please ensure the file is not corrupted and is in a valid .xlsx or .xls format.")

    text_col = _find_text_column(df)
    return df[text_col].fillna('').astype(str).tolist()

