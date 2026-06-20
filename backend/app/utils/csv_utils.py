import pandas as pd
from io import StringIO

VALID_COLUMNS = ['review', 'text', 'comment', 'feedback', 'message', 'content']

def parse_csv(file_content: str):
    df = pd.read_csv(StringIO(file_content))
    
    # Find the first matching valid column (case-insensitive)
    text_col = None
    for col in df.columns:
        if col.lower() in VALID_COLUMNS:
            text_col = col
            break
            
    if not text_col:
        raise ValueError(f"No valid text column found. Expected one of: {VALID_COLUMNS}")
        
    return df[text_col].fillna('').astype(str).tolist()
