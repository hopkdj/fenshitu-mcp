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
    IMG_WIDTH, IMG_HEIGHT_7DAY,
    MAIN_CHART_RATIO, VOL_CHART_RATIO,
    FONT_SIZE_TITLE, FONT_SIZE_INFO, FONT_SIZE_AXIS, FONT_SIZE_TIME,
)
from fenshitu.indicators import calc_avg_price


def generate_7day_chart(
    data_dict: dict[str, pd.DataFrame],
    stock_code: str,
    stock_name: str,
    output_path: str | None = None,
) -> str:
    if not data_dict:
        raise ValueError("No data available for the specified date range")

    sorted_dates = sorted(data_dict.keys())
    num_days = len(sorted_dates)

    all_prices = []
    all_volumes = []

    processed_data = []
    for date_str in sorted_dates:
        df = data_dict[date_str].copy()
        df["avg_price"] = calc_avg_price(df)
        all_prices.extend(df["close"].tolist())
        all_volumes.extend(df["volume"].tolist())
        processed_data.append(df)

    global_price_min = min(all_prices)
    global_price_max = max(all_prices)
    price_padding = (global_price_max - global_price_min) * 0.05

    fig = plt.figure(figsize=(IMG_WIDTH / 100, IMG_HEIGHT_7DAY / 100), dpi=100, facecolor=COLOR_BG)
    fig.subplots_adjust(left=0.06, right=0.94, top=0.92, bottom=0.08)

    chart_height_ratio = MAIN_CHART_RATIO + VOL_CHART_RATIO
    gs_top = fig.add_gridspec(2, num_days, height_ratios=[MAIN_CHART_RATIO / chart_height_ratio, VOL_CHART_RATIO / chart_height_ratio], hspace=0.05, wspace=0.02)

    fig.patch.set_facecolor(COLOR_BG)

    for day_idx, (date_str, df) in enumerate(zip(sorted_dates, processed_data)):
        ax_price = fig.add_subplot(gs_top[0, day_idx])
        ax_vol = fig.add_subplot(gs_top[1, day_idx], sharex=ax_price)

        ax_price.set_facecolor(COLOR_BG_DARKER)
        ax_vol.set_facecolor(COLOR_BG_DARKER)

        morning_mask = df["time"].dt.strftime("%H:%M") <= "11:30"
        afternoon_mask = df["time"].dt.strftime("%H:%M") >= "13:00"
        
        morning_df = df[morning_mask].copy()
        afternoon_df = df[afternoon_mask].copy()
        
        afternoon_df["display_time"] = afternoon_df["time"] - pd.Timedelta(hours=1, minutes=30)
        morning_df["display_time"] = morning_df["time"]
        
        display_times = pd.concat([morning_df["display_time"], afternoon_df["display_time"]])
        
        prev_close = df["open"].iloc[0]

        ax_price.plot(display_times, pd.concat([morning_df["close"], afternoon_df["close"]]), color=COLOR_PRICE_LINE, linewidth=0.8)
        ax_price.plot(display_times, pd.concat([morning_df["avg_price"], afternoon_df["avg_price"]]), color=COLOR_AVG_LINE, linewidth=0.8)
        ax_price.axhline(y=prev_close, color="#999999", linestyle="--", linewidth=0.8, alpha=0.8, zorder=5)

        ax_price.set_ylim(global_price_min - price_padding, global_price_max + price_padding)

        ax_price.grid(True, color=COLOR_GRID, linestyle="-", linewidth=0.3, alpha=0.4)
        ax_price.tick_params(axis="y", colors=COLOR_TEXT_DIM, labelsize=FONT_SIZE_AXIS - 2)
        ax_price.tick_params(axis="x", bottom=False, labelbottom=False)

        for spine in ax_price.spines.values():
            spine.set_color(COLOR_GRID)
            spine.set_linewidth(0.3)

        if day_idx == 0:
            ax_price.set_ylabel("价格", color=COLOR_TEXT_DIM, fontsize=FONT_SIZE_AXIS - 2)
        if day_idx == num_days - 1:
            sec_axis = ax_price.twinx()
            sec_axis.set_ylim(ax_price.get_ylim())
            sec_axis.set_yticks(ax_price.get_yticks())
            sec_labels = [(y - prev_close) / prev_close * 100 for y in ax_price.get_yticks()]
            sec_axis.set_yticklabels([f"{l:+.1f}%" for l in sec_labels], color=COLOR_TEXT_DIM, fontsize=FONT_SIZE_AXIS - 2)
            sec_axis.spines["top"].set_visible(False)
            sec_axis.spines["right"].set_visible(False)
            sec_axis.spines["bottom"].set_visible(False)
            sec_axis.spines["left"].set_visible(False)

        date_obj = datetime.datetime.strptime(date_str, "%Y%m%d")
        ax_price.text(0.5, 0.95, f"{date_obj.month}/{date_obj.day}", transform=ax_price.transAxes,
                      ha="center", color=COLOR_TEXT_DIM, fontsize=FONT_SIZE_TIME - 1)

        morning_vol = morning_df[["display_time", "open", "close", "volume"]]
        afternoon_vol = afternoon_df[["display_time", "open", "close", "volume"]]
        
        morning_colors = [COLOR_UP if c >= o else COLOR_DOWN for o, c in zip(morning_vol["open"], morning_vol["close"])]
        afternoon_colors = [COLOR_UP if c >= o else COLOR_DOWN for o, c in zip(afternoon_vol["open"], afternoon_vol["close"])]
        
        ax_vol.bar(morning_vol["display_time"], morning_vol["volume"], color=morning_colors, alpha=0.6, width=0.0006)
        ax_vol.bar(afternoon_vol["display_time"], afternoon_vol["volume"], color=afternoon_colors, alpha=0.6, width=0.0006)
        ax_vol.grid(True, color=COLOR_GRID, linestyle="-", linewidth=0.3, alpha=0.3)
        ax_vol.tick_params(axis="y", colors=COLOR_TEXT_DIM, labelsize=FONT_SIZE_AXIS - 3)
        ax_vol.tick_params(axis="x", colors=COLOR_TEXT_DIM, labelsize=FONT_SIZE_TIME - 1, rotation=0)

        for spine in ax_vol.spines.values():
            spine.set_color(COLOR_GRID)
            spine.set_linewidth(0.3)

        time_ticks = [
            datetime.datetime.strptime(f"{date_str} 09:30", "%Y%m%d %H:%M"),
            datetime.datetime.strptime(f"{date_str} 11:30", "%Y%m%d %H:%M"),
            datetime.datetime.strptime(f"{date_str} 11:30", "%Y%m%d %H:%M") + pd.Timedelta(minutes=60),
            datetime.datetime.strptime(f"{date_str} 11:30", "%Y%m%d %H:%M") + pd.Timedelta(minutes=120),
        ]
        ax_vol.set_xticks(time_ticks)
        ax_vol.set_xticklabels(["09:30", "11:30", "14:00", "15:00"], fontsize=FONT_SIZE_TIME - 2)

        if day_idx > 0:
            ax_vol.set_yticks([])
            ax_price.set_yticks([])

    title_text = f"{stock_name}({stock_code})  多日分时"
    fig.text(0.06, 0.96, title_text, color=COLOR_TEXT_BRIGHT, fontsize=FONT_SIZE_TITLE, fontweight="bold")

    if output_path is None:
        output_path = f"/tmp/fenshi_{stock_code}_7day.png"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=100, facecolor=COLOR_BG, bbox_inches="tight")
    plt.close(fig)

    return output_path
