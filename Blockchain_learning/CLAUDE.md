# CLAUDE.md

本文件为 Claude Code（claude.ai/code）在此区块链学习项目中工作时提供指引。

## 项目背景

本项目是一个区块链链上数据分析入门学习项目，目标是通过动手实践掌握以太坊链上数据的获取、解析与分析。
最终产出一个可展示的鲸鱼钱包追踪 Dashboard。

## 技术栈

- 数据获取：`web3.py` + Etherscan API + Alchemy RPC
- 数据处理：`pandas`
- 可视化：`streamlit` + `plotly`
- 环境管理：`.env` 存储 API keys（禁止硬编码）
- Python 版本：3.10+

## 项目结构（当前仓库 + 后续规划）

```
Blockchain_learning/
├── CLAUDE.md
├── README.md
├── config.py
├── analyzer.py                 # Week3：Pandas 聚合分析（已实现）
├── week1/ week2/ week3/        # 分周练习脚本
├── docs/                       # 学习文档（含 week3_data_analysis.md）
├── data/                       # 数据与 Week3 输出（data/week3/）
├── notebooks/                  # Jupyter 探索（含 week3 notebook）
├── tests/                      # pytest 测试（含 test_analyzer.py）
├── pytest.ini                  # pytest 配置（含 pythonpath=.，避免 import 问题）
├── realtime/                  # Week4 实时 USDC：fetcher + parser + config
└── dashboard.py                # Streamlit 实时看板入口
```

## 开发设置

### 1. 创建虚拟环境
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

典型的 `requirements.txt` 内容：
```
web3>=6.0.0
pandas>=2.0.0
streamlit>=1.28.0
plotly>=5.17.0
python-dotenv>=1.0.0
pytest>=7.4.0
black>=23.0.0
mypy>=1.0.0
```

### 3. 配置 API 密钥
在项目根目录创建 `.env` 文件（已加入 `.gitignore`），内容如下：
```
ALCHEMY_API_KEY=your_key_here
ETHERSCAN_API_KEY=your_key_here
ALCHEMY_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}
```

所有代码通过 `config.py` 读取配置，禁止直接访问 `.env`。

## 常用开发命令

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_analyzer.py

# 运行单个测试用例
pytest tests/test_analyzer.py::test_daily_volume_and_tx_count

# 带覆盖率报告
pytest --cov=.
```

### 代码格式化与检查
```bash
# 使用 black 格式化代码
black .

# 使用 mypy 进行类型检查
mypy .

# 使用 flake8 进行代码风格检查（可选）
flake8 .
```

### 启动 Streamlit Dashboard
```bash
streamlit run dashboard.py
```

### 运行 Jupyter Notebook
```bash
jupyter notebook notebooks/
```

### Week 3：链上 CSV 日度分析
```bash
# 依赖 Week 2 导出的 data/usdc_transfers_*.csv，输出至 data/week3/
python week3/week3_analysis.py --source csv

# 可选：实时模式（需 ALCHEMY_API_KEY）
python week3/week3_analysis.py --source realtime --blocks 100

# 分析模块单测（项目已提供 pytest.ini；若仍冲突：PYTEST_DISABLE_PLUGIN_AUTOLOAD=1）
pytest tests/test_analyzer.py
```

学习文档：`docs/week3_data_analysis.md`。核心模块：`analyzer.py`。

## 项目架构说明

### 分层设计
1. **配置层（config.py）**：集中管理所有环境变量和 API 端点。
2. **数据获取层（fetcher.py）**：封装 Web3.py 和 Etherscan API 调用，负责拉取区块、交易、事件日志等原始数据。
3. **数据解析层（parser.py）**：将原始数据（如 wei 金额、十六进制日志）转换为可读的 Python 对象（Decimal、datetime 等）。
4. **分析层（analyzer.py）**：使用 pandas 进行聚合、统计、时间序列分析。
5. **可视化层（dashboard.py）**：Streamlit 应用，提供交互式图表和表格。

### 数据流
```
区块链网络 → fetcher → 原始数据 → parser → 清洗后数据 → analyzer → 分析结果 → dashboard → 图表
```

### 单元测试
每个模块应有对应的测试文件，放在 `tests/` 目录下：
- `tests/test_fetcher.py`
- `tests/test_parser.py`
- `tests/test_analyzer.py`
- `tests/test_config.py`

测试应使用 pytest，并尽量使用真实网络调用（注意速率限制）或适当的模拟（mock）。

## 学习计划（四周）

### Week 1：区块链数据基础
- 掌握 Block / Transaction / Receipt / Address 基本概念
- 练习 1：查询最新区块信息
- 练习 2：解析指定交易详情
- 练习 3：拉取地址历史交易 → 存 CSV

### Week 2：合约事件解析
- 理解 ABI、Event Log、Topic 结构
- 练习 1：解析 USDC Transfer 事件
- 练习 2：批量抓取事件 → DataFrame
- 练习 3：统计地址收发 USDC 总量

### Week 3：数据分析实战
- Pandas 链上数据聚合分析套路
- 练习：USDC 每日转账量时间序列分析（`analyzer.py` + `week3/week3_analysis.py` + `notebooks/week3_usdc_daily_analysis.ipynb`）
- 并行能力（可选）：Dune Analytics SQL（`ethereum.logs`）对照同口径指标

### Week 4：整合项目
- 完成 Streamlit Dashboard 全部功能
- 输入地址 → 展示余额、持仓、交易历史、事件时间线
- 发布到 GitHub

## 编码规范（请 Claude Code 遵守）

1. **中文注释**：所有代码加中文注释，便于学习理解。
2. **函数文档字符串**：每个函数必须有 docstring，说明参数和返回值。
3. **API 密钥安全**：API keys 只通过 `config.py` 读取，禁止在其他文件中直接访问 .env。
4. **错误处理**：网络请求统一加错误处理和 rate limit 保护。
5. **数据单位**：ETH 用 `Decimal` 类型，wei 转换在 parser.py 统一处理。
6. **探索性开发**：新功能先写在 notebooks/ 探索，验证后再重构到对应模块。

## 学习重点提示

- 遇到不理解的概念，Claude Code 请主动解释原理，不只给代码。
- 优先使用最简单直观的实现，而非过度封装。
- 每个练习完成后，提示下一步可以探索什么。

## 注意事项

- 已实现：`config.py`、`week1/`、`week2/`、`analyzer.py`、`week3/`、`tests/test_analyzer.py`、`notebooks/week3_usdc_daily_analysis.ipynb` 等；后续周继续按架构扩展 `fetcher.py` / `parser.py` / `dashboard.py`。
- 若添加新的依赖或工具，请同步更新 `requirements.txt` 和本文件的“常用开发命令”部分。