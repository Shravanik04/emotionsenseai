import pandas as pd
from io import StringIO, BytesIO

VALID_COLUMNS = ['review', 'text', 'comment', 'feedback', 'message', 'content']


def _find_text_column(df: pd.DataFrame) -> str:
    """Find the first matching valid text column (case-insensitive)."""
    for col in df.columns:
        if col.lower() in VALID_COLUMNS:
            return col
    raise ValueError(f"No valid text column found. Expected one of: {VALID_COLUMNS}")


def parse_csv(file_content: str):
    df = pd.read_csv(StringIO(file_content))
    text_col = _find_text_column(df)
    return df[text_col].fillna('').astype(str).tolist()


def parse_txt(file_content: str):
    """Parse a plain-text file: one text per line."""
    lines = [line.strip() for line in file_content.splitlines() if line.strip()]
    return lines


def parse_excel(file_bytes: bytes):
    """Parse an Excel (.xlsx / .xls) file."""
    df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
    text_col = _find_text_column(df)
    return df[text_col].fillna('').astype(str).tolist()
