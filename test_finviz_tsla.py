from importlib.metadata import version

import pandas as pd
from finvizfinance.quote import finvizfinance


def main() -> None:
    ticker = "TSLA"
    print(f"finvizfinance version: {version('finvizfinance')}")

    fundamentals = finvizfinance(ticker).ticker_fundament()
    if not fundamentals:
        raise RuntimeError(f"No fundamentals returned for {ticker}")

    fundamentals["Ticker"] = ticker
    print(pd.Series(fundamentals).to_string())


if __name__ == "__main__":
    main()
