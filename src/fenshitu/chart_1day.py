from __future__ import annotations

import datetime
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd

CJK_FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
if os.path.exists(CJK_FONT):
    fm.fontManager.addfont(CJK_FONT)
    plt.rcParams["font.sans-serif"] = ["Noto Sans CJK JP"] + plt.rcParams["font.sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

from fenshitu.styles import (
    COLOR_BG, COLOR_BG_DARKER, COLOR_GRID, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_TEXT_BRIGHT, COLOR_UP, COLOR_DOWN, COLOR_PRICE_LINE, COLOR_AVG_LINE,
    COLOR_ZERO_LINE, COLOR_VOL_UP, COLOR_VOL_DOWN,
    IMG_WIDTH, IMG_HEIGHT_1DAY,
    MARGIN_TOP, MARGIN_BOTTOM, MARGIN_LEFT, MARGIN_RIGHT,
    MAIN_CHART_RATIO, VOL_CHART_RATIO,
    FONT_SIZE_TITLE, FONT_SIZE_INFO, FONT_SIZE_AXIS, FONT_SIZE_TIME,
    TIME_LABELS_1DAY,
)
from fenshitu.indicators import calc_avg_price


def generate_1day_chart(
    df: pd.DataFrame,
    stock_code: str,
    stock_name: str,
    date: str,
    output_path: str | None = None,
) -> str:
    if df.empty:
        raise ValueError("No data available for the specified date")

    df = df.copy()
    df["avg_price"] = calc_avg_price(df)

    prev_close = df["open"].iloc[0]
    close_price = df["close"].iloc[-1]
    high_price = df["high"].max()
    low_price = df["low"].min()
    total_volume = df["volume"].sum()
    pct_change = (close_price - prev_close) / prev_close * 100

    date_obj = datetime.datetime.strptime(date, "%Y%m%d")
    weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    date_display = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日 {weekday_names[date_obj.weekday()]}"

    fig = plt.figure(figsize=(IMG_WIDTH / 100, IMG_HEIGHT_1DAY / 100), dpi=100, facecolor=COLOR_BG)
    fig.subplots_adjust(left=0.08, right=0.92, top=0.88, bottom=0.12)

    gs = fig.add_gridspec(2, 1, height_ratios=[MAIN_CHART_RATIO / (MAIN_CHART_RATIO + VOL_CHART_RATIO), VOL_CHART_RATIO / (MAIN_CHART_RATIO + VOL_CHART_RATIO)], hspace=0.05)
    ax_price = fig.add_subplot(gs[0])
    ax_vol = fig.add_subplot(gs[1], sharex=ax_price)

    fig.patch.set_facecolor(COLOR_BG)
    ax_price.set_facecolor(COLOR_BG_DARKER)
    ax_vol.set_facecolor(COLOR_BG_DARKER)

    morning_mask = df["time"].dt.strftime("%H:%M") <= "11:30"
    afternoon_mask = df["time"].dt.strftime("%H:%M") >= "13:00"
    
    morning_df = df[morning_mask].copy()
    afternoon_df = df[afternoon_mask].copy()
    
    afternoon_df["display_time"] = afternoon_df["time"] - pd.Timedelta(hours=1, minutes=30)
    morning_df["display_time"] = morning_df["time"]
    
    display_times = pd.concat([morning_df["display_time"], afternoon_df["display_time"]])

    ax_price.plot(display_times, pd.concat([morning_df["close"], afternoon_df["close"]]), color=COLOR_PRICE_LINE, linewidth=1)
    ax_price.plot(display_times, pd.concat([morning_df["avg_price"], afternoon_df["avg_price"]]), color=COLOR_AVG_LINE, linewidth=1)
    ax_price.axhline(y=prev_close, color="#999999", linestyle="--", linewidth=0.8, alpha=0.8, zorder=5)

    ax_price.grid(True, color=COLOR_GRID, linestyle="-", linewidth=0.5, alpha=0.5)

    price_range = df["close"].max() - df["close"].min()
    padding = price_range * 0.05
    ax_price.set_ylim(df["close"].min() - padding, df["close"].max() + padding)

    ax_price.tick_params(axis="y", colors=COLOR_TEXT, labelsize=FONT_SIZE_AXIS)
    ax_price.spines["top"].set_visible(False)
    ax_price.spines["right"].set_visible(False)
    ax_price.spines["bottom"].set_visible(False)
    ax_price.spines["left"].set_color(COLOR_GRID)

    sec_axis = ax_price.twinx()
    sec_axis.set_ylim(ax_price.get_ylim())
    sec_axis.set_yticks(ax_price.get_yticks())
    sec_labels = [(y - prev_close) / prev_close * 100 for y in ax_price.get_yticks()]
    sec_axis.set_yticklabels([f"{l:+.2f}%" for l in sec_labels], color=COLOR_TEXT, fontsize=FONT_SIZE_AXIS)
    sec_axis.spines["top"].set_visible(False)
    sec_axis.spines["right"].set_visible(False)
    sec_axis.spines["bottom"].set_visible(False)
    sec_axis.spines["left"].set_visible(False)

    morning_vol = morning_df[["display_time", "open", "close", "volume"]]
    afternoon_vol = afternoon_df[["display_time", "open", "close", "volume"]]
    
    morning_colors = [COLOR_UP if c >= o else COLOR_DOWN for o, c in zip(morning_vol["open"], morning_vol["close"])]
    afternoon_colors = [COLOR_UP if c >= o else COLOR_DOWN for o, c in zip(afternoon_vol["open"], afternoon_vol["close"])]
    
    ax_vol.bar(morning_vol["display_time"], morning_vol["volume"], color=morning_colors, alpha=0.7, width=0.0006)
    ax_vol.bar(afternoon_vol["display_time"], afternoon_vol["volume"], color=afternoon_colors, alpha=0.7, width=0.0006)
    ax_vol.grid(True, color=COLOR_GRID, linestyle="-", linewidth=0.5, alpha=0.3)
    ax_vol.tick_params(axis="y", colors=COLOR_TEXT_DIM, labelsize=FONT_SIZE_AXIS - 1)
    ax_vol.spines["top"].set_visible(False)
    ax_vol.spines["right"].set_visible(False)
    ax_vol.spines["bottom"].set_color(COLOR_GRID)
    ax_vol.spines["left"].set_color(COLOR_GRID)

    ax_price.tick_params(axis="x", bottom=False, labelbottom=False)
    ax_vol.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax_vol.tick_params(axis="x", colors=COLOR_TEXT_DIM, labelsize=FONT_SIZE_TIME, rotation=0)

    time_ticks = [
        datetime.datetime.strptime(f"{date} 09:30", "%Y%m%d %H:%M"),
        datetime.datetime.strptime(f"{date} 10:30", "%Y%m%d %H:%M"),
        datetime.datetime.strptime(f"{date} 11:30", "%Y%m%d %H:%M"),
        datetime.datetime.strptime(f"{date} 11:30", "%Y%m%d %H:%M") + pd.Timedelta(minutes=60),
        datetime.datetime.strptime(f"{date} 11:30", "%Y%m%d %H:%M") + pd.Timedelta(minutes=120),
    ]
    ax_vol.set_xticks(time_ticks)
    ax_vol.set_xticklabels(["09:30", "10:30", "11:30", "14:00", "15:00"])

    title_text = f"{stock_name}({stock_code})  {date_display}"
    fig.text(0.08, 0.94, title_text, color=COLOR_TEXT_BRIGHT, fontsize=FONT_SIZE_TITLE, fontweight="bold")

    change_color = COLOR_UP if pct_change >= 0 else COLOR_DOWN
    change_sign = "+" if pct_change >= 0 else ""
    info_text = f"分时  收盘:{close_price:.2f}  涨幅:{change_sign}{pct_change:.2f}%  最高:{high_price:.2f}  最低:{low_price:.2f}  成交:{total_volume/10000:.2f}万"
    fig.text(0.08, 0.90, info_text, color=COLOR_TEXT, fontsize=FONT_SIZE_INFO)

    if output_path is None:
        output_path = f"/tmp/fenshi_{stock_code}_{date}.png"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=100, facecolor=COLOR_BG, bbox_inches="tight")
    plt.close(fig)

    return output_path
