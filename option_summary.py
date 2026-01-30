import pandas as pd


def summarize_option_chain(df: pd.DataFrame, expiry: str | None) -> pd.DataFrame:
    """Summarize option chain by expiration."""
    if "expiration" not in df.columns:
        df = df.copy()
        df["expiration"] = expiry if expiry is not None else "ALL"
    if "volume" not in df.columns or "openInterest" not in df.columns:
        raise ValueError("volume/openInterest columns not found")

    df = df.copy()
    df["volume"] = df["volume"].fillna(0)
    df["openInterest"] = df["openInterest"].fillna(0)
    summary_df = (
        df.groupby("expiration", dropna=False)
        .agg(
            num_strikes=("strike", "nunique"),
            min_strike=("strike", "min"),
            max_strike=("strike", "max"),
            total_volume=("volume", "sum"),
            total_open_interest=("openInterest", "sum"),
            call_strikes_with_bid_ask_pos=(
                "strike",
                lambda s: (
                    df.loc[s.index, ["bid", "ask"]].fillna(0).gt(0).all(axis=1)
                    & df.loc[s.index, "option_type"].eq("call")
                ).sum(),
            ),
            put_strikes_with_bid_ask_pos=(
                "strike",
                lambda s: (
                    df.loc[s.index, ["bid", "ask"]].fillna(0).gt(0).all(axis=1)
                    & df.loc[s.index, "option_type"].eq("put")
                ).sum(),
            ),
        )
        .reset_index()
    )
    if (
        summary_df["min_strike"].dropna().apply(float.is_integer).all()
        and summary_df["max_strike"].dropna().apply(float.is_integer).all()
    ):
        summary_df["min_strike"] = summary_df["min_strike"].astype(int)
        summary_df["max_strike"] = summary_df["max_strike"].astype(int)
    summary_df["total_volume"] = summary_df["total_volume"].astype(int)
    summary_df["total_open_interest"] = summary_df["total_open_interest"].astype(int)
    return summary_df
