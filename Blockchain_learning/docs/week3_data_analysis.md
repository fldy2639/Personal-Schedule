# Week 3：数据分析实战（USDC 时间序列）

## 1. 学习目标

在 Week 2 的 USDC `Transfer` 事件 CSV 基础上，完成链上时间序列分析闭环：

1. 按 UTC 日历日聚合，得到每日转账量与每日转账日志条数。
2. 对指定地址做收发与净流入统计，理解「日志条数 ≠ 交易笔数」。
3. 使用可复现的本地 CSV 作为数据源（与 `analyzer.py` 分析函数对接）。

---

## 2. 数据准备

- 输入：Week 2 产出的 `data/usdc_transfers_*.csv`
- 必备列：`transaction_hash`, `block_number`, `log_index`, `from`, `to`, `value_raw`, `value_usdc`, `timestamp`, `datetime`
- 若尚无文件，请先运行 Week 2 脚本导出事件数据。

---

## 3. 关键分析口径

### 3.1 每日转账量（Daily Volume）

- 口径：按 `date`（**UTC**）分组，对当日 `value_usdc` **求和**
- 输出列：`date`, `daily_volume_usdc`

### 3.2 每日转账笔数（Daily Tx Count）

- 口径：按 `date`（UTC）分组，统计当日 **Transfer 日志条数**
- 输出列：`date`, `daily_tx_count`
- 说明：一笔交易可能包含多条 `Transfer` 日志，因此该指标**不是** Etherscan 上的「交易笔数」。

### 3.3 地址收发统计（Address Activity）

- 转入：`to` 等于目标地址（大小写不敏感）
- 转出：`from` 等于目标地址
- 常用指标：`total_received_usdc`, `total_sent_usdc`, `net_flow_usdc`（净流入 = 收 - 支）
- `first_seen` / `last_seen`：该地址在**当前样本**中首次/末次出现在 `from` 或 `to` 的时间（UTC）

---

## 4. 运行方式

在项目根目录 `Blockchain_learning/` 下执行。

### 4.1 CSV 模式（推荐，可复现）

依赖 Week 2 导出的 `data/usdc_transfers_*.csv`，无需联网（除读取文件外）。

```bash
# 默认：使用 data/ 下最新的 usdc_transfers_*.csv
python week3/week3_analysis.py --source csv

# 指定 CSV
python week3/week3_analysis.py --source csv --csv-path data/usdc_transfers_1775815222.csv

# 同时统计某一地址的收发与净流入
python week3/week3_analysis.py --source csv --address 0x你的地址

# 指定输出目录（默认 data/week3/）
python week3/week3_analysis.py --source csv --output-dir data/week3
```

### 4.2 实时模式（可选）

通过 `config.get_alchemy_rpc_url()` 连接节点，拉取最近若干区块内的 USDC `Transfer` 日志再聚合（需配置 `.env` 中的 `ALCHEMY_API_KEY`）。注意：日志量大时 RPC 调用较多，且脚本内会按日志查询区块时间戳，耗时可能较长。

```bash
python week3/week3_analysis.py --source realtime --blocks 100
python week3/week3_analysis.py --source realtime --blocks 200 --chunk-size 10 --address 0x你的地址
```

输出文件（文件名带 UTC 时间戳）：

- `data/week3/daily_volume_*.csv`
- `data/week3/daily_tx_count_*.csv`
- `data/week3/address_stats_*.json`（未传 `--address` 时为空对象 `{}`）
- `data/week3/daily_volume_plot_*.html`（已安装 `plotly` 时自动生成，可在浏览器打开查看折线图）

---

## 5. Notebook 探索

```bash
jupyter notebook notebooks/week3_usdc_daily_analysis.ipynb
```

Notebook 与脚本共用同一套 CSV 与分析逻辑（`analyzer`），便于对照图表与导出的 CSV 是否一致。

---

## 6. 测试

```bash
# 若本机 pytest 因全局插件报错，可临时关闭自动加载插件：
# Windows PowerShell: $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
pytest tests/test_analyzer.py
```

---

## 7. 验证清单

1. `daily_volume_*.csv` 与 `daily_tx_count_*.csv` 成功生成，日期列为 UTC 日历日。
2. 对某一地址，`address_stats_*.json` 中 `net_flow_usdc` 等于 `total_received_usdc - total_sent_usdc`。
3. 控制台摘要中的「样本内总量」与 `daily_volume` 各日之和一致（允许浮点舍入误差）。

---

## 8. 常见误区

1. **把日志条数当「用户点的交易数」**  
   一笔合约交互可能触发多条 ERC-20 `Transfer` 日志。

2. **金额显示为两位小数就忽略精度**  
   USDC 为 6 位小数，展示时可提高小数位以免误解。

3. **混用本地时区与 UTC**  
   「按天」统计务必统一为 UTC，否则跨日边界会与链上浏览器不一致。

---

## 9. 与 Dune 的衔接建议

在 Dune（如 `ethereum.logs`）中可复现相近口径：

1. 过滤 USDC 合约地址  
2. 过滤 `Transfer` 的 `topic0`  
3. 按 `block_time` 的 UTC 日期聚合金额与条数  

不同平台索引与延迟不同，趋势与量级可比即可，不必强求逐笔一致。
