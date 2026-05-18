from __future__ import annotations

import datetime

import pandas as pd
from mootdx.quotes import Quotes


def get_stock_name(code: str) -> str:
    try:
        from mootdx.quotes import Quotes
        import re
        client = Quotes.factory(market="std")
        f10 = client.F10(code)
        if f10 and isinstance(f10, dict):
            text = f10.get("最新提示", "")
            match = re.search(rf"◇{code}\s+(\S+)\s+更新日期", text)
            if match:
                return match.group(1)
    except Exception:
        pass
    return code


def fetch_intraday_data(code: str, date: str) -> pd.DataFrame:
    client = Quotes.factory(market="std")
    bars = client.minutes(symbol=code, frequency=1, date=date, limit=240)

    if bars.empty:
        return pd.DataFrame()

    bars = bars.copy()
    
    n = len(bars)
    if n <= 120:
        times = pd.date_range(start=f"{date} 09:30", periods=n, freq="min")
    else:
        morning_n = 120
        afternoon_n = n - 120
        morning_times = pd.date_range(start=f"{date} 09:30", periods=morning_n, freq="min")
        afternoon_times = pd.date_range(start=f"{date} 13:00", periods=afternoon_n, freq="min")
        times = morning_times.union(afternoon_times)
    
    bars["time"] = times

    bars = bars.rename(columns={"price": "close"})
    bars["open"] = bars["close"].shift(1).fillna(bars["close"].iloc[0])
    bars["high"] = bars[["open", "close"]].max(axis=1)
    bars["low"] = bars[["open", "close"]].min(axis=1)
    bars["volume"] = bars["vol"]
    bars["amount"] = bars["volume"] * bars["close"]

    bars = bars[["time", "open", "close", "high", "low", "volume", "amount"]]
    return bars


def fetch_multi_day_intraday(code: str, start_date: str, end_date: str) -> dict[str, pd.DataFrame]:
    result = {}
    current = datetime.datetime.strptime(start_date, "%Y%m%d")
    end = datetime.datetime.strptime(end_date, "%Y%m%d")

    while current <= end:
        if current.weekday() < 5:
            date_str = current.strftime("%Y%m%d")
            try:
                df = fetch_intraday_data(code, date_str)
                if not df.empty:
                    result[date_str] = df
            except Exception:
                pass
        current += datetime.timedelta(days=1)

    return result


def get_previous_close(code: str, date: str) -> float:
    client = Quotes.factory(market="std")
    bars = client.minutes(symbol=code, frequency=1, date=date, limit=1)
    if bars.empty:
        return 0.0
    return float(bars["price"].iloc[0])
