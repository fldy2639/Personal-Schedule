# 区块链链上数据分析学习项目

> 通过动手实践掌握以太坊链上数据的获取、解析与分析，最终产出一个可展示的鲸鱼钱包追踪 Dashboard。

## 🎯 项目目标

- **掌握基础**: 区块链数据获取、解析、分析全流程
- **实战练习**: 每周一个主题，从易到难逐步深入
- **产出导向**: 最终完成一个功能完整的鲸鱼钱包追踪 Dashboard
- **安全规范**: 遵循API密钥管理、编码规范等最佳实践

## 📁 项目结构

```
Blockchain_learning/
├── CLAUDE.md                    # Claude Code项目指导文件
├── README.md                    # 本文件
├── .env                         # API密钥配置（不提交git）
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git忽略文件
├── requirements.txt             # Python依赖包列表
├── pytest.ini                   # pytest 配置（避免第三方插件冲突）
├── config.py                    # 统一配置管理模块
├── analyzer.py                  # Week3：Pandas 聚合分析（可复用函数）
├── realtime/                    # Week4：实时 USDC 拉取与解析（子包）
│   ├── config.py                # USDC 合约与 topic0 等常量
│   ├── fetcher.py               # eth_getLogs 分块拉取
│   └── parser.py                # 日志 → DataFrame
├── dashboard.py                 # Week4：Streamlit 多 Tab 实时看板入口
├── data/                        # 数据文件目录（本地生成，默认不提交）
│   ├── transactions_*.csv       # 交易历史数据
│   ├── usdc_transfers_*.csv     # USDC转账事件数据（Week2）
│   └── week3/                   # Week3 分析输出（日度 CSV、地址 JSON、可选 Plotly HTML）
├── docs/                        # 学习文档
│   ├── week1_blockchain_basics.md
│   ├── week2_contract_events.md
│   └── week3_data_analysis.md
├── week1/                       # 第一周：区块链数据基础
│   ├── __init__.py
│   ├── block_info.py           # 练习1：查询最新区块信息
│   ├── transaction_parser.py   # 练习2：解析指定交易详情
│   ├── address_history.py      # 练习3：拉取地址历史交易
│   └── results1.md             # 练习结果记录
├── week2/                       # 第二周：合约事件解析
│   ├── __init__.py
│   └── week2_events.py         # 三个练习：USDC事件解析
├── week3/                       # 第三周：数据分析实战
│   ├── __init__.py
│   └── week3_analysis.py       # CSV / 实时模式日度聚合与地址统计
├── notebooks/                   # Jupyter探索性分析
│   └── week3_usdc_daily_analysis.ipynb
└── tests/                       # 单元测试
    ├── test_analyzer.py
    └── test_parser.py
```

## 📚 学习计划（四周）

### Week 1：区块链数据基础 ✅
- **掌握概念**: Block / Transaction / Receipt / Address
- **练习1**: 查询最新区块信息 (`week1/block_info.py`)
- **练习2**: 解析指定交易详情 (`week1/transaction_parser.py`)
- **练习3**: 拉取地址历史交易 → CSV (`week1/address_history.py`)

### Week 2：合约事件解析 ✅
- **理解概念**: ABI、Event Log、Topic结构
- **练习1**: 解析USDC Transfer事件
- **练习2**: 批量抓取事件 → DataFrame
- **练习3**: 统计地址收发USDC总量
- **脚本**: `week2/week2_events.py`

### Week 3：数据分析实战 ✅
- **文档**: `docs/week3_data_analysis.md`
- **分析模块**: `analyzer.py`（`load_usdc_csv`、`ensure_datetime`、日度聚合、地址统计、导出）
- **练习脚本**: `week3/week3_analysis.py`（`--source csv` 读取 Week2 CSV；可选 `--source realtime`）
- **Notebook**: `notebooks/week3_usdc_daily_analysis.ipynb`
- **测试**: `pytest tests/test_analyzer.py`（项目已提供 `pytest.ini`；若仍冲突可设 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`）

### Week 4：整合项目（进行中）
- `realtime/`：统一实时拉取（`fetcher.py`）与解析（`parser.py`），常量集中在 `config.py`
- `dashboard.py`：多 Tab（概览/事件流/时间序列/地址分析）实时看板入口
- 下一步：补充更完整的异常处理、交互优化与更多链上指标

## 🚀 快速开始

### 1. 环境配置
```bash
# 创建虚拟环境
python -m venv venv

# Windows激活
venv\Scripts\activate

# macOS/Linux激活
source venv/bin/activate

# 安装依赖（可按周分阶段安装）
pip install -r requirements.txt
```

### 2. API密钥配置
1. 复制 `.env.example` 为 `.env`
2. 获取并填入API密钥：
   - **Alchemy API**: https://www.alchemy.com/
   - **Etherscan API**: https://etherscan.io/apis
3. **重要**: 将 `.env` 加入 `.gitignore`，不要提交密钥

### 3. 运行练习

**Week 1 练习**:
```bash
# 在项目根目录运行
cd week1
python block_info.py          # 练习1
python transaction_parser.py  # 练习2  
python address_history.py     # 练习3
```

**Week 2 练习**:
```bash
cd week2
python week2_events.py        # 包含三个练习
```

**Week 3 练习**（在项目根目录 `Blockchain_learning/`）:
```bash
# 使用 data/ 下最新 usdc_transfers_*.csv 生成日度统计 → data/week3/
python week3/week3_analysis.py --source csv

# 指定 CSV 或地址
python week3/week3_analysis.py --source csv --csv-path data/usdc_transfers_xxx.csv --address 0x你的地址

# 可选：实时拉取最近 N 个区块的 USDC 日志（需配置 ALCHEMY_API_KEY）
python week3/week3_analysis.py --source realtime --blocks 100

# 单元测试
pytest tests/test_analyzer.py

# Notebook（需安装 jupyter）
jupyter notebook notebooks/week3_usdc_daily_analysis.ipynb
```

**Week 4 Dashboard**（在项目根目录 `Blockchain_learning/`）:
```bash
# 启动实时 USDC 多 Tab Dashboard
streamlit run dashboard.py
```

Dashboard 参数说明（侧边栏）：
- `目标地址`：用于地址分析页签，留空则仅看全局指标
- `覆盖区块数`：从结束区块向前抓取的区块跨度
- `分块查询大小`：单次 RPC 查询区块数，建议小值避免速率限制
- `结束区块`：默认最新区块，可回看历史窗口

## 🔧 技术栈

- **数据获取**: `web3.py` + Etherscan API + Alchemy RPC
- **数据处理**: `pandas`
- **可视化**: `streamlit` + `plotly`（第四周引入）
- **环境管理**: `.env` + `python-dotenv`
- **Python版本**: 3.10+

## 📖 学习资源

1. **项目文档**: `docs/` 目录下的周学习文档
2. **代码注释**: 所有脚本都有详细的中文注释
3. **CLAUDE.md**: Claude Code工作指引
4. **在线资源**:
   - [Web3.py文档](https://web3py.readthedocs.io/)
   - [Etherscan API文档](https://docs.etherscan.io/)
   - [Alchemy文档](https://docs.alchemy.com/)

## ⚠️ 注意事项

### 安全规范
- ✅ **禁止硬编码API密钥**：所有密钥通过 `config.py` 读取
- ✅ **使用环境变量**：`.env` 文件管理敏感信息
- ✅ **版本控制**：`.gitignore` 已配置，避免提交敏感文件

### API限制
- **Etherscan免费版**: 每天10万次调用，添加请求间隔避免超限
- **Alchemy免费版**: 每天3亿计算单元，足够学习使用
- **网络请求**: 添加适当延迟，处理超时和重试

### 编码规范
- **中文注释**: 所有代码添加中文注释便于学习
- **函数文档**: 每个函数有docstring说明参数和返回值
- **错误处理**: 统一错误处理和用户友好提示
- **代码格式化**: 使用black保持代码风格统一

## 🔍 问题排查

### 常见问题
1. **连接失败**: 检查API密钥、网络连接、RPC URL格式
2. **导入错误**: 确保在正确目录运行，依赖包已安装
3. **数据为空**: 确认地址/交易哈希正确，交易已确认
4. **编码问题**: Windows控制台可能遇到Unicode错误，脚本已做兼容处理

### 调试建议
- 查看 `config.py` 中的API密钥状态检查
- 使用脚本的调试输出模式
- 检查 `.env` 文件格式和位置
- 在Etherscan网站手动验证API请求

## 🤝 贡献与反馈

本项目为学习项目，欢迎：
1. **提出问题**: 遇到bug或疑问可记录在issues
2. **改进建议**: 对代码结构、学习内容提出建议
3. **扩展功能**: 在完成基础练习后尝试扩展功能

---

**学习提示**: 区块链开发最好的方式是动手实践。遇到问题时，先尝试理解错误信息，再查看文档，最后搜索解决方案。每个错误都是学习的机会！

**更新日期**: 2026-04-10