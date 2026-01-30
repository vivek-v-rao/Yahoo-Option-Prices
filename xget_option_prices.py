#!/usr/bin/env python3
"""
download option prices (calls + puts) for one or more symbols/expirations to CSV

usage:
  python xget_option_prices.py SYMBOL [YYYYMMDD] [outfile.csv] [--plot-iv] [--timing] [--exp-range N:M]
  python xget_option_prices.py SYMBOL1 SYMBOL2 ... [YYYYMMDD] [--plot-iv] [--timing] [--exp-range N:M]

notes:
  - if YYYYMMDD is omitted, all expirations are fetched
  - --exp-range N:M uses days from today (inclusive); empty side means open-ended
  - if YYYYMMDD and --exp-range are both provided, expirations are the union
  - prints a per-expiration summary for each symbol (strikes, min/max, volume, open interest, bid/ask counts)
"""

import time
start = time.time()
import sys
from datetime import datetime
from time import perf_counter
import pandas as pd
from timing_util import print_timings
from option_summary import summarize_option_chain
from option_plots import plot_iv_vs_strike
from option_chain_fetch import (
    dash,
    expirations_in_range,
    fetch_option_chain,
    is_date_token,
    option_chain_df,
    parse_exp_range,
)
timings = pd.Series(dtype="float")
timings["imported modules"] = time.time()
pd.options.display.float_format = '{:.3f}'.format

def main(argv):
    if len(argv) < 2:
        print("usage: python xget_option_prices.py SYMBOL [YYYYMMDD] [outfile.csv] [--plot-iv] [--timing] [--exp-range N:M]")
        sys.exit(1)

    plot_iv = "--plot-iv" in argv
    exp_range = None
    args: list[str] = []
    i = 1
    while i < len(argv):
        if argv[i] == "--plot-iv":
            i += 1
            continue
        if argv[i] == "--exp-range":
            if i + 1 >= len(argv):
                print("missing value for --exp-range (use N:M)")
                sys.exit(1)
            exp_range = argv[i + 1]
            i += 2
            continue
        args.append(argv[i])
        i += 1

    expiry_idx = None
    for idx, token in enumerate(args):
        if is_date_token(token):
            expiry_idx = idx
            break
    if expiry_idx is None:
        symbols = [s.upper() for s in args]
        expiry = None
        outfile = None
    else:
        symbols = [s.upper() for s in args[:expiry_idx]]
        expiry = dash(args[expiry_idx])
        outfile = args[expiry_idx + 1] if len(args) > expiry_idx + 1 else None
        if len(args) > expiry_idx + 2:
            print("too many positional arguments")
            sys.exit(1)
    if not symbols:
        print("missing symbol(s)")
        sys.exit(1)
    if outfile is not None and len(symbols) > 1:
        print("outfile ignored when multiple symbols are provided")
        outfile = None

    for symbol in symbols:
        display_symbol = symbol.lstrip("^")
        default = f"{display_symbol}_{expiry}.csv" if expiry is not None else f"{display_symbol}_all.csv"
        out = outfile or default
        start = perf_counter()
        df, expiry_label = fetch_option_chain(symbol, expiry, exp_range)
        elapsed = perf_counter() - start
        timings[f"fetched option data {display_symbol}"] = time.time()
        df.to_csv(out, index=False)
        print(f"wrote {out}")
        print(df.head())  # quick sanity check
        try:
            summary_df = summarize_option_chain(df, expiry)
        except ValueError:
            print("volume/openInterest columns not found; skipping summary")
        else:
            print(f"summary for {display_symbol}")
            print(summary_df.to_string())
        timings[f"summarized option data {display_symbol}"] = time.time()
        if plot_iv:
            plot_iv_vs_strike(df, display_symbol, expiry_label)


if __name__ == "__main__":
    main(sys.argv)
    print_timings(timings, start)
