# xget_option_prices.py

Download option chains (calls + puts) from Yahoo Finance via `yfinance` and write CSVs. Supports single or multiple symbols, single expiry or all expirations, optional expiration range, and optional implied-volatility plotting.

## Requirements

- Python 3
- `pandas`
- `yfinance`
- `matplotlib` (only for `--plot-iv`)

## Usage

```
python xget_option_prices.py SYMBOL [YYYYMMDD] [outfile.csv] [--plot-iv] [--timing] [--exp-range N:M]
python xget_option_prices.py SYMBOL1 SYMBOL2 ... [YYYYMMDD] [--plot-iv] [--timing] [--exp-range N:M]
```

### Arguments

- `SYMBOL`: one or more tickers. If the symbol starts with `^`, it will be stripped in output filenames and summary labels.
- `YYYYMMDD` (optional): specific expiration date to fetch. If omitted, all expirations are fetched.
- `outfile.csv` (optional): output filename for a single symbol. Ignored for multi-symbol runs.

### Options

- `--exp-range N:M`: filter expirations by days from today (inclusive). Empty side means open-ended (e.g., `:30` or `7:`). If both `YYYYMMDD` and `--exp-range` are provided, the expirations are the union.
- `--plot-iv`: plot implied volatility vs. strike for the fetched chain.
- `--timing`: print timing summary at the end.

## Output

- Writes a CSV per symbol (or to your custom `outfile.csv`).
- The default output filename is:
  - `SYMBOL_YYYY-MM-DD.csv` when a single expiry is requested, or
  - `SYMBOL_all.csv` when all expiries are fetched.

- A per-expiration summary is printed to stdout when volume/open interest fields are present.

## Examples

Fetch all expirations for one symbol:
```
python xget_option_prices.py SPX
```

Fetch one expiration and write to a custom file:
```
python xget_option_prices.py SPX 20260220 spx_20260220.csv
```

Fetch multiple symbols (all expirations):
```
python xget_option_prices.py SPY QQQ IWM
```

Fetch expirations 0–30 days out and plot IV:
```
python xget_option_prices.py SPX --exp-range 0:30 --plot-iv
```

## Notes

- Data source is Yahoo Finance via `yfinance`.
- If `--plot-iv` is used, the script pulls a spot price to focus the plot around the current level.
- The output CSV includes both calls and puts with an `option_type` column.

