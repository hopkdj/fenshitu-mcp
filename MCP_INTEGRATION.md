# Fenshitu MCP 服务接入文档

## 服务概述

Fenshitu MCP 服务是一个专门用于生成 A 股股票分时图的 Model Context Protocol (MCP) 服务。该服务支持生成单日分时图和多日分时图（最多 7 天），图表样式参考了中国主流炒股软件（如东方财富、同花顺）的风格。

## 服务信息

- **服务名称**: `fenshitu-mcp`
- **服务类型**: MCP Server
- **传输协议**: stdio（默认）/ HTTP
- **默认端口**: 8090（HTTP 模式）
- **数据源**: mootdx（通达信数据接口）

## 可用工具

### 1. generate_intraday_chart

生成单日 A 股分时图。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `code` | string | 是 | - | A 股股票代码，如 `600379`、`000001` |
| `date` | string | 否 | 当天 | 交易日期，格式 `YYYYMMDD`，如 `20240515` |
| `output_path` | string | 否 | 自动生成 | 输出图片路径，默认 `/tmp/fenshi_{code}_{date}.png` |

#### 返回值

- 成功：返回 base64 编码的 PNG 图片数据，格式为 `data:image/png;base64,{base64_data}`
- 失败：返回错误信息字符串

#### 示例

```json
{
  "tool": "generate_intraday_chart",
  "arguments": {
    "code": "600379",
    "date": "20240515"
  }
}
```

### 2. generate_multi_day_chart

生成多日 A 股分时图（最多 7 天）。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `code` | string | 是 | - | A 股股票代码，如 `600379`、`000001` |
| `start_date` | string | 是 | - | 开始日期，格式 `YYYYMMDD`，如 `20240513` |
| `end_date` | string | 否 | `start_date` | 结束日期，格式 `YYYYMMDD`，如 `20240517` |
| `output_path` | string | 否 | 自动生成 | 输出图片路径，默认 `/tmp/fenshi_{code}_7day.png` |

#### 限制

- 日期范围最大为 7 天（包含起止日期）
- 自动跳过非交易日（周末、节假日）

#### 返回值

- 成功：返回 base64 编码的 PNG 图片数据，格式为 `data:image/png;base64,{base64_data}`
- 失败：返回错误信息字符串

#### 示例

```json
{
  "tool": "generate_multi_day_chart",
  "arguments": {
    "code": "600379",
    "start_date": "20240513",
    "end_date": "20240517"
  }
}
```

## 配置方式

### 方式一：stdio 模式（推荐用于 AI 助手集成）

在 AI 助手的 MCP 配置文件中添加：

```json
{
  "mcpServers": {
    "fenshitu-mcp": {
      "command": "/opt/ss-code/mcp-fenshitu/.venv/bin/python",
      "args": ["-m", "fenshitu.server"],
      "cwd": "/opt/ss-code/mcp-fenshitu"
    }
  }
}
```

### 方式二：HTTP 模式（独立服务）

1. 启动服务：
   ```bash
   export MCP_TRANSPORT=http
   export MCP_HOST=0.0.0.0
   export MCP_PORT=8090
   /opt/ss-code/mcp-fenshitu/.venv/bin/python -m fenshitu.server
   ```

2. 或使用 systemd 服务（已配置开机自启）：
   ```bash
   systemctl start fenshitu-mcp.service
   ```

3. 在 AI 助手的 MCP 配置文件中添加：
   ```json
   {
     "mcpServers": {
       "fenshitu-mcp": {
         "url": "http://localhost:8090"
       }
     }
   }
   ```

## 图表特性

### 单日分时图
- 深色背景（#1a1a1a）
- 白色价格线 + 黄色均价线（VWAP）
- 红涨绿跌成交量柱状图
- 双 Y 轴（左：价格，右：涨跌幅百分比）
- 时间轴：09:30, 10:30, 11:30, 13:00, 14:00, 15:00
- 标题显示股票名称、代码、日期、星期
- 信息栏显示收盘价、涨幅、最高价、最低价、成交量

### 多日分时图
- 5 个交易日横向排列
- 每日独立的价格图和成交量图
- 统一的价格刻度（便于对比）
- 底部 MACD 指标（DIF 白线、DEA 黄线、红/青柱状图）
- 每日日期标签

## 使用注意事项

1. **股票代码格式**
   - 支持 6 位数字代码
   - 沪市：600xxx、601xxx、603xxx、688xxx
   - 深市：000xxx、002xxx、300xxx

2. **日期格式**
   - 必须为 `YYYYMMDD` 格式
   - 自动识别非交易日（周末、节假日）
   - 如果指定日期无数据，返回错误信息

3. **数据源限制**
   - 使用 mootdx 连接通达信服务器
   - 需要网络连接
   - 历史数据可能有限制

4. **图片输出**
   - 返回 base64 编码的 PNG 图片
   - 可直接在支持 data URL 的环境中显示
   - 也可保存到指定路径

## 错误处理

服务会返回以下错误信息：

- `No intraday data available for {code} on {date}. It might be a non-trading day.` - 指定日期无数据
- `Error: Maximum date range is 7 days (start_date to end_date inclusive)` - 日期范围超过 7 天
- `No intraday data available for {code} between {start_date} and {end_date}.` - 日期范围内无数据

## 系统服务管理

服务已配置为 systemd 服务，支持开机自启：

```bash
# 查看状态
systemctl status fenshitu-mcp.service

# 启动服务
systemctl start fenshitu-mcp.service

# 停止服务
systemctl stop fenshitu-mcp.service

# 重启服务
systemctl restart fenshitu-mcp.service

# 启用开机自启
systemctl enable fenshitu-mcp.service

# 禁用开机自启
systemctl disable fenshitu-mcp.service

# 查看日志
journalctl -u fenshitu-mcp.service -f
```

## 依赖环境

- Python 3.12+
- 虚拟环境：`/opt/ss-code/mcp-fenshitu/.venv`
- 主要依赖包：
  - `mcp>=1.20.0`
  - `mootdx>=0.11.0`
  - `akshare>=1.14.0`
  - `matplotlib>=3.8.0`
  - `pandas>=2.0.0`
  - `numpy>=1.24.0`

## 项目结构

```
/opt/ss-code/mcp-fenshitu/
── pyproject.toml          # 项目配置
├── requirements.txt        # 依赖列表
├── .venv/                  # Python 虚拟环境
├── img_fenshi_1day.jpg     # 参考图 1（单日分时）
├── img_fenshi_7day.jpg     # 参考图 2（多日分时）
└── src/fenshitu/
    ├── __init__.py
    ├── styles.py           # 样式常量
    ├── data_fetcher.py     # 数据获取模块
    ├── indicators.py       # 技术指标计算
    ├── chart_1day.py       # 单日分时图生成器
    ├── chart_7day.py       # 多日分时图生成器
    └── server.py           # MCP 服务入口
```

## 更新日志

### v0.1.4 (2026-05-18)
- 移除多日分时图中的 MACD 指标，避免午休时段数据断开导致的显示异常
- 优化多日图布局，价格图和成交量图占据全部空间，显示更清晰
- 简化代码结构，移除不必要的 MACD 计算逻辑

### v0.1.3 (2026-05-18)
- 修复数据获取问题，现在正确生成 A 股交易时间戳（上午 09:30-11:30，下午 13:00-15:00），确保每天获取完整的 240 根分钟 bar
- 修复多日图时间轴标签重叠问题，优化 x 轴刻度显示（09:30, 11:30, 13:00, 15:00）
- 修复成交量柱显示问题，调整柱状图宽度（0.0006 天 ≈ 1 分钟），确保每分钟成交量柱清晰可见
- 优化数据获取逻辑，使用 `union` 方法拼接上午和下午时间戳，避免 pandas 兼容性问题

### v0.1.2 (2026-05-18)
- 修复股票名称获取问题，使用 mootdx F10 数据正确显示股票名称（如"平安银行"）
- 修复午休时段（11:30-13:00）图表绘制问题，现在将上午和下午数据分开绘制，避免直线连接
- 优化图表生成逻辑，确保价格线和成交量柱状图在午休时段正确断开

### v0.1.1 (2026-05-18)
- 修复股票名称获取问题，现在正确显示股票名称（如"平安银行"）而不是代码
- 修复午休时段（11:30-13:00）图表绘制问题，现在正确断开连接而不是画直线
- 优化技术指标计算，正确处理 NaN 值

### v0.1.0 (2026-05-18)
- 初始版本
- 支持单日分时图生成
- 支持多日分时图生成（最多 7 天）
- 支持 stdio 和 HTTP 两种传输模式
- 配置 systemd 服务支持开机自启
