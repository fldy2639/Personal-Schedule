# Week 1：区块链数据基础

## 1. 核心概念解析

### 1.1 区块（Block）

区块是区块链的基本单位，就像一个存储交易的数字容器。每个区块包含：

- **区块头（Header）**：包含元数据，如区块高度、时间戳、前一区块哈希等
- **区块体（Body）**：包含该区块打包的所有交易

**关键字段**：
- `区块高度（Block Number）`：区块在链上的位置，从0开始计数
- `时间戳（Timestamp）`：区块被挖出的时间（Unix时间戳）
- `矿工地址（Miner）`：成功挖出该区块的矿工地址
- `Gas限制（Gas Limit）`：区块允许的最大Gas总量
- `Gas使用量（Gas Used）`：区块实际使用的Gas总量
- `难度值（Difficulty）`：挖出该区块的计算难度
- `交易列表（Transactions）`：该区块包含的交易哈希列表

```python
# 示例：获取区块信息的基本代码
from web3 import Web3

# 连接以太坊节点
w3 = Web3(Web3.HTTPProvider('你的RPC_URL'))

# 获取最新区块号
latest_block = w3.eth.block_number
print(f"最新区块号: {latest_block}")

# 获取区块详情
block = w3.eth.get_block(latest_block)
print(f"区块哈希: {block['hash'].hex()}")
print(f"交易数量: {len(block['transactions'])}")
```

### 1.2 交易（Transaction）

交易是账户之间的状态转移，可以是普通转账或合约调用。

**交易结构**：
- `from`：发送方地址
- `to`：接收方地址（如果是合约创建交易，则为None）
- `value`：转账金额（单位：wei）
- `gasPrice`：Gas价格（单位：wei）
- `gas`：Gas限制（愿意支付的最大Gas量）
- `nonce`：交易序号，防止重放攻击
- `data`：调用合约时的输入数据（普通转账为空）

**交易生命周期**：
1. **创建**：用户创建交易并签名
2. **广播**：将交易发送到网络
3. **打包**：矿工将交易打包进区块
4. **确认**：区块被网络确认

```python
# 示例：获取交易信息
tx_hash = "0x..."  # 交易哈希
transaction = w3.eth.get_transaction(tx_hash)

print(f"发送方: {transaction['from']}")
print(f"接收方: {transaction['to']}")
print(f"转账金额: {w3.from_wei(transaction['value'], 'ether')} ETH")
```

### 1.3 交易收据（Transaction Receipt）

交易收据记录了交易执行的结果，不同于交易本身（交易是"意图"，收据是"结果"）。

**收据结构**：
- `status`：交易执行状态（1=成功，0=失败）
- `gasUsed`：实际使用的Gas量
- `logs`：事件日志数组
- `contractAddress`：如果是合约创建交易，这里显示新合约地址

**事件日志（Event Logs）**：
智能合约可以通过事件（Event）向外发送消息，这些消息被记录在日志中。每个日志包含：
- `address`：发出事件的合约地址
- `topics`：事件签名哈希和索引参数
- `data`：非索引参数

```python
# 示例：获取交易收据
receipt = w3.eth.get_transaction_receipt(tx_hash)

print(f"交易状态: {'成功' if receipt['status'] == 1 else '失败'}")
print(f"Gas使用量: {receipt['gasUsed']}")
print(f"事件日志数量: {len(receipt['logs'])}")
```

### 1.4 地址（Address）

以太坊地址是账户的唯一标识符，格式为`0x`开头的40个十六进制字符。

**地址类型**：
1. **外部账户地址（EOA）**：由私钥控制，可以主动发起交易
2. **合约地址**：由合约代码控制，只能被动响应交易调用

**地址生成**：
```
私钥 → 公钥 → Keccak-256哈希 → 取后20字节 → 0x前缀 → 地址
```

**地址功能**：
- 存储ETH余额
- 存储代币余额（通过合约记录）
- 接收和发送交易

```python
# 示例：查询地址余额
address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Vitalik Buterin的地址
balance = w3.eth.get_balance(address)
print(f"地址余额: {w3.from_wei(balance, 'ether')} ETH")
```

## 2. Web3.py 基础

### 2.1 Web3.py 是什么

Web3.py是Python的以太坊交互库，它：
- 提供JSON-RPC和WebSocket连接
- 封装了底层协议细节
- 提供高层API便于开发者使用

### 2.2 核心对象

- **Web3实例**：连接以太坊节点的入口
- **Account**：私钥管理和交易签名
- **Contract**：智能合约交互
- **Filter**：事件监听和过滤

### 2.3 常用方法

```python
# 连接以太坊
w3 = Web3(Web3.HTTPProvider('https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY'))

# 检查连接
if w3.is_connected():
    print("连接成功")
else:
    print("连接失败")

# 常用查询方法
latest_block = w3.eth.block_number  # 最新区块号
gas_price = w3.eth.gas_price        # 当前Gas价格
chain_id = w3.eth.chain_id          # 链ID（1=主网）
```

## 3. 数据单位转换

### 3.1 ETH单位体系

以太坊使用多级单位体系，最小单位是wei：

| 单位 | 值（wei） | 用途 |
|------|-----------|------|
| wei | 1 | 最小单位，智能合约内部使用 |
| gwei | 1,000,000,000 | Gas价格常用单位 |
| ether | 1,000,000,000,000,000,000 | 用户常用显示单位 |

### 3.2 Web3.py转换函数

```python
from web3 import Web3

# 创建Web3实例（不连接节点也可用于单位转换）
w3 = Web3()

# 其他单位转换为wei
value_in_wei = w3.to_wei(1, 'ether')      # 1 ETH = 10^18 wei
gas_in_wei = w3.to_wei(30, 'gwei')        # 30 Gwei = 30×10^9 wei

# wei转换为其他单位
value_in_eth = w3.from_wei(value_in_wei, 'ether')
gas_in_gwei = w3.from_wei(gas_in_wei, 'gwei')

print(f"1 ETH = {value_in_wei} wei")
print(f"30 Gwei = {gas_in_gwei} Gwei")
```

## 4. API服务介绍

### 4.1 Alchemy RPC

**功能**：提供稳定的以太坊节点连接
**优势**：
- 高可用性（99.9% SLA）
- WebSocket支持（实时数据）
- 开发者工具和监控
- 免费层足够学习使用

**使用方式**：
```python
# 通过RPC URL连接
w3 = Web3(Web3.HTTPProvider('https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY'))
```

**获取API密钥**：
1. 访问 https://www.alchemy.com/
2. 注册账号
3. 创建应用，选择Ethereum主网
4. 获取API密钥

### 4.2 Etherscan API

**功能**：提供链上数据查询服务
**优势**：
- 历史数据查询（交易列表、内部交易等）
- 合约验证和源代码查看
- 丰富的统计数据

**常用端点**：
- `account/txlist`：获取地址交易列表
- `account/balance`：获取地址余额
- `contract/getabi`：获取合约ABI

**使用方式**：
```python
import requests

api_key = "YOUR_ETHERSCAN_API_KEY"
address = "0x..."
url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&apikey={api_key}"

response = requests.get(url)
data = response.json()
```

**获取API密钥**：
1. 访问 https://etherscan.io/apis
2. 注册账号
3. 创建API密钥（免费版每天10万次调用）

## 5. 安全注意事项

### 5.1 API密钥管理

**错误做法**（不要这样）：
```python
# 硬编码API密钥（绝对禁止！）
API_KEY = "sk_live_1234567890abcdef"
```

**正确做法**：
1. 使用环境变量
2. 通过`.env`文件管理
3. 将`.env`加入`.gitignore`

```python
# .env文件内容
ALCHEMY_API_KEY=your_alchemy_key_here
ETHERSCAN_API_KEY=your_etherscan_key_here

# Python代码中读取
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("ALCHEMY_API_KEY")
```

### 5.2 速率限制

每个API服务都有调用限制：
- **Alchemy**：免费版每天3亿计算单元
- **Etherscan**：免费版每天10万次调用

**最佳实践**：
1. 添加请求间隔（避免短时间内大量调用）
2. 缓存重复查询结果
3. 监控API使用量

```python
import time

def safe_api_call():
    # 添加延迟，避免触发速率限制
    time.sleep(0.1)  # 100毫秒延迟
    # 执行API调用
    # ...
```

### 5.3 私钥安全

**学习环境**：
- 使用测试网（Goerli、Sepolia）
- 使用测试网ETH（通过水龙头获取）
- 不要使用主网私钥

**生产环境**：
- 使用硬件钱包
- 使用环境变量或密钥管理服务
- 定期轮换密钥

## 6. 第一周练习目标

### 练习1：查询最新区块信息
- 目标：掌握`w3.eth.get_block()`方法
- 学习点：区块结构、关键字段含义
- 输出：打印区块号、哈希、时间戳、交易数量

### 练习2：解析指定交易详情
- 目标：区分交易和交易收据
- 学习点：交易字段、单位转换、状态检查
- 输出：打印发送方、接收方、金额、Gas费用、交易状态

### 练习3：拉取地址历史交易
- 目标：使用Etherscan API批量获取数据
- 学习点：API调用、数据处理、CSV导出
- 输出：CSV文件，包含交易历史记录

## 7. 常见问题

### Q1: 为什么连接失败？
- 检查API密钥是否正确
- 检查网络连接
- 确认RPC URL格式正确

### Q2: 为什么查询返回空数据？
- 确认地址/交易哈希正确
- 检查区块号是否有效
- 确认交易是否已确认（可能需要等待）

### Q3: 如何选择合适的Gas价格？
- 使用`w3.eth.gas_price`获取当前市场价
- 对于普通转账，使用默认值即可
- 对于急需确认的交易，可以适当提高

### Q4: 什么是nonce？为什么重要？
- nonce是交易序号，从0开始递增
- 防止重放攻击（同一交易不能重复执行）
- 确保交易顺序执行

## 8. 下一步学习建议

完成第一周练习后，可以探索：
1. **智能合约交互**：调用合约方法、读取合约状态
2. **事件监听**：实时监控合约事件
3. **Gas优化**：分析Gas使用，优化交易成本
4. **批量处理**：同时处理多个地址或交易

---

**提示**：学习区块链开发最好的方式是动手实践。遇到问题时，先尝试理解错误信息，再查看文档，最后搜索解决方案。每个错误都是学习的机会！