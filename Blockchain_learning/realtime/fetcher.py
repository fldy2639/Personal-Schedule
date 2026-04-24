#!/usr/bin/env python3
"""
数据获取：实时 USDC Transfer 日志拉取（eth_getLogs 分块 + 重试/限速）。

职责：连接节点、分块拉取原始日志，不做业务解析。
"""

from __future__ import annotations

import time
from typing import Any

from web3 import Web3

from config import get_alchemy_rpc_url

from .config import USDC_CONTRACT_ADDRESS, USDC_TRANSFER_TOPIC0

# 包外引用旧路径时仍可见（与单模块时代一致）
__all__ = [
    "USDC_CONTRACT_ADDRESS",
    "USDC_TRANSFER_TOPIC0",
    "create_web3_client",
    "fetch_usdc_transfer_logs",
]


def create_web3_client() -> Web3:
    """
    创建并校验 Web3 连接。

    返回:
        Web3: 已连接的 Web3 实例。

    异常:
        ConnectionError: 无法连接节点时抛出。
    """
    rpc_url = get_alchemy_rpc_url()
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise ConnectionError("无法连接以太坊节点，请检查 ALCHEMY_API_KEY 或网络状态。")
    return w3


def fetch_usdc_transfer_logs(
    w3: Web3,
    end_block: int,
    block_span: int,
    chunk_size: int = 10,
    sleep_seconds: float = 0.05,
    max_retries: int = 3,
    retry_backoff_seconds: float = 0.8,
) -> list[dict[str, Any]]:
    """
    分块拉取 USDC Transfer 原始日志（eth_getLogs）。

    参数:
        w3: Web3 客户端实例。
        end_block: 查询结束区块（包含）。
        block_span: 向前覆盖的区块数量（包含 end_block）。
        chunk_size: 每次请求的区块跨度，默认 10。
        sleep_seconds: 每个分块请求后的暂停秒数，默认 0.05。
        max_retries: 单分块失败时最大重试次数，默认 3。
        retry_backoff_seconds: 重试基准退避秒数，默认 0.8。

    返回:
        list[dict[str, Any]]: 原始日志列表（不做业务解析）。

    异常:
        ValueError: 参数非法时抛出。
        RuntimeError: 超过重试次数后仍失败时抛出。
    """
    if block_span <= 0:
        raise ValueError("block_span 必须大于 0。")
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0。")
    if end_block < 0:
        raise ValueError("end_block 不能为负数。")

    start_block = max(0, end_block - block_span + 1)
    checksum_contract = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS)

    all_logs: list[dict[str, Any]] = []
    for chunk_start in range(start_block, end_block + 1, chunk_size):
        chunk_end = min(chunk_start + chunk_size - 1, end_block)

        for attempt in range(1, max_retries + 1):
            try:
                logs = w3.eth.get_logs(
                    {
                        "fromBlock": chunk_start,
                        "toBlock": chunk_end,
                        "address": checksum_contract,
                        "topics": [USDC_TRANSFER_TOPIC0],
                    }
                )
                all_logs.extend(logs)
                break
            except Exception as exc:
                if attempt >= max_retries:
                    raise RuntimeError(
                        f"区块范围 {chunk_start}-{chunk_end} 拉取失败，已重试 {max_retries} 次。"
                    ) from exc
                wait_seconds = retry_backoff_seconds * attempt
                time.sleep(wait_seconds)

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    return all_logs
