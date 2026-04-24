#!/usr/bin/env python3
"""
练习1：查询最新区块信息

目标：掌握web3.eth.get_block()方法的使用，理解区块结构

学习点：
1. 连接以太坊节点
2. 获取区块信息
3. 理解区块关键字段含义
4. 处理API配置错误

运行前请确保：
1. 复制 .env.example 为 .env
2. 在 .env 中填入你的Alchemy API密钥
3. 安装依赖：pip install -r requirements.txt
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3

def check_api_config():
    """
    检查API配置是否完整
    如果不完整，提示用户如何配置
    """
    # 加载.env文件
    load_dotenv()

    # 检查必要的环境变量
    alchemy_api_key = os.getenv("ALCHEMY_API_KEY")

    if not alchemy_api_key:
        print("❌ 错误：缺少Alchemy API密钥配置")
        print("\n请按照以下步骤配置：")
        print("1. 复制 .env.example 为 .env")
        print("2. 在 .env 文件中填入你的Alchemy API密钥")
        print("3. Alchemy API密钥获取地址：https://www.alchemy.com/")
        print("\n示例 .env 文件内容：")
        print("ALCHEMY_API_KEY=your_alchemy_api_key_here")
        print("ETHERSCAN_API_KEY=your_etherscan_api_key_here")
        return False

    # 显示API密钥状态（部分隐藏以保护隐私）
    masked_key = alchemy_api_key[:8] + "..." + alchemy_api_key[-4:] if len(alchemy_api_key) > 12 else "***"
    print(f"🔑 使用Alchemy API密钥: {masked_key}")

    # 检查密钥格式
    if alchemy_api_key == "your_alchemy_api_key_here" or alchemy_api_key == "pmlCFu1i2gnC7NqSkrTEY":
        print("⚠️  警告: 使用的是示例API密钥，需要替换为真实的Alchemy API密钥")
        print("   请访问 https://www.alchemy.com/ 注册并获取免费API密钥")
        return False

    return True

def connect_to_ethereum():
    """
    连接以太坊节点
    返回Web3实例
    """
    load_dotenv()
    alchemy_api_key = os.getenv("ALCHEMY_API_KEY")

    # 构建RPC URL
    rpc_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"

    # 创建Web3实例
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    # 检查连接
    if w3.is_connected():
        print("✅ 成功连接到以太坊网络")
        return w3
    else:
        print("❌ 连接以太坊失败，请检查网络或API密钥")
        return None

def get_block_info(w3, block_number='latest'):
    """
    获取指定区块的信息
    参数：
        w3: Web3实例
        block_number: 区块号或'latest'（最新区块）
    """
    try:
        # 获取区块信息
        block = w3.eth.get_block(block_number)
        return block
    except Exception as e:
        print(f"❌ 获取区块信息失败: {e}")
        return None

def display_block_info(block, w3):
    """
    显示区块的详细信息
    """
    if not block:
        print("❌ 区块数据为空")
        return

    print("\n" + "="*60)
    print("📦 区块详细信息")
    print("="*60)

    # 基本信息
    print(f"区块高度: {block['number']}")
    print(f"区块哈希: {block['hash'].hex()}")

    # 时间信息
    from datetime import datetime
    timestamp = block['timestamp']
    dt = datetime.fromtimestamp(timestamp)
    print(f"时间戳: {timestamp} ({dt.strftime('%Y-%m-%d %H:%M:%S')})")

    # 矿工信息
    print(f"矿工地址: {block['miner']}")

    # 交易信息
    tx_count = len(block['transactions'])
    print(f"交易数量: {tx_count}")

    # Gas信息
    print(f"Gas限制: {block['gasLimit']:,}")
    print(f"Gas使用量: {block['gasUsed']:,}")
    gas_usage_percent = (block['gasUsed'] / block['gasLimit']) * 100
    print(f"Gas使用率: {gas_usage_percent:.1f}%")

    # 难度和随机数
    print(f"难度值: {block['difficulty']:,}")
    print(f"随机数: {block['nonce'].hex()}")

    # 父区块信息
    print(f"父区块哈希: {block['parentHash'].hex()}")

    print("="*60)

def get_multiple_blocks(w3, count=5):
    """
    获取多个连续区块的信息
    """
    print(f"\n📊 最近 {count} 个区块的交易数量统计")
    print("-"*40)

    latest_block = w3.eth.block_number

    for i in range(count):
        block_number = latest_block - i
        block = w3.eth.get_block(block_number)
        tx_count = len(block['transactions'])

        # 获取区块时间
        timestamp = block['timestamp']
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)

        print(f"区块 #{block_number:8d} | 交易数: {tx_count:4d} | 时间: {dt.strftime('%H:%M:%S')}")

def main():
    """
    主函数：执行区块信息查询练习
    """
    print("🔍 区块链学习 - 练习1：查询最新区块信息")
    print("="*60)

    # 检查API配置
    if not check_api_config():
        sys.exit(1)

    # 连接以太坊
    w3 = connect_to_ethereum()
    if not w3:
        sys.exit(1)

    # 获取最新区块号
    latest_block_number = w3.eth.block_number
    print(f"📈 最新区块号: {latest_block_number}")

    # 获取最新区块信息
    print("\n正在获取最新区块信息...")
    latest_block = get_block_info(w3, 'latest')

    if latest_block:
        # 显示区块详情
        display_block_info(latest_block, w3)

        # 获取多个区块的交易统计
        get_multiple_blocks(w3, count=10)

        # 获取前一个区块进行比较
        print("\n🔍 比较前一个区块:")
        previous_block = get_block_info(w3, latest_block['number'] - 1)
        if previous_block:
            print(f"  区块 #{previous_block['number']}: {len(previous_block['transactions'])} 笔交易")

        # 显示当前Gas价格
        current_gas_price = w3.eth.gas_price
        print(f"\n⛽ 当前Gas价格: {w3.from_wei(current_gas_price, 'gwei'):.0f} Gwei")
        print(f"  (约 {w3.from_wei(current_gas_price, 'ether'):.8f} ETH/Gas)")

        # 显示链ID
        chain_id = w3.eth.chain_id
        print(f"🔗 链ID: {chain_id} (1 = Ethereum主网)")

    print("\n" + "="*60)
    print("✅ 练习1完成！")
    print("\n学习总结：")
    print("1. 学会了如何连接以太坊网络")
    print("2. 掌握了区块的基本结构和关键字段")
    print("3. 了解了区块高度、时间戳、交易数量等概念")
    print("4. 学会了获取多个区块进行对比分析")
    print("="*60)

if __name__ == "__main__":
    main()