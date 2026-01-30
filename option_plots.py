#!/usr/bin/env python3
"""
Option plotting utilities.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf


def plot_iv_vs_strike(
    df: pd.DataFrame,
    symbol: str,
    expiry: str,
    low_mult: float = 0.90,
    high_mult: float = 1.10,
) -> None:
    """Plot implied volatility vs strike by option type."""
    if "impliedVolatility" not in df.columns or "strike" not in df.columns:
        print("impliedVolatility/strike columns not found; skipping plot")
        return

    plot_df = df[["strike", "impliedVolatility", "option_type"]].dropna()
    if plot_df.empty:
        print("no implied volatility data to plot")
        return

    spot = None
    try:
        tkr = yf.Ticker(symbol)
        if getattr(tkr, "fast_info", None):
            spot = tkr.fast_info.get("last_price") or tkr.fast_info.get("lastPrice")
        if spot is None:
            hist = tkr.history(period="1d")
            if not hist.empty and "Close" in hist.columns:
                spot = float(hist["Close"].iloc[-1])
    except Exception:
        spot = None

    if spot is not None:
        low = low_mult * spot
        high = high_mult * spot
        plot_df = plot_df[(plot_df["strike"] >= low) & (plot_df["strike"] <= high)]
        if plot_df.empty:
            print("no strikes in requested range; skipping plot")
            return
    else:
        print("spot price unavailable; plotting all strikes")

    fig, ax = plt.subplots()
    for opt_type, color in (("call", "tab:blue"), ("put", "tab:orange")):
        sub = plot_df[plot_df["option_type"] == opt_type]
        if not sub.empty:
            sub = sub.sort_values("strike")
            ax.plot(sub["strike"], sub["impliedVolatility"], label=opt_type, color=color)

    ax.set_title(f"{symbol} {expiry} implied volatility vs strike")
    ax.set_xlabel("strike")
    ax.set_ylabel("implied volatility")
    ax.legend()
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.show()
