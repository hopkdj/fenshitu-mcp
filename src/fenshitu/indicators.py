from __future__ import annotations

import pandas as pd


def calc_avg_price(df: pd.DataFrame) -> pd.Series:
    cumulative_amount = df["amount"].cumsum(skipna=True)
    cumulative_volume = df["volume"].cumsum(skipna=True)
    avg = cumulative_amount / cumulative_volume
    avg = avg.replace([float("inf"), float("-inf")], float("nan"))
    return avg


def calc_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    close = df["close"]
    ema_fast = close.ewm(span=fast, adjust=False, ignore_na=True).mean()
    ema_slow = close.ewm(span=slow, adjust=False, ignore_na=True).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False, ignore_na=True).mean()
    macd = 2 * (dif - dea)
    return dif, dea, macd
