from __future__ import annotations

import base64
import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from fenshitu.data_fetcher import fetch_intraday_data, fetch_multi_day_intraday, get_stock_name
from fenshitu.chart_1day import generate_1day_chart
from fenshitu.chart_7day import generate_7day_chart


mcp = FastMCP("fenshitu-mcp")


@mcp.tool()
def generate_intraday_chart(
    code: str,
    date: str = "",
    output_path: str = "",
) -> str:
    if not date:
        date = datetime.datetime.now().strftime("%Y%m%d")

    df = fetch_intraday_data(code, date)
    if df.empty:
        return f"No intraday data available for {code} on {date}. It might be a non-trading day."

    stock_name = get_stock_name(code)
    result_path = generate_1day_chart(df, code, stock_name, date, output_path or None)

    with open(result_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    return f"data:image/png;base64,{image_data}"


@mcp.tool()
def generate_multi_day_chart(
    code: str,
    start_date: str,
    end_date: str = "",
    output_path: str = "",
) -> str:
    if not end_date:
        end_date = start_date

    start_dt = datetime.datetime.strptime(start_date, "%Y%m%d")
    end_dt = datetime.datetime.strptime(end_date, "%Y%m%d")
    days_diff = (end_dt - start_dt).days

    if days_diff > 6:
        return "Error: Maximum date range is 7 days (start_date to end_date inclusive)"

    data_dict = fetch_multi_day_intraday(code, start_date, end_date)
    if not data_dict:
        return f"No intraday data available for {code} between {start_date} and {end_date}."

    stock_name = get_stock_name(code)
    result_path = generate_7day_chart(data_dict, code, stock_name, output_path or None)

    with open(result_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    num_days = len(data_dict)
    return f"data:image/png;base64,{image_data}"


def main():
    import os
    
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    
    if transport == "http":
        import uvicorn
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = int(os.environ.get("MCP_PORT", "8090"))
        app = mcp.streamable_http_app()
        uvicorn.run(app, host=host, port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
