#!/usr/bin/env python3
"""
配置模块 - 统一管理区块链学习项目的环境变量和API配置

所有API密钥和配置都应通过此模块读取，禁止在其他文件中直接访问 .env

使用示例：
    from config import get_etherscan_api_key, get_alchemy_rpc_url

    api_key = get_etherscan_api_key()
    rpc_url = get_alchemy_rpc_url()
"""

import os
import sys
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

def get_etherscan_api_key():
    """
    获取Etherscan API密钥

    返回:
        str: Etherscan API密钥
    异常:
        如果未配置API密钥，打印错误信息并退出程序
    """
    api_key = os.getenv("ETHERSCAN_API_KEY")
    if not api_key:
        print("❌ 错误：未配置 ETHERSCAN_API_KEY")
        print("请在 .env 文件中添加：ETHERSCAN_API_KEY=your_key_here")
        print("获取API密钥：https://etherscan.io/apis")
        sys.exit(1)

    # 检查是否为示例密钥
    if api_key == "your_etherscan_key_here" or api_key == "GQZUWB91R2ZTDP8EGDRSU2XXQXHAT2VEQ9":
        print("⚠️  警告：使用的是示例Etherscan API密钥，需要替换为真实的密钥")
        print("请访问 https://etherscan.io/apis 注册并获取免费API密钥")

    return api_key

def get_alchemy_api_key():
    """
    获取Alchemy API密钥

    返回:
        str: Alchemy API密钥
    异常:
        如果未配置API密钥，打印错误信息并退出程序
    """
    api_key = os.getenv("ALCHEMY_API_KEY")
    if not api_key:
        print("❌ 错误：未配置 ALCHEMY_API_KEY")
        print("请在 .env 文件中添加：ALCHEMY_API_KEY=your_key_here")
        print("获取API密钥：https://www.alchemy.com/")
        sys.exit(1)

    # 检查是否为示例密钥
    if api_key == "your_alchemy_api_key_here":
        print("⚠️  警告：使用的是示例Alchemy API密钥，需要替换为真实的密钥")
        print("请访问 https://www.alchemy.com/ 注册并获取免费API密钥")

    return api_key

def get_alchemy_rpc_url():
    """
    获取Alchemy RPC URL

    返回:
        str: 完整的Alchemy RPC URL
    """
    api_key = get_alchemy_api_key()
    return f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"

def get_etherscan_api_base_url():
    """
    获取Etherscan API基础URL（V2版本）

    返回:
        str: Etherscan V2 API基础URL
    """
    return "https://api.etherscan.io/v2/api"

def get_etherscan_api_params(chainid=1):
    """
    获取Etherscan API通用参数

    参数:
        chainid (int): 区块链ID，默认为1（以太坊主网）

    返回:
        dict: 包含chainid等通用参数的字典
    """
    return {
        'chainid': chainid,  # 以太坊主网chainid=1
    }

def mask_api_key(api_key):
    """
    隐藏API密钥的部分字符，用于安全显示

    参数:
        api_key (str): 原始API密钥

    返回:
        str: 部分隐藏的API密钥
    """
    if not api_key or len(api_key) <= 12:
        return "***"
    return api_key[:8] + "..." + api_key[-4:]

def print_api_key_status():
    """打印当前API密钥配置状态"""
    print("🔧 当前API配置状态:")
    print("-" * 40)

    try:
        etherscan_key = get_etherscan_api_key()
        print(f"Etherscan API: 已配置 ({mask_api_key(etherscan_key)})")
    except SystemExit:
        print("Etherscan API: ❌ 未配置")

    try:
        alchemy_key = get_alchemy_api_key()
        print(f"Alchemy API:   已配置 ({mask_api_key(alchemy_key)})")
    except SystemExit:
        print("Alchemy API:    ❌ 未配置")

    print("-" * 40)

# 测试配置模块
if __name__ == "__main__":
    print("🧪 测试配置模块...")
    print_api_key_status()

    try:
        etherscan_key = get_etherscan_api_key()
        print(f"✅ Etherscan API密钥获取成功: {mask_api_key(etherscan_key)}")
    except SystemExit:
        print("❌ Etherscan API密钥配置失败")

    try:
        alchemy_key = get_alchemy_api_key()
        print(f"✅ Alchemy API密钥获取成功: {mask_api_key(alchemy_key)}")

        rpc_url = get_alchemy_rpc_url()
        print(f"✅ Alchemy RPC URL: {rpc_url[:50]}...")
    except SystemExit:
        print("❌ Alchemy API密钥配置失败")