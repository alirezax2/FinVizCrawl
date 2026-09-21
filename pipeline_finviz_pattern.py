import os
import time
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

from finvizfinance.constants import filter_dict
from finvizfinance.screener.overview import Overview
from utils import upload_to_hf_dataset

# Load environment variables from .env file
load_dotenv()

# Get the name of the HuggingFace dataset for FinViz to export
dataset_name_FinViz_output = os.getenv('dataset_name_FinViz_output')

# Get the Hugging Face API token from the environment
HF_TOKEN_FINVIZ = os.getenv('HF_TOKEN_FINVIZ')

# Ensure output directory exists
if not os.path.exists('finviz'):
    os.makedirs('finviz')

# Get current date
current_datetime = datetime.now().strftime("%Y-%m-%d")

# Pattern signal mapping: +1 for Bullish, -1 for Bearish, +1 for Neutral/Horizontal/Symmetrical
PATTERN_SIGNAL_MAP = {
    # Bullish (+1)
    'TL Support': 1,
    'TL Support (Strong)': 1,
    'Wedge Down': 1,
    'Wedge Down (Strong)': 1,
    'Triangle Ascending': 1,
    'Triangle Ascending (Strong)': 1,
    'Channel Up': 1,
    'Channel Up (Strong)': 1,
    'Double Bottom': 1,
    'Multiple Bottom': 1,
    'Head & Shoulders Inverse': 1,

    # Bearish (-1)
    'TL Resistance': -1,
    'TL Resistance (Strong)': -1,
    'Wedge Up': -1,
    'Wedge Up (Strong)': -1,
    'Triangle Descending': -1,
    'Triangle Descending (Strong)': -1,
    'Channel Down': -1,
    'Channel Down (Strong)': -1,
    'Double Top': -1,
    'Multiple Top': -1,
    'Head & Shoulders': -1,

    # Neutral / Support & Resistance / Symmetrical (+1 when present)
    'Horizontal S/R': 1,
    'Horizontal S/R (Strong)': 1,
    'Wedge': 1,
    'Wedge (Strong)': 1,
    'Channel': 1,
    'Channel (Strong)': 1,
}

def get_pattern_list():
    """Retrieve list of valid Finviz patterns, skipping 'Any'."""
    pattern_options = filter_dict.get('Pattern', {}).get('option', {})
    patterns = [p for p in pattern_options.keys() if p.strip().lower() != 'any']
    return patterns

def main():
    patterns = get_pattern_list()
    print(f"Retrieved {len(patterns)} patterns to scan:")
    for idx, p in enumerate(patterns, 1):
        signal = PATTERN_SIGNAL_MAP.get(p, 1)
        direction = "Bullish (+1)" if signal == 1 else "Bearish (-1)"
        print(f"  {idx}. {p} [{direction}]")

    # Storage for ticker patterns and metadata
    ticker_metadata = {}
    pattern_matches = {p: set() for p in patterns}

    meta_cols = ['Company', 'Sector', 'Industry', 'Country', 'Market Cap', 'P/E', 'Price', 'Change %', 'Volume']

    for i, pattern in enumerate(patterns, 1):
        print(f"\n[{i}/{len(patterns)}] Querying pattern: '{pattern}' ...")
        retries = 3
        df_pattern = None
        for attempt in range(1, retries + 1):
            try:
                screener = Overview()
                screener.set_filter(filters_dict={'Pattern': pattern})
                df_pattern = screener.screener_view()
                break
            except Exception as e:
                print(f"  Attempt {attempt} failed for '{pattern}': {e}")
                if attempt < retries:
                    time.sleep(3)

        if df_pattern is not None and not df_pattern.empty and 'Ticker' in df_pattern.columns:
            matched_tickers = df_pattern['Ticker'].dropna().tolist()
            pattern_matches[pattern].update(matched_tickers)
            print(f"  Found {len(matched_tickers)} tickers for '{pattern}'")

            # Save/update ticker metadata
            for _, row in df_pattern.iterrows():
                ticker = row['Ticker']
                if ticker not in ticker_metadata:
                    meta = {}
                    for col in meta_cols:
                        if col in row:
                            meta[col] = row[col]
                    ticker_metadata[ticker] = meta
        else:
            print(f"  No tickers found for '{pattern}'")

        # Small delay between pattern queries to prevent rate-limiting
        time.sleep(2)

    all_tickers = sorted(list(ticker_metadata.keys()))
    print(f"\nTotal unique tickers with at least one detected pattern: {len(all_tickers)}")

    if not all_tickers:
        print("No tickers found across all patterns. Creating empty dataframe with columns.")
        DFtotal = pd.DataFrame(columns=['Ticker'] + meta_cols + patterns)
    else:
        rows = []
        for ticker in all_tickers:
            row_data = {'Ticker': ticker}
            # Add metadata
            meta = ticker_metadata.get(ticker, {})
            for col in meta_cols:
                row_data[col] = meta.get(col, '')

            # Add pattern values: 1 / -1 if ticker has pattern, else 0
            for pattern in patterns:
                if ticker in pattern_matches[pattern]:
                    signal_value = PATTERN_SIGNAL_MAP.get(pattern, 1)
                    row_data[pattern] = signal_value
                else:
                    row_data[pattern] = 0

            rows.append(row_data)

        DFtotal = pd.DataFrame(rows)

    # Pattern columns to compute counts
    pattern_cols = [p for p in patterns if p in DFtotal.columns]

    # Count +1 and -1 for each row
    DFtotal['Pattern_+1_Count'] = (DFtotal[pattern_cols] == 1).sum(axis=1)
    DFtotal['Pattern_-1_Count'] = (DFtotal[pattern_cols] == -1).sum(axis=1)
    DFtotal['Pattern_Total'] = (DFtotal[pattern_cols] != 0).sum(axis=1)

    # Drop first character of Ticker column
    if 'Ticker' in DFtotal.columns:
        DFtotal['Ticker'] = DFtotal['Ticker'].astype(str).str[1:]

    # Output file paths
    file_path = fr'finviz/FinViz_Pattern_{current_datetime}.csv'
    latest_file_path = fr'finviz/FinViz_Pattern.csv'

    # Save CSV files locally
    DFtotal.to_csv(file_path, index=False)
    DFtotal.to_csv(latest_file_path, index=False)
    print(f"\nSaved dated CSV: {file_path}")
    print(f"Saved latest CSV: {latest_file_path}")

    # Upload to Hugging Face Dataset if configured
    if dataset_name_FinViz_output and HF_TOKEN_FINVIZ:
        print(f"\nUploading to Hugging Face dataset: {dataset_name_FinViz_output}")
        upload_to_hf_dataset(file_path, dataset_name_FinViz_output, HF_TOKEN_FINVIZ, repo_type="dataset")
        upload_to_hf_dataset(latest_file_path, dataset_name_FinViz_output, HF_TOKEN_FINVIZ, repo_type="dataset")
    else:
        print("\nHugging Face credentials not set; skipping upload.")

if __name__ == "__main__":
    main()
