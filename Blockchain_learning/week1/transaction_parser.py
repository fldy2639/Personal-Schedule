#!/usr/bin/env python3
"""
练习2：解析指定交易详情

目标：掌握交易和交易收据的解析方法，理解两者的区别

学习点：
1. 获取交易详情（transaction）和交易收据（receipt）
2. 解析交易的关键字段
3. 单位转换：wei → ether/gwei
4. 理解交易状态和Gas费用计算
5. 分析事件日志（Event Logs）

运行前请确保：
1. 已配置 .env 文件（参考练习1）
2. 准备一个有效的交易哈希用于测试

示例交易哈希（以太坊主网）：
- 0x2f81c59fb33e44c5e8e6b2d7b933e8f8c06d8e7c3e3e9e3b7e3e3e3e3e3e3e3e3 (示例，请使用真实交易)
- 可以从 etherscan.io 查找真实交易哈希
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3
from datetime import datetime

def check_api_config():
    """
    检查API配置是否完整
    """
    load_dotenv()
    alchemy_api_key = os.getenv("ALCHEMY_API_KEY")

    if not alchemy_api_key:
        print("❌ 错误：缺少Alchemy API密钥配置")
        print("\n请按照以下步骤配置：")
        print("1. 复制 .env.example 为 .env")
        print("2. 在 .env 文件中填入你的Alchemy API密钥")
        print("3. 参考练习1的说明获取API密钥")
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
    """
    load_dotenv()
    alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
    rpc_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"

    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if w3.is_connected():
        print("✅ 成功连接到以太坊网络")
        return w3
    else:
        print("❌ 连接以太坊失败")
        return None

def get_transaction_data(w3, tx_hash):
    """
    获取交易详情和交易收据
    返回：(transaction, receipt) 元组
    """
    try:
        print(f"正在查询交易: {tx_hash}")

        # 获取交易详情
        transaction = w3.eth.get_transaction(tx_hash)
        if not transaction:
            print("❌ 未找到该交易")
            return None, None

        # 获取交易收据
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if not receipt:
            print("⚠️  找到交易但未找到收据（可能尚未确认）")
            # 收据可能为空，但交易存在

        return transaction, receipt

    except Exception as e:
        print(f"❌ 获取交易数据失败: {e}")
        return None, None

def parse_transaction(transaction, w3):
    """
    解析交易详情
    """
    if not transaction:
        return None

    parsed = {
        'hash': transaction['hash'].hex() if hasattr(transaction['hash'], 'hex') else transaction['hash'],
        'block_number': transaction['blockNumber'] if transaction['blockNumber'] else '待确认',
        'from': transaction['from'],
        'to': transaction['to'] if transaction['to'] else '合约创建',
        'value_wei': transaction['value'],
        'value_eth': w3.from_wei(transaction['value'], 'ether'),
        'gas': transaction['gas'],
        'gas_price_wei': transaction['gasPrice'],
        'gas_price_gwei': w3.from_wei(transaction['gasPrice'], 'gwei'),
        'nonce': transaction['nonce'],
        'input': transaction['input'],
        'input_length': len(transaction['input']),
        'is_contract_creation': transaction['to'] is None,
        'is_contract_interaction': len(transaction['input']) > 2  # 不是简单的0x
    }

    return parsed

def parse_receipt(receipt, w3):
    """
    解析交易收据
    """
    if not receipt:
        return None

    gas_used = receipt['gasUsed']
    gas_price = receipt.get('effectiveGasPrice', 0)

    parsed = {
        'transaction_hash': receipt['transactionHash'].hex(),
        'block_number': receipt['blockNumber'],
        'status': receipt['status'] == 1,  # 1=成功, 0=失败
        'gas_used': gas_used,
        'gas_price_wei': gas_price,
        'gas_price_gwei': w3.from_wei(gas_price, 'gwei'),
        'gas_fee_wei': gas_used * gas_price,
        'gas_fee_eth': w3.from_wei(gas_used * gas_price, 'ether'),
        'contract_address': receipt.get('contractAddress'),
        'logs_count': len(receipt['logs']),
        'logs': []
    }

    # 解析事件日志（只取前3个作为示例）
    for i, log in enumerate(receipt['logs'][:3]):
        log_info = {
            'index': i,
            'address': log['address'],
            'topics_count': len(log['topics']),
            'topics': [topic.hex() for topic in log['topics']],
            'data_length': len(log['data'])
        }
        parsed['logs'].append(log_info)

    return parsed

def display_transaction_info(parsed_tx, parsed_receipt, w3):
    """
    显示交易和收据的详细信息
    """
    print("\n" + "="*70)
    print("💸 交易详情分析")
    print("="*70)

    if not parsed_tx:
        print("❌ 无交易数据")
        return

    # 交易基本信息
    print("\n📄 交易基本信息")
    print("-"*40)
    print(f"交易哈希: {parsed_tx['hash']}")
    print(f"发送方: {parsed_tx['from']}")
    print(f"接收方: {parsed_tx['to']}")
    print(f"区块: {parsed_tx['block_number']}")

    # 转账信息
    print("\n💰 转账信息")
    print("-"*40)
    print(f"转账金额: {parsed_tx['value_eth']:.8f} ETH")
    print(f"        ({parsed_tx['value_wei']:,} wei)")

    # Gas信息
    print("\n⛽ Gas信息")
    print("-"*40)
    print(f"Gas限制: {parsed_tx['gas']:,}")
    print(f"Gas价格: {parsed_tx['gas_price_gwei']:.0f} Gwei")
    print(f"        ({parsed_tx['gas_price_wei']:,} wei)")

    # 交易类型判断
    print("\n🔧 交易类型")
    print("-"*40)
    if parsed_tx['is_contract_creation']:
        print("类型: 🆕 合约创建")
    elif parsed_tx['is_contract_interaction']:
        print(f"类型: 📝 合约调用 (输入数据长度: {parsed_tx['input_length']} 字节)")
        if parsed_tx['input_length'] < 100:
            print(f"输入数据: {parsed_tx['input'][:100]}...")
    else:
        print("类型: 🔄 普通转账")

    print(f"Nonce: {parsed_tx['nonce']}")

    # 显示收据信息（如果有）
    if parsed_receipt:
        print("\n📋 交易收据")
        print("-"*40)
        print(f"状态: {'✅ 成功' if parsed_receipt['status'] else '❌ 失败'}")
        print(f"实际Gas使用量: {parsed_receipt['gas_used']:,}")
        print(f"Gas费用: {parsed_receipt['gas_fee_eth']:.6f} ETH")
        print(f"       ({parsed_receipt['gas_fee_wei']:,} wei)")

        if parsed_receipt['contract_address']:
            print(f"创建的合约地址: {parsed_receipt['contract_address']}")

        print(f"事件日志数量: {parsed_receipt['logs_count']}")

        # 显示事件日志详情
        if parsed_receipt['logs']:
            print("\n📝 事件日志（前3个）")
            print("-"*40)
            for log in parsed_receipt['logs']:
                print(f"日志 #{log['index']}:")
                print(f"  合约地址: {log['address']}")
                print(f"  主题数量: {log['topics_count']}")
                if log['topics']:
                    print(f"  第一个主题: {log['topics'][0][:20]}...")
                print(f"  数据长度: {log['data_length']} 字节")
                print()

    else:
        print("\n📋 交易收据: ⏳ 未确认或不存在")

    print("="*70)

def calculate_gas_efficiency(parsed_tx, parsed_receipt):
    """
    计算Gas使用效率
    """
    if not parsed_receipt or not parsed_tx:
        return

    gas_used = parsed_receipt['gas_used']
    gas_limit = parsed_tx['gas']

    if gas_limit > 0:
        efficiency = (gas_used / gas_limit) * 100
        print(f"\n📊 Gas使用效率: {efficiency:.1f}%")
        print(f"   Gas限制: {gas_limit:,}")
        print(f"   Gas使用: {gas_used:,}")

        if efficiency < 50:
            print("   💡 提示: Gas使用率较低，可能可以设置更低的Gas限制")
        elif efficiency > 90:
            print("   ⚠️  提示: Gas使用率较高，接近限制")

def get_example_transaction_hashes():
    """
    返回一些示例交易哈希（真实以太坊交易）
    用户可以从这些中选择或输入自己的
    """
    examples = [
        {
            'hash': '0x2f81c59fb33e44c5e8e6b2d7b933e8f8c06d8e7c3e3e9e3b7e3e3e3e3e3e3e3e3',
            'desc': '示例1: 普通ETH转账（请替换为真实哈希）'
        },
        {
            'hash': '0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060',
            'desc': '示例2: Uniswap交易（真实交易）'
        },
        {
            'hash': '0x4d69d0b4c9b8e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5',
            'desc': '示例3: 合约创建交易（请替换为真实哈希）'
        }
    ]
    return examples

def main():
    """
    主函数：执行交易解析练习
    """
    print("🔍 区块链学习 - 练习2：解析指定交易详情")
    print("="*70)

    # 检查API配置
    if not check_api_config():
        sys.exit(1)

    # 连接以太坊
    w3 = connect_to_ethereum()
    if not w3:
        sys.exit(1)

    # 获取用户输入的交易哈希
    print("\n请输入交易哈希（0x开头，64个字符），或按回车使用示例：")
    print("1. 普通ETH转账")
    print("2. Uniswap交易")
    print("3. 自定义交易哈希")

    choice = input("\n请选择 (1/2/3 或直接输入交易哈希): ").strip()

    tx_hash = None

    if choice == '1':
        # 使用示例1（需要用户替换为真实哈希）
        examples = get_example_transaction_hashes()
        tx_hash = examples[0]['hash']
        print(f"使用示例交易: {examples[0]['desc']}")
        print(f"交易哈希: {tx_hash}")
        print("⚠️  注意：这是一个示例哈希，请替换为真实的交易哈希")
    elif choice == '2':
        # 使用示例2（真实交易）
        examples = get_example_transaction_hashes()
        tx_hash = examples[1]['hash']
        print(f"使用示例交易: {examples[1]['desc']}")
        print(f"交易哈希: {tx_hash}")
    elif choice == '3':
        # 自定义交易哈希
        tx_hash = input("请输入交易哈希: ").strip()
    elif choice.startswith('0x'):
        # 用户直接输入了交易哈希
        tx_hash = choice
    else:
        print("❌ 无效输入，使用默认示例")
        examples = get_example_transaction_hashes()
        tx_hash = examples[0]['hash']

    # 验证交易哈希格式
    if not tx_hash.startswith('0x') or len(tx_hash) != 66:
        print(f"❌ 交易哈希格式错误: {tx_hash}")
        print("  正确格式: 0x开头，总共66个字符（0x + 64个十六进制字符）")
        sys.exit(1)

    # 获取交易数据
    transaction, receipt = get_transaction_data(w3, tx_hash)

    if not transaction:
        print("❌ 无法获取交易数据，请检查交易哈希是否正确")
        sys.exit(1)

    # 解析数据
    parsed_tx = parse_transaction(transaction, w3)
    parsed_receipt = parse_receipt(receipt, w3) if receipt else None

    # 显示结果
    display_transaction_info(parsed_tx, parsed_receipt, w3)

    # 计算Gas效率
    calculate_gas_efficiency(parsed_tx, parsed_receipt)

    # 学习总结
    print("\n" + "="*70)
    print("✅ 练习2完成！")
    print("\n📚 学习总结：")
    print("1. 学会了如何查询交易详情和交易收据")
    print("2. 理解了交易（意图）和收据（结果）的区别")
    print("3. 掌握了ETH单位转换（wei ↔ ether/gwei）")
    print("4. 学会了分析Gas费用和使用效率")
    print("5. 了解了事件日志的基本结构")
    print("\n💡 下一步建议：")
    print("- 尝试分析不同类型的交易（转账、合约调用、合约创建）")
    print("- 对比不同交易的Gas效率")
    print("- 在etherscan.io上查找更多交易示例")
    print("="*70)

if __name__ == "__main__":
    main()