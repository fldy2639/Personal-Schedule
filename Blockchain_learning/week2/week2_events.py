#!/usr/bin/env python3
"""
Week 2：合约事件解析练习

练习1：解析USDC Transfer事件
练习2：批量抓取事件 → DataFrame
练习3：统计地址收发USDC总量

学习目标：
1. 理解智能合约事件的结构和原理
2. 掌握使用Web3.py解析事件日志
3. 学习批量获取事件并转换为DataFrame
4. 掌握基于事件的数据分析方法

运行前请确保：
1. 已配置 .env 文件（练习 1 至少需 ALCHEMY_API_KEY；ETHERSCAN_API_KEY 可选）
2. 已安装依赖：pip install web3 python-dotenv requests pandas
3. 了解USDC代币的基本知识（ERC-20标准，6位小数）

非交互运行练习 1：
  python week2/week2_events.py --practice1 0x你的交易哈希
"""

import argparse
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# 从子目录运行本脚本时，确保能导入项目根目录的 config
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv
import pandas as pd
from web3 import Web3
import requests

# 导入项目配置模块
try:
    from config import (
        get_etherscan_api_key,
        get_alchemy_api_key,
        get_alchemy_rpc_url,
        get_etherscan_api_base_url,
        get_etherscan_api_params,
        mask_api_key,
        print_api_key_status
    )
    print("[信息] 使用项目配置模块")
except ImportError:
    print("[警告] 未找到config.py，使用直接读取.env的方式")
    load_dotenv()

    def get_etherscan_api_key():
        key = os.getenv("ETHERSCAN_API_KEY")
        if not key:
            print("[错误] 未配置ETHERSCAN_API_KEY")
            sys.exit(1)
        return key

    def get_alchemy_api_key():
        key = os.getenv("ALCHEMY_API_KEY")
        if not key:
            print("[错误] 未配置ALCHEMY_API_KEY")
            sys.exit(1)
        return key

    def get_alchemy_rpc_url():
        return f"https://eth-mainnet.g.alchemy.com/v2/{get_alchemy_api_key()}"

# ========== 常量定义 ==========

# USDC合约地址（以太坊主网）
USDC_CONTRACT_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

# USDC小数位数（ERC-20标准为6，不是常见的18）
USDC_DECIMALS = 6

# Transfer事件签名（keccak256("Transfer(address,address,uint256)"))
TRANSFER_EVENT_SIGNATURE = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# USDC合约ABI（简化的，只包含必要部分）
USDC_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

# ========== 辅助函数 ==========

def connect_to_ethereum():
    """连接以太坊网络"""
    rpc_url = get_alchemy_rpc_url()
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if w3.is_connected():
        print("[成功] 成功连接到以太坊网络")
        return w3
    else:
        print("[错误] 连接以太坊失败")
        return None

def create_usdc_contract(w3):
    """创建USDC合约对象"""
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(USDC_CONTRACT_ADDRESS),
        abi=USDC_ABI
    )
    return contract

def usdc_to_human(value_raw):
    """将原始USDC值转换为可读金额"""
    return value_raw / (10 ** USDC_DECIMALS)

def human_to_usdc(value_human):
    """将可读金额转换为原始USDC值"""
    return int(value_human * (10 ** USDC_DECIMALS))

def get_example_transaction_hashes():
    """返回包含 USDC 转账的示例交易哈希（主网真实交易，便于对照 Etherscan）。"""
    return [
        {
            "hash": "0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060",
            "desc": "Uniswap 相关交易（含 USDC Transfer）",
        },
        {
            "hash": "0xf6ced6681638ee17931c965fd79eed66cae74148eb8aec656251906d3505f253",
            "desc": "普通链上转账（含 USDC）",
        },
    ]

# ========== 练习1：解析USDC Transfer事件 ==========

def practice1_parse_usdc_transfer(w3, contract, tx_hash):
    """
    练习1：解析USDC Transfer事件

    目标：从交易收据中解析USDC Transfer事件
    学习点：事件ABI、参数解析、单位转换
    """
    print("\n" + "="*70)
    print("练习1：解析USDC Transfer事件")
    print("="*70)

    try:
        # 获取交易收据
        print(f"正在查询交易: {tx_hash}")
        receipt = w3.eth.get_transaction_receipt(tx_hash)

        if not receipt:
            print("[错误] 未找到交易收据")
            return False

        print(f"[成功] 获取到交易收据，区块: {receipt['blockNumber']}")
        print(f"[信息] 事件日志数量: {len(receipt['logs'])}")

        # 查找USDC Transfer事件（统一规范化topic0后再比较，避免不同节点返回格式差异）
        usdc_transfers = []
        expected_topic0 = TRANSFER_EVENT_SIGNATURE.lower()
        for i, log in enumerate(receipt['logs']):
            # 检查日志是否来自USDC合约
            if log['address'].lower() == USDC_CONTRACT_ADDRESS.lower():
                # 检查是否是Transfer事件（检查第一个topic）
                topic0_hex = ""
                if log.get("topics"):
                    topic0_hex = Web3.to_hex(log["topics"][0]).lower()
                if topic0_hex == expected_topic0:
                    usdc_transfers.append((i, log))

        if not usdc_transfers:
            print("[信息] 未找到USDC Transfer事件")

            # 显示所有日志的来源，帮助调试
            print("\n[调试] 交易中的事件日志：")
            for i, log in enumerate(receipt['logs']):
                topic0_preview = Web3.to_hex(log["topics"][0]) if log.get("topics") else "无topic0"
                print(
                    f"  日志 {i}: 合约 {log['address'][:20]}..., 主题数: {len(log['topics'])}, "
                    f"topic0: {topic0_preview}"
                )

            return False

        print(f"[成功] 找到 {len(usdc_transfers)} 个USDC Transfer事件")

        # 解析每个USDC Transfer事件
        for log_index, raw_log in usdc_transfers:
            try:
                # 使用合约事件对象解析日志
                parsed_log = contract.events.Transfer().process_log(raw_log)
                args = parsed_log['args']

                print(f"\n📄 USDC Transfer事件 #{log_index}")
                print("-" * 40)
                print(f"发送方: {args['from']}")
                print(f"接收方: {args['to']}")
                print(f"原始金额: {args['value']:,}")
                print(f"USDC金额: {usdc_to_human(args['value']):,.2f} USDC")
                print(f"区块: {parsed_log['blockNumber']}")
                print(f"交易哈希: {parsed_log['transactionHash'].hex()}")

                # 显示原始日志详情（学习用）
                print(f"\n[学习] 原始日志详情:")
                print(f"  事件签名: {raw_log['topics'][0].hex()}")
                print(f"  主题数量: {len(raw_log['topics'])}")
                print(f"  数据长度: {len(raw_log['data'])} 字节")

            except Exception as e:
                print(f"[错误] 解析日志失败: {e}")
                continue

        # 学习总结
        print("\n✅ 练习1完成！")
        print("[学习] 掌握要点：")
        print("1. 通过合约地址和事件签名识别特定事件")
        print("2. 使用合约事件对象解析日志参数")
        print("3. 进行单位转换（原始值 → USDC）")
        print("4. 理解事件在交易收据中的存储方式")

        return True

    except Exception as e:
        print(f"[错误] 练习1执行失败: {e}")
        return False

# ========== 练习2：批量抓取事件 → DataFrame ==========

def practice2_batch_fetch_events(w3, contract):
    """
    练习2：批量抓取事件 → DataFrame

    目标：批量获取USDC Transfer事件并转换为DataFrame
    学习点：事件过滤、批量查询、数据转换
    """
    print("\n" + "="*70)
    print("练习2：批量抓取USDC Transfer事件 → DataFrame")
    print("="*70)

    try:
        # 获取当前区块号
        latest_block = w3.eth.block_number
        print(f"[信息] 当前最新区块: {latest_block:,}")

        # 设置查询范围（最近100个区块）
        end_block = latest_block
        start_block = max(0, end_block - 100)  # 最近100个区块

        print(f"[信息] 查询范围: 区块 {start_block:,} - {end_block:,}")
        print(f"[信息] 查询范围大小: {end_block - start_block + 1} 个区块")

        # 直接使用 eth_getLogs 查询，并分块拉取以兼容免费套餐的区块范围限制
        print("[信息] 通过 eth_getLogs 分块获取事件日志...")
        chunk_size = 10
        raw_logs = []
        for chunk_start in range(start_block, end_block + 1, chunk_size):
            chunk_end = min(chunk_start + chunk_size - 1, end_block)
            print(f"  查询区块 {chunk_start:,} - {chunk_end:,}")
            batch_logs = w3.eth.get_logs({
                "fromBlock": chunk_start,
                "toBlock": chunk_end,
                "address": Web3.to_checksum_address(USDC_CONTRACT_ADDRESS),
                "topics": [TRANSFER_EVENT_SIGNATURE],
            })
            raw_logs.extend(batch_logs)
            time.sleep(0.05)

        # 使用 ABI 解析原始日志，得到统一结构
        events = []
        for raw_log in raw_logs:
            events.append(contract.events.Transfer().process_log(raw_log))

        if not events:
            print("[信息] 指定范围内未找到USDC Transfer事件")
            return None

        print(f"[成功] 找到 {len(events)} 个USDC Transfer事件")

        # 转换为DataFrame
        print("[信息] 转换为DataFrame...")
        data = []

        for event in events:
            args = event['args']
            data.append({
                'transaction_hash': event['transactionHash'].hex(),
                'block_number': event['blockNumber'],
                'log_index': event['logIndex'],
                'from': args['from'],
                'to': args['to'],
                'value_raw': args['value'],
                'value_usdc': usdc_to_human(args['value']),
                'timestamp': None  # 稍后添加
            })

        df = pd.DataFrame(data)

        # 添加时间戳信息
        print("[信息] 添加时间戳信息...")
        timestamps = {}

        # 获取所有区块的时间戳（去重）
        unique_blocks = df['block_number'].unique()
        print(f"[信息] 需要查询 {len(unique_blocks)} 个区块的时间戳")

        for i, block_num in enumerate(unique_blocks):
            if i > 0 and i % 10 == 0:
                print(f"  已查询 {i}/{len(unique_blocks)} 个区块")

            block = w3.eth.get_block(int(block_num))
            timestamps[block_num] = block['timestamp']

            # 添加延迟，避免速率限制
            time.sleep(0.05)

        # 应用时间戳
        df['timestamp'] = df['block_number'].map(timestamps)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')

        # 基本分析
        print("\n📊 批量数据统计")
        print("-" * 40)
        print(f"时间范围: {df['datetime'].min()} 到 {df['datetime'].max()}")
        print(f"总交易笔数: {len(df):,}")
        print(f"总转账金额: {df['value_usdc'].sum():,.2f} USDC")
        print(f"平均每笔金额: {df['value_usdc'].mean():,.2f} USDC")
        print(f"最大单笔转账: {df['value_usdc'].max():,.2f} USDC")

        # 保存为CSV
        filename = f"usdc_transfers_{int(time.time())}.csv"
        df.to_csv(f"data/{filename}", index=False)
        print(f"\n[保存] 数据已保存到: data/{filename}")
        print(f"      共 {len(df)} 行，{len(df.columns)} 列")

        # 显示前几行数据
        print("\n📋 数据预览（前5行）:")
        print(df.head().to_string())

        # 学习总结
        print("\n✅ 练习2完成！")
        print("[学习] 掌握要点：")
        print("1. 使用事件过滤器批量查询事件")
        print("2. 将事件数据转换为结构化DataFrame")
        print("3. 添加元数据（时间戳）")
        print("4. 数据基本统计和保存")

        return df

    except Exception as e:
        print(f"[错误] 练习2执行失败: {e}")
        import traceback
        traceback.print_exc()
        return None

# ========== 练习3：统计地址收发USDC总量 ==========

def practice3_analyze_address_activity(df, address):
    """
    练习3：统计地址收发USDC总量

    目标：分析指定地址的USDC活动模式
    学习点：数据筛选、聚合统计、模式分析
    """
    print("\n" + "="*70)
    print("练习3：统计地址收发USDC总量")
    print("="*70)

    if df is None or df.empty:
        print("[错误] 没有数据可供分析")
        return None

    print(f"[信息] 分析地址: {address}")

    try:
        # 标准化地址格式（小写）
        address = address.lower()

        # 筛选该地址相关的交易
        incoming = df[df['to'].str.lower() == address].copy()
        outgoing = df[df['from'].str.lower() == address].copy()

        print(f"\n📈 地址活动统计")
        print("-" * 40)
        print(f"接收交易数: {len(incoming):,}")
        print(f"发送交易数: {len(outgoing):,}")
        print(f"总交易数: {len(incoming) + len(outgoing):,}")

        print(f"\n💰 资金流动统计")
        print("-" * 40)
        total_received = incoming['value_usdc'].sum() if not incoming.empty else 0
        total_sent = outgoing['value_usdc'].sum() if not outgoing.empty else 0
        net_flow = total_received - total_sent

        print(f"总接收金额: {total_received:,.2f} USDC")
        print(f"总发送金额: {total_sent:,.2f} USDC")
        print(f"净流入: {net_flow:,.2f} USDC")

        if len(incoming) > 0:
            print(f"平均接收金额: {incoming['value_usdc'].mean():,.2f} USDC")
            print(f"最大接收金额: {incoming['value_usdc'].max():,.2f} USDC")

        if len(outgoing) > 0:
            print(f"平均发送金额: {outgoing['value_usdc'].mean():,.2f} USDC")
            print(f"最大发送金额: {outgoing['value_usdc'].max():,.2f} USDC")

        # 时间分析
        if not incoming.empty:
            print(f"\n📅 接收活动时间范围")
            print("-" * 40)
            print(f"首次接收: {incoming['datetime'].min()}")
            print(f"最后接收: {incoming['datetime'].max()}")

        if not outgoing.empty:
            print(f"\n📅 发送活动时间范围")
            print("-" * 40)
            print(f"首次发送: {outgoing['datetime'].min()}")
            print(f"最后发送: {outgoing['datetime'].max()}")

        # 交易频率分析
        if not incoming.empty:
            incoming['date'] = incoming['datetime'].dt.date
            daily_in = incoming.groupby('date').size()
            print(f"\n📊 接收频率: 平均每天 {daily_in.mean():.1f} 笔交易")

        if not outgoing.empty:
            outgoing['date'] = outgoing['datetime'].dt.date
            daily_out = outgoing.groupby('date').size()
            print(f"📊 发送频率: 平均每天 {daily_out.mean():.1f} 笔交易")

        # 交易对手分析
        if not incoming.empty:
            top_senders = incoming['from'].value_counts().head(3)
            print(f"\n🤝 主要发送方（前3）:")
            for addr, count in top_senders.items():
                print(f"  {addr[:20]}...: {count} 笔交易")

        if not outgoing.empty:
            top_receivers = outgoing['to'].value_counts().head(3)
            print(f"\n🤝 主要接收方（前3）:")
            for addr, count in top_receivers.items():
                print(f"  {addr[:20]}...: {count} 笔交易")

        # 金额分布分析
        print(f"\n📋 交易金额分布")
        print("-" * 40)

        # 定义金额区间
        bins = [0, 100, 1000, 10000, 100000, float('inf')]
        labels = ['<100', '100-1k', '1k-10k', '10k-100k', '>100k']

        if not incoming.empty:
            incoming['amount_range'] = pd.cut(incoming['value_usdc'], bins=bins, labels=labels)
            range_counts = incoming['amount_range'].value_counts().sort_index()
            print("接收金额分布:")
            for rng, count in range_counts.items():
                print(f"  {rng} USDC: {count} 笔交易")

        if not outgoing.empty:
            outgoing['amount_range'] = pd.cut(outgoing['value_usdc'], bins=bins, labels=labels)
            range_counts = outgoing['amount_range'].value_counts().sort_index()
            print("发送金额分布:")
            for rng, count in range_counts.items():
                print(f"  {rng} USDC: {count} 笔交易")

        # 学习总结
        print("\n✅ 练习3完成！")
        print("[学习] 掌握要点：")
        print("1. 基于地址筛选交易数据")
        print("2. 资金流动统计和净流量计算")
        print("3. 时间模式和频率分析")
        print("4. 交易对手和金额分布分析")

        # 返回统计结果
        stats = {
            'address': address,
            'total_received': total_received,
            'total_sent': total_sent,
            'net_flow': net_flow,
            'tx_count_in': len(incoming),
            'tx_count_out': len(outgoing),
            'avg_incoming': incoming['value_usdc'].mean() if not incoming.empty else 0,
            'avg_outgoing': outgoing['value_usdc'].mean() if not outgoing.empty else 0
        }

        return stats

    except Exception as e:
        print(f"[错误] 练习3执行失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_realtime_example_addresses(df, top_n=3):
    """
    从当前查询到的 DataFrame 中提取高频地址，作为练习3示例地址。

    参数:
        df (pd.DataFrame): 练习2生成的USDC事件数据
        top_n (int): 需要返回的示例地址数量

    返回:
        list[str]: 示例地址列表
    """
    fallback_examples = [
        "0x28C6c06298d514Db089934071355E5743bf21d60",  # Binance热钱包
        "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # Uniswap Router
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
    ]

    if df is None or df.empty:
        return fallback_examples[:top_n]

    # 统计 from/to 出现频次，优先选择在当前窗口中活跃的地址用于演示
    address_series = pd.concat([df["from"], df["to"]], ignore_index=True).dropna()
    top_addresses = address_series.value_counts().head(top_n).index.tolist()

    # 若实时地址不足，使用默认地址补齐，保证交互选项完整
    for addr in fallback_examples:
        if len(top_addresses) >= top_n:
            break
        if addr not in top_addresses:
            top_addresses.append(addr)

    return top_addresses[:top_n]

# ========== 主函数 ==========

def parse_cli_args(argv=None):
    """
    解析命令行参数。

    参数:
        argv: 可选，默认使用 sys.argv[1:]（供测试注入）。

    返回:
        argparse.Namespace: 解析结果，含 practice1 等字段。
    """
    parser = argparse.ArgumentParser(
        description="Week 2：合约事件解析（USDC Transfer 等）"
    )
    parser.add_argument(
        "--practice1",
        metavar="TX_HASH",
        help="非交互：直接运行练习 1，并解析该交易哈希中的 USDC Transfer",
    )
    return parser.parse_args(argv)


def main():
    """主函数：执行Week 2练习"""
    # Windows 控制台默认 GBK 时，避免打印 emoji 等字符报错
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    args = parse_cli_args()

    # 非交互：仅练习 1
    if args.practice1:
        print("🔍 Week 2：合约事件解析练习（--practice1）")
        print("=" * 70)
        print_api_key_status()
        w3 = connect_to_ethereum()
        if not w3:
            sys.exit(1)
        contract = create_usdc_contract(w3)
        print(f"[成功] 创建USDC合约对象，地址: {USDC_CONTRACT_ADDRESS[:20]}...")
        try:
            decimals = contract.functions.decimals().call()
            print(f"[信息] USDC小数位: {decimals} (应与常量 {USDC_DECIMALS} 一致)")
            if decimals != USDC_DECIMALS:
                print("[警告] USDC小数位与常量不一致，请更新USDC_DECIMALS")
        except Exception:
            print("[信息] 无法获取USDC小数位，使用预设值")
        ok = practice1_parse_usdc_transfer(w3, contract, args.practice1.strip())
        sys.exit(0 if ok else 1)

    print("🔍 Week 2：合约事件解析练习")
    print("="*70)

    print_api_key_status()

    # 连接以太坊
    w3 = connect_to_ethereum()
    if not w3:
        sys.exit(1)

    # 创建USDC合约对象
    contract = create_usdc_contract(w3)
    print(f"[成功] 创建USDC合约对象，地址: {USDC_CONTRACT_ADDRESS[:20]}...")

    # 获取USDC小数位（验证）
    try:
        decimals = contract.functions.decimals().call()
        print(f"[信息] USDC小数位: {decimals} (应与常量 {USDC_DECIMALS} 一致)")
        if decimals != USDC_DECIMALS:
            print("[警告] USDC小数位与常量不一致，请更新USDC_DECIMALS")
    except:
        print("[信息] 无法获取USDC小数位，使用预设值")

    # 选择要执行的练习
    print("\n请选择要执行的练习：")
    print("1. 练习1：解析USDC Transfer事件")
    print("2. 练习2：批量抓取事件 → DataFrame")
    print("3. 练习3：统计地址收发USDC总量")
    print("4. 全部执行（按顺序1→2→3）")

    choice = input("\n请选择 (1-4): ").strip()

    df = None  # 用于存储练习2的数据，供练习3使用

    # 练习1：解析USDC Transfer事件
    if choice in ['1', '4']:
        print("\n📋 练习1：需要提供一个包含USDC转账的交易哈希")
        print("示例交易哈希：")
        examples = get_example_transaction_hashes()
        for i, ex in enumerate(examples, 1):
            print(f"{i}. {ex['desc']}: {ex['hash']}")

        tx_hash = input("\n请输入交易哈希（直接输入哈希或选择 1-2；也可命令行 --practice1 0x...）: ").strip()

        # 如果输入的是数字，使用对应示例
        if tx_hash in ["1", "2"]:
            idx = int(tx_hash) - 1
            tx_hash = examples[idx]["hash"]
            print(f"使用示例: {examples[idx]['desc']}")
            print(f"交易哈希: {tx_hash}")

        practice1_parse_usdc_transfer(w3, contract, tx_hash)

    # 练习2：批量抓取事件 → DataFrame
    if choice in ['2', '4']:
        if choice == '4':
            input("\n按回车键继续练习2...")

        df = practice2_batch_fetch_events(w3, contract)

    # 练习3：统计地址收发USDC总量
    if choice in ['3', '4']:
        if choice == '4':
            input("\n按回车键继续练习3...")

        if df is None and choice == '3':
            # 如果直接选择练习3，需要先获取数据
            print("[信息] 需要先获取数据进行分析...")
            df = practice2_batch_fetch_events(w3, contract)

        if df is not None and not df.empty:
            print("\n📋 练习3：选择一个地址进行分析")
            print("示例地址（基于当前数据实时生成）：")
            examples = get_realtime_example_addresses(df, top_n=3)

            for i, addr in enumerate(examples, 1):
                print(f"{i}. {addr}")

            addr_choice = input("\n请输入地址或选择1-3: ").strip()

            if addr_choice in ['1', '2', '3']:
                idx = int(addr_choice) - 1
                address = examples[idx]
            else:
                address = addr_choice

            practice3_analyze_address_activity(df, address)
        else:
            print("[错误] 没有可用数据进行分析")

    # 学习总结
    print("\n" + "="*70)
    print("✅ Week 2 学习完成！")
    print("\n📚 学习总结：")
    print("1. 掌握了智能合约事件的基本概念和结构")
    print("2. 学会了使用Web3.py解析事件日志")
    print("3. 掌握了批量获取事件并转换为DataFrame的方法")
    print("4. 学会了基于事件进行地址活动分析")

    print("\n💡 下一步建议：")
    print("- 尝试分析其他ERC-20代币（如DAI、UNI）")
    print("- 探索复杂事件（包含结构体、数组）")
    print("- 实现实时事件监听（WebSocket）")
    print("- 构建交易关系网络图")
    print("="*70)

if __name__ == "__main__":
    # 确保data目录存在
    os.makedirs("data", exist_ok=True)

    # 检查pandas是否已安装
    try:
        import pandas as pd
    except ImportError:
        print("[错误] 未安装pandas，请运行: pip install pandas")
        print("或分阶段安装: pip install web3 python-dotenv requests pandas")
        sys.exit(1)

    main()