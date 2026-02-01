#!/usr/bin/env python3
"""
download option prices (calls + puts) for one or more symbols/expirations to CSV

usage:
  python xget_option_prices.py SYMBOL [YYYYMMDD] [outfile.csv] [--expiry YYYYMMDD|YYYYMMDD:YYYYMMDD] [--plot-iv] [--timing] [--exp-range N:M]
  python xget_option_prices.py SYMBOL1 SYMBOL2 ... [YYYYMMDD] [--expiry YYYYMMDD|YYYYMMDD:YYYYMMDD] [--plot-iv] [--timing] [--exp-range N:M]

notes:
  - if YYYYMMDD is omitted and --expiry is not given, all expirations are fetched
  - --exp-range N:M uses days from today (inclusive); empty side means open-ended
  - if YYYYMMDD/--expiry and --exp-range are both provided, expirations are the union
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
    get_expirations,
    is_date_token,
    option_chain_df,
    parse_exp_range,
)
timings = pd.Series(dtype="float")
timings["imported modules"] = time.time()
pd.options.display.float_format = '{:.3f}'.format

def main(argv):
    if len(argv) < 2:
        print("usage: python xget_option_prices.py SYMBOL [YYYYMMDD] [outfile.csv] [--expiry YYYYMMDD|YYYYMMDD:YYYYMMDD] [--plot-iv] [--timing] [--exp-range N:M]")
        sys.exit(1)

    plot_iv = "--plot-iv" in argv
    exp_range = None
    expiry = None
    expiry_list = None
    expiry_range = None
    args: list[str] = []
    i = 1
    def _is_expiry_token(tok: str) -> bool:
        if is_date_token(tok):
            return True
        if ":" in tok:
            left, right = tok.split(":", 1)
            left_ok = (left == "") or is_date_token(left)
            right_ok = (right == "") or is_date_token(right)
            return left_ok and right_ok
        return False

    while i < len(argv):
        if argv[i] == "--plot-iv":
            i += 1
            continue
        if argv[i] == "--expiry":
            j = i + 1
            vals = []
            while j < len(argv) and not argv[j].startswith("--") and _is_expiry_token(argv[j]):
                vals.append(argv[j])
                j += 1
            if not vals:
                print("missing value for --expiry")
                sys.exit(1)
            if len(vals) == 1:
                token = vals[0]
                if ":" in token:
                    expiry_range = token
                else:
                    expiry = dash(token)
            else:
                expiry_list = [dash(v) for v in vals]
            i = j
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
        outfile = None
        if len(args) >= 2 and args[-1].lower().endswith(".csv"):
            outfile = args[-1]
            symbols = [s.upper() for s in args[:-1]]
        else:
            symbols = [s.upper() for s in args]
    else:
        symbols = [s.upper() for s in args[:expiry_idx]]
        if expiry is None and expiry_list is None and expiry_range is None:
            expiry = dash(args[expiry_idx])
        outfile = args[expiry_idx + 1] if len(args) > expiry_idx + 1 else None
        if len(args) > expiry_idx + 2:
            print("too many positional arguments")
            sys.exit(1)
    if not symbols:
        print("missing symbol(s)")
        sys.exit(1)
    multi_out = outfile is not None and len(symbols) > 1
    combined_frames = []

    for symbol in symbols:
        display_symbol = symbol.lstrip("^")
        default = f"{display_symbol}_{expiry}.csv" if expiry is not None else f"{display_symbol}_all.csv"
        out = outfile or default
        start = perf_counter()
        if expiry_list is not None or expiry_range is not None:
            exps = []
            if expiry_list is not None:
                exps.extend(expiry_list)
            if expiry_range is not None:
                start_s, end_s = expiry_range.split(":", 1)
                start_d = datetime.strptime(dash(start_s), "%Y-%m-%d").date()
                end_d = datetime.strptime(dash(end_s), "%Y-%m-%d").date()
                if end_d < start_d:
                    start_d, end_d = end_d, start_d
                avail = get_expirations(symbol)
                exps.extend([e for e in avail if start_d <= datetime.strptime(e, "%Y-%m-%d").date() <= end_d])
            if exp_range is not None:
                min_days, max_days = parse_exp_range(exp_range)
                avail = get_expirations(symbol)
                exps.extend(expirations_in_range(avail, min_days, max_days))
            exps = sorted(set(exps))
            frames = []
            for exp in exps:
                df_exp, _ = fetch_option_chain(symbol, exp, None)
                frames.append(df_exp)
            df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
            expiry_label = "MULTI"
        else:
            df, expiry_label = fetch_option_chain(symbol, expiry, exp_range)
        elapsed = perf_counter() - start
        timings[f"fetched option data {display_symbol}"] = time.time()
        if multi_out:
            df = df.copy()
            df["symbol"] = display_symbol
            combined_frames.append(df)
        else:
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
        if plot_iv and not multi_out:
            plot_iv_vs_strike(df, display_symbol, expiry_label)

    if multi_out:
        combined = pd.concat(combined_frames, ignore_index=True) if combined_frames else pd.DataFrame()
        combined.to_csv(outfile, index=False)
        print(f"wrote {outfile}")


if __name__ == "__main__":
    main(sys.argv)
    print_timings(timings, start)
