#!/usr/bin/env python3
"""
Shared option-chain fetch utilities.
"""

from datetime import datetime
from typing import Tuple

import pandas as pd
import yfinance as yf


def option_chain_df(symbol: str, expiry: str | None) -> pd.DataFrame:
    """Get option prices for one or all expirations (if expiry is None)."""
    tkr = yf.Ticker(symbol)
    if expiry is None:
        if not tkr.options:
            raise ValueError("no expirations available")
        frames: list[pd.DataFrame] = []
        for exp in tkr.options:
            chain = tkr.option_chain(exp)
            calls = chain.calls.assign(option_type="call", expiration=exp)
            puts = chain.puts.assign(option_type="put", expiration=exp)
            frames.append(pd.concat([calls, puts], ignore_index=True))
        return pd.concat(frames, ignore_index=True)

    if expiry not in tkr.options:
        raise ValueError(f"{expiry} not in {tkr.options}")
    chain = tkr.option_chain(expiry)
    calls = chain.calls.assign(option_type="call", expiration=expiry)
    puts = chain.puts.assign(option_type="put", expiration=expiry)
    return pd.concat([calls, puts], ignore_index=True)


def dash(exp: str) -> str:
    """yyyymmdd to yyyy-mm-dd (yfinance’s format)."""
    return f"{exp[:4]}-{exp[4:6]}-{exp[6:]}" if exp.isdigit() and len(exp) == 8 else exp


def parse_exp_range(spec: str) -> Tuple[int | None, int | None]:
    """Parse N:M (days from today). Empty side means open-ended."""
    if ":" not in spec:
        raise ValueError("exp-range must be in N:M form")
    left, right = spec.split(":", 1)
    min_days = int(left) if left != "" else None
    max_days = int(right) if right != "" else None
    if min_days is not None and min_days < 0:
        raise ValueError("exp-range minimum must be >= 0")
    if max_days is not None and max_days < 0:
        raise ValueError("exp-range maximum must be >= 0")
    if min_days is not None and max_days is not None and min_days > max_days:
        raise ValueError("exp-range minimum exceeds maximum")
    return min_days, max_days


def expirations_in_range(options: list[str], min_days: int | None, max_days: int | None) -> list[str]:
    """Filter expiration strings by days from today (inclusive)."""
    today = datetime.now().date()
    selected: list[str] = []
    for exp in options:
        try:
            exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
        except ValueError:
            continue
        delta = (exp_date - today).days
        if min_days is not None and delta < min_days:
            continue
        if max_days is not None and delta > max_days:
            continue
        selected.append(exp)
    return selected


def is_date_token(token: str) -> bool:
    if token.isdigit() and len(token) == 8:
        return True
    try:
        datetime.strptime(token, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def fetch_option_chain(
    symbol: str,
    expiry: str | None,
    exp_range: str | None,
) -> tuple[pd.DataFrame, str]:
    if exp_range is None:
        df = option_chain_df(symbol, expiry)
        expiry_label = expiry or "ALL"
        return df, expiry_label

    min_days, max_days = parse_exp_range(exp_range)
    tkr = yf.Ticker(symbol)
    options = list(tkr.options)
    range_exps = expirations_in_range(options, min_days, max_days)
    if expiry is None:
        exps = range_exps
    else:
        exps = sorted(set(range_exps + [expiry]))
    if not exps:
        raise ValueError("no expirations matched")
    frames: list[pd.DataFrame] = []
    for exp in exps:
        chain = tkr.option_chain(exp)
        calls = chain.calls.assign(option_type="call", expiration=exp)
        puts = chain.puts.assign(option_type="put", expiration=exp)
        frames.append(pd.concat([calls, puts], ignore_index=True))
    df = pd.concat(frames, ignore_index=True)
    return df, "MULTI"


def get_expirations(symbol: str) -> list[str]:
    """Return available expirations for symbol (yyyy-mm-dd)."""
    tkr = yf.Ticker(symbol)
    return list(tkr.options)


def get_spot(symbol: str) -> float | None:
    """Best-effort last price for symbol."""
    try:
        tkr = yf.Ticker(symbol)
        if getattr(tkr, "fast_info", None):
            val = tkr.fast_info.get("last_price") or tkr.fast_info.get("lastPrice")
            if val:
                return float(val)
        hist = tkr.history(period="1d")
        if not hist.empty and "Close" in hist.columns:
            return float(hist["Close"].iloc[-1])
    except Exception:
        return None
    return None
