#!/usr/bin/env python3
"""
练习3：拉取地址历史交易并保存为CSV

目标：掌握使用Etherscan API获取地址交易历史，进行基本数据分析

学习点：
1. 使用Etherscan API查询地址交易历史
2. 处理API响应和分页
3. 数据解析和清洗
4. 使用csv模块保存数据
5. 基本统计分析和可视化思维

运行前请确保：
1. 已配置 .env 文件，包含ETHERSCAN_API_KEY
2. 准备要查询的以太坊地址

示例地址：
- Vitalik Buterin: 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
- Uniswap V2 Router: 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D
- 或任何你感兴趣的地址
"""

import os
import sys
import csv
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from web3 import Web3
import requests

def check_api_config():
    """
    检查API配置是否完整
    需要Etherscan API密钥
    """
    load_dotenv()
    etherscan_api_key = os.getenv("ETHERSCAN_API_KEY")

    if not etherscan_api_key:
        print("[错误] 错误：缺少Etherscan API密钥配置")
        print("\n请按照以下步骤配置：")
        print("1. 复制 .env.example 为 .env")
        print("2. 在 .env 文件中填入你的Etherscan API密钥")
        print("3. Etherscan API密钥获取地址：https://etherscan.io/apis")
        print("\n注意：Etherscan API免费版每天有10万次调用限制")
        return False

    # 显示API密钥状态（部分隐藏以保护隐私）
    masked_key = etherscan_api_key[:8] + "..." + etherscan_api_key[-4:] if len(etherscan_api_key) > 12 else "***"
    print(f"[密钥] 使用Etherscan API密钥: {masked_key}")

    # 检查密钥格式
    if etherscan_api_key == "your_etherscan_key_here" or etherscan_api_key == "GQZUWB91R2ZTDP8EGDRSU2XXQXHAT2VEQ9":
        print("[警告]  警告: 使用的是示例API密钥，需要替换为真实的Etherscan API密钥")
        print("   请访问 https://etherscan.io/apis 注册并获取免费API密钥")
        return False

    return True

def get_address_transactions_etherscan(address, api_key, max_txs=100):
    """
    使用Etherscan API获取地址交易历史
    注意：Etherscan已迁移到API V2，旧V1端点已弃用
    参数：
        address: 以太坊地址
        api_key: Etherscan API密钥
        max_txs: 最大交易数量（默认100）
    """
    # Etherscan API 可能的端点格式
    # 由于V2迁移，尝试多种可能的端点格式
    possible_base_urls = [
        "https://api.etherscan.io/v2/api",  # V2端点（推荐）
        "https://api.etherscan.io/api/v2",  # 另一种可能的V2端点
        "https://api.etherscan.io/v2",      # 简写V2端点
        "https://api.etherscan.io/api",     # V1端点（已弃用，备用）
    ]

    # API参数
    # V2 API需要chainid参数，以太坊主网chainid=1
    params = {
        'module': 'account',
        'action': 'txlist',
        'address': address,
        'startblock': 0,
        'endblock': 99999999,
        'page': 1,
        'offset': min(max_txs, 10000),  # Etherscan单次最多10000条
        'sort': 'desc',  # 最新的交易在前
        'apikey': api_key,
        'chainid': 1  # 以太坊主网chainid，V2 API必需
    }

    print(f"正在获取地址 {address} 的交易历史...")
    print(f"最多获取 {max_txs} 笔交易")

    # 尝试所有可能的端点
    last_error = None
    for base_url in possible_base_urls:
        try:
            print(f"\n尝试端点: {base_url}")

            # 调试：打印请求URL（不含API密钥）
            debug_params = params.copy()
            debug_params['apikey'] = '***隐藏***'
            debug_url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in debug_params.items()])}"
            print(f"[搜索] 调试: API请求: {debug_url}")

            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # 调试：打印完整响应
            print(f"[搜索] 调试: API响应状态: {data.get('status', '无状态字段')}")
            print(f"[搜索] 调试: API消息: {data.get('message', '无消息字段')}")
            # 打印完整响应以便调试
            print(f"[搜索] 调试: 完整响应: {json.dumps(data, indent=2)[:500]}...")

            # 检查API响应状态
            if data['status'] != '1':
                error_msg = data.get('message', '未知错误')
                print(f"[错误] 端点 {base_url} 返回错误: {error_msg}")

                # 如果是弃用的V1端点，继续尝试下一个
                if 'deprecated V1 endpoint' in error_msg:
                    last_error = f"V1端点已弃用: {error_msg}"
                    continue
                elif 'Invalid API Key' in error_msg:
                    print("[提示] 提示: API密钥无效，请检查 .env 文件中的 ETHERSCAN_API_KEY")
                    print("      获取有效API密钥: https://etherscan.io/apis")
                    return None
                elif 'rate limit' in error_msg.lower():
                    print("[提示] 提示: 达到API调用频率限制，请稍后重试")
                    return None
                elif error_msg == 'No transactions found':
                    print("[信息]  该地址没有交易记录")
                    return []
                else:
                    last_error = error_msg
                    continue  # 尝试下一个端点

            # 成功获取数据
            if 'result' in data:
                transactions = data['result'][:max_txs]
                print(f"[成功] 成功从 {base_url} 获取 {len(transactions)} 笔交易")
                return transactions
            else:
                print(f"[错误] 端点 {base_url} 返回的数据没有result字段")
                last_error = "API响应缺少result字段"
                continue

        except requests.exceptions.RequestException as e:
            print(f"[错误] 端点 {base_url} 网络请求失败: {e}")
            last_error = str(e)
            # 404错误可能是端点不存在，继续尝试下一个
            if "404" in str(e):
                continue
            else:
                # 其他网络错误可能不是端点问题，直接返回
                return None
        except json.JSONDecodeError as e:
            print(f"[错误] 端点 {base_url} JSON解析失败: {e}")
            last_error = str(e)
            continue
        except Exception as e:
            print(f"[错误] 端点 {base_url} 获取交易失败: {e}")
            last_error = str(e)
            continue

    # 所有端点都尝试失败
    print(f"\n[错误] 所有端点尝试都失败")
    if last_error:
        print(f"最后错误: {last_error}")

    # 根据最后错误给出建议
    if "404" in str(last_error):
        print("[提示] 提示: 所有API端点都返回404，可能需要检查Etherscan API文档")
        print("      文档: https://docs.etherscan.io/v2-migration")

    return None

def parse_etherscan_transaction(tx, w3):
    """
    解析Etherscan API返回的交易数据
    """
    try:
        # 基础信息
        parsed = {
            'hash': tx.get('hash', ''),
            'block_number': int(tx.get('blockNumber', 0)),
            'timestamp': int(tx.get('timeStamp', 0)),
            'datetime': datetime.fromtimestamp(int(tx.get('timeStamp', 0))).strftime('%Y-%m-%d %H:%M:%S'),
            'from': tx.get('from', ''),
            'to': tx.get('to', ''),
            'value_wei': int(tx.get('value', 0)),
            'value_eth': w3.from_wei(int(tx.get('value', 0)), 'ether'),
            'gas': int(tx.get('gas', 0)),
            'gas_price_wei': int(tx.get('gasPrice', 0)),
            'gas_price_gwei': w3.from_wei(int(tx.get('gasPrice', 0)), 'gwei'),
            'gas_used': int(tx.get('gasUsed', 0)),
            'gas_fee_wei': int(tx.get('gasUsed', 0)) * int(tx.get('gasPrice', 0)),
            'gas_fee_eth': w3.from_wei(int(tx.get('gasUsed', 0)) * int(tx.get('gasPrice', 0)), 'ether'),
            'is_error': tx.get('isError', '0'),
            'txreceipt_status': tx.get('txreceipt_status', ''),
            'input': tx.get('input', ''),
            'contract_address': tx.get('contractAddress', ''),
            'cumulative_gas_used': int(tx.get('cumulativeGasUsed', 0)),
            'confirmations': int(tx.get('confirmations', 0))
        }

        # 交易类型判断
        input_data = parsed['input']
        if parsed['contract_address']:
            parsed['tx_type'] = '合约创建'
        elif len(input_data) > 2 and input_data != '0x':  # 有输入数据
            parsed['tx_type'] = '合约调用'
        else:
            parsed['tx_type'] = '普通转账'

        # 交易状态
        if parsed['is_error'] == '1':
            parsed['status'] = '失败'
        elif parsed['txreceipt_status'] == '1':
            parsed['status'] = '成功'
        else:
            parsed['status'] = '未知'

        return parsed

    except Exception as e:
        print(f"[错误] 解析交易失败: {e}, 交易数据: {tx.get('hash', '未知')}")
        return None

def save_to_csv(transactions, filename):
    """
    将交易数据保存为CSV文件
    使用Python内置csv模块，不依赖pandas
    """
    if not transactions:
        print("[错误] 没有交易数据可保存")
        return False

    try:
        # 确定CSV文件的列（选择最重要的字段）
        fieldnames = [
            'hash', 'block_number', 'datetime', 'from', 'to',
            'tx_type', 'status', 'value_eth', 'gas_price_gwei',
            'gas_used', 'gas_fee_eth', 'confirmations'
        ]

        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for tx in transactions:
                # 只写入选定的字段
                row = {field: tx.get(field, '') for field in fieldnames}
                writer.writerow(row)

        print(f"[成功] 交易数据已保存到: {filename}")
        print(f"   共 {len(transactions)} 笔交易")
        print(f"   文件大小: {os.path.getsize(filename) / 1024:.1f} KB")
        return True

    except Exception as e:
        print(f"[错误] 保存CSV文件失败: {e}")
        return False

def analyze_transactions(transactions):
    """
    对交易数据进行基本分析
    返回统计信息
    """
    if not transactions:
        return None

    stats = {
        'total_txs': len(transactions),
        'successful_txs': 0,
        'failed_txs': 0,
        'total_value_eth': 0.0,
        'total_gas_fee_eth': 0.0,
        'tx_types': {},
        'date_range': None
    }

    timestamps = []
    values_eth = []
    gas_fees_eth = []

    for tx in transactions:
        # 统计交易状态
        if tx.get('status') == '成功':
            stats['successful_txs'] += 1
        elif tx.get('status') == '失败':
            stats['failed_txs'] += 1

        # 统计交易类型
        tx_type = tx.get('tx_type', '未知')
        stats['tx_types'][tx_type] = stats['tx_types'].get(tx_type, 0) + 1

        # 累加金额和Gas费用
        stats['total_value_eth'] += float(tx.get('value_eth', 0))
        stats['total_gas_fee_eth'] += float(tx.get('gas_fee_eth', 0))

        # 收集时间戳用于范围计算
        timestamp = tx.get('timestamp')
        if timestamp:
            timestamps.append(timestamp)

        # 收集数值用于后续分析
        values_eth.append(float(tx.get('value_eth', 0)))
        gas_fees_eth.append(float(tx.get('gas_fee_eth', 0)))

    # 计算日期范围
    if timestamps:
        min_time = min(timestamps)
        max_time = max(timestamps)
        stats['date_range'] = {
            'start': datetime.fromtimestamp(min_time).strftime('%Y-%m-%d'),
            'end': datetime.fromtimestamp(max_time).strftime('%Y-%m-%d'),
            'days': (max_time - min_time) / (24 * 3600) if max_time > min_time else 0
        }

    # 计算平均值
    if stats['total_txs'] > 0:
        stats['avg_value_eth'] = stats['total_value_eth'] / stats['total_txs']
        stats['avg_gas_fee_eth'] = stats['total_gas_fee_eth'] / stats['total_txs']

    # 找出最大单笔交易
    if values_eth:
        max_value_idx = values_eth.index(max(values_eth))
        stats['largest_tx'] = {
            'value_eth': values_eth[max_value_idx],
            'hash': transactions[max_value_idx].get('hash', ''),
            'to': transactions[max_value_idx].get('to', '')
        }

    return stats

def display_statistics(stats, address):
    """
    显示交易统计信息
    """
    if not stats:
        print("[错误] 没有统计信息可显示")
        return

    print("\n" + "="*70)
    print(f"[统计] 地址 {address[:10]}... 交易分析报告")
    print("="*70)

    print(f"\n[图表] 基本统计")
    print("-"*40)
    print(f"总交易笔数: {stats['total_txs']:,}")
    print(f"成功交易: {stats['successful_txs']:,} ({stats['successful_txs']/stats['total_txs']*100:.1f}%)")
    print(f"失败交易: {stats['failed_txs']:,} ({stats['failed_txs']/stats['total_txs']*100:.1f}%)")

    if stats.get('date_range'):
        print(f"\n[日历] 时间范围")
        print("-"*40)
        print(f"开始: {stats['date_range']['start']}")
        print(f"结束: {stats['date_range']['end']}")
        print(f"天数: {stats['date_range']['days']:.1f} 天")

    print(f"\n[资金] 资金流动")
    print("-"*40)
    print(f"总转账金额: {stats['total_value_eth']:.4f} ETH")
    if stats.get('avg_value_eth'):
        print(f"平均每笔金额: {stats['avg_value_eth']:.4f} ETH")

    if stats.get('largest_tx'):
        print(f"最大单笔交易: {stats['largest_tx']['value_eth']:.4f} ETH")
        print(f"  交易哈希: {stats['largest_tx']['hash'][:20]}...")
        print(f"  接收方: {stats['largest_tx']['to'][:20]}...")

    print(f"\n[燃料] Gas费用统计")
    print("-"*40)
    print(f"总Gas费用: {stats['total_gas_fee_eth']:.6f} ETH")
    if stats.get('avg_gas_fee_eth'):
        print(f"平均每笔Gas费用: {stats['avg_gas_fee_eth']:.6f} ETH")

    print(f"\n[工具] 交易类型分布")
    print("-"*40)
    for tx_type, count in stats['tx_types'].items():
        percentage = (count / stats['total_txs']) * 100
        print(f"{tx_type}: {count:,} 笔 ({percentage:.1f}%)")

    print("="*70)

def get_example_addresses():
    """
    返回一些示例地址
    """
    examples = [
        {
            'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
            'name': 'Vitalik Buterin (以太坊创始人)',
            'desc': '观察创始人的交易模式'
        },
        {
            'address': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
            'name': 'Uniswap V2 Router',
            'desc': '去中心化交易所路由，交易频繁'
        },
        {
            'address': '0x28C6c06298d514Db089934071355E5743bf21d60',
            'name': 'Binance 14 (交易所热钱包)',
            'desc': '交易所钱包，大额交易多'
        },
        {
            'address': '0x0000000000000000000000000000000000000000',
            'name': '零地址 (合约创建)',
            'desc': '合约创建时使用的地址'
        }
    ]
    return examples

def main():
    """
    主函数：执行地址历史交易练习
    """
    print("[搜索] 区块链学习 - 练习3：拉取地址历史交易")
    print("="*70)

    # 检查API配置
    if not check_api_config():
        sys.exit(1)

    # 加载API密钥
    load_dotenv()
    etherscan_api_key = os.getenv("ETHERSCAN_API_KEY")

    # 创建Web3实例用于单位转换
    w3 = Web3()

    # 选择要查询的地址
    print("\n请选择要查询的地址：")
    examples = get_example_addresses()
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['name']}")
        print(f"   地址: {example['address']}")
        print(f"   描述: {example['desc']}")
        print()

    print("5. 输入自定义地址")

    choice = input("\n请选择 (1-5): ").strip()

    address = None
    if choice == '1':
        address = examples[0]['address']
        print(f"选择: {examples[0]['name']}")
    elif choice == '2':
        address = examples[1]['address']
        print(f"选择: {examples[1]['name']}")
    elif choice == '3':
        address = examples[2]['address']
        print(f"选择: {examples[2]['name']}")
    elif choice == '4':
        address = examples[3]['address']
        print(f"选择: {examples[3]['name']}")
    elif choice == '5':
        address = input("请输入以太坊地址 (0x开头): ").strip()
    else:
        print("[错误] 无效选择，使用默认地址: Vitalik Buterin")
        address = examples[0]['address']

    # 验证地址格式
    if not address.startswith('0x') or len(address) != 42:
        print(f"[错误] 地址格式错误: {address}")
        print("  正确格式: 0x开头，总共42个字符（0x + 40个十六进制字符）")
        sys.exit(1)

    # 获取交易数量限制
    try:
        max_txs = int(input("\n请输入要获取的最大交易数量 (默认100，建议不超过1000): ") or "100")
        max_txs = min(max_txs, 1000)  # 限制最大数量，避免API限制
    except ValueError:
        print("[错误] 输入无效，使用默认值100")
        max_txs = 100

    # 获取交易数据
    raw_transactions = get_address_transactions_etherscan(
        address=address,
        api_key=etherscan_api_key,
        max_txs=max_txs
    )

    if raw_transactions is None:
        print("[错误] 获取交易数据失败")
        sys.exit(1)

    if not raw_transactions:
        print("[信息]  该地址没有交易记录")
        sys.exit(0)

    # 解析交易数据
    print(f"\n正在解析 {len(raw_transactions)} 笔交易...")
    parsed_transactions = []
    for i, raw_tx in enumerate(raw_transactions):
        parsed = parse_etherscan_transaction(raw_tx, w3)
        if parsed:
            parsed_transactions.append(parsed)

        # 显示进度
        if (i + 1) % 20 == 0 or (i + 1) == len(raw_transactions):
            print(f"  已解析 {i + 1}/{len(raw_transactions)} 笔交易")

    print(f"[成功] 成功解析 {len(parsed_transactions)} 笔交易")

    # 保存为CSV文件
    filename = f"transactions_{address[:10]}_{int(time.time())}.csv"
    save_success = save_to_csv(parsed_transactions, filename)

    # 分析数据
    stats = analyze_transactions(parsed_transactions)
    if stats:
        display_statistics(stats, address)

    # 学习总结
    print("\n" + "="*70)
    print("[成功] 练习3完成！")
    print("\n[学习] 学习总结：")
    print("1. 学会了使用Etherscan API获取地址交易历史")
    print("2. 掌握了交易数据的解析和清洗方法")
    print("3. 学会了使用csv模块保存结构化数据")
    print("4. 掌握了基本的交易数据分析技巧")
    print("5. 理解了不同类型交易的特点（转账、合约调用等）")

    if save_success:
        print(f"\n[保存] 数据文件: {filename}")
        print("   可以使用Excel、Numbers或文本编辑器打开查看")

    print("\n[提示] 下一步建议：")
    print("- 尝试分析不同地址的交易模式")
    print("- 比较不同时间段的Gas价格变化")
    print("- 计算地址的ETH余额变化（需要额外处理内部交易）")
    print("- 在后续学习中引入pandas进行更复杂的分析")
    print("="*70)

if __name__ == "__main__":
    main()