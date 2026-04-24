#!/usr/bin/env python3
"""
Week 3 练习：USDC 每日转账量时间序列 + 地址活动统计

支持两种数据源：
1. csv：读取 Week2 导出的 data/usdc_transfers_*.csv
2. realtime：通过 Alchemy RPC 分块拉取最近 N 个区块的 USDC Transfer 日志

运行示例（在项目根目录）：
  python week3/week3_analysis.py --source csv
  python week3/week3_analysis.py --source realtime --blocks 100
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from web3 import Web3

try:
    import plotly.graph_objects as go
except ImportError:  # 可视化依赖可选
    go = None

# 确保可从项目根目录导入 config / analyzer
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from analyzer import (  # noqa: E402
    analyze_address_activity,
    compute_daily_tx_count,
    compute_daily_volume,
    ensure_datetime,
    export_analysis_outputs,
    load_usdc_csv,
)
from config import get_alchemy_rpc_url  # noqa: E402

# USDC 主网合约与 Transfer topic0（与 week2 保持一致）
USDC_CONTRACT_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
TRANSFER_TOPIC0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
USDC_DECIMALS = 6

# 简化 ABI：仅用于解析 Transfer 日志
USDC_ABI_MIN = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    }
]


def _hex_to_tx_hash_str(h) -> str:
    """将交易哈希统一为 0x 开头的十六进制字符串。"""
    if hasattr(h, "hex"):
        hx = h.hex()
    else:
        hx = str(h)
    if not hx.startswith("0x"):
        hx = "0x" + hx
    return hx


def find_latest_usdc_csv(data_dir: Path) -> Path:
    """
    在 data 目录下查找最新的 usdc_transfers_*.csv。

    参数:
        data_dir: data 目录路径。

    返回:
        Path: 最新 CSV 路径。
    """
    candidates = sorted(data_dir.glob("usdc_transfers_*.csv"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(f"未找到 usdc_transfers_*.csv，请先运行 week2 练习2 生成数据: {data_dir}")
    return candidates[-1]


def fetch_usdc_transfers_realtime(
    w3: Web3,
    end_block: int,
    block_span: int,
    chunk_size: int = 10,
) -> pd.DataFrame:
    """
    通过 eth_getLogs 分块拉取 USDC Transfer，并转为与 CSV 同结构的 DataFrame。

    参数:
        w3: Web3 实例。
        end_block: 结束区块（包含）。
        block_span: 向前覆盖的区块数量（包含 end_block）。
        chunk_size: 单次查询区块跨度（兼容免费套餐限制，默认 10）。

    返回:
        pd.DataFrame: 与 week2 CSV 列一致的表。
    """
    start_block = max(0, end_block - block_span + 1)
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(USDC_CONTRACT_ADDRESS), abi=USDC_ABI_MIN
    )

    rows = []
    block_ts_cache: dict[int, int] = {}

    def _get_block_timestamp(block_number: int) -> int:
        """获取区块时间戳（带缓存，避免重复 RPC）。"""
        if block_number in block_ts_cache:
            return block_ts_cache[block_number]
        ts = int(w3.eth.get_block(block_number)["timestamp"])
        block_ts_cache[block_number] = ts
        return ts

    for chunk_start in range(start_block, end_block + 1, chunk_size):
        chunk_end = min(chunk_start + chunk_size - 1, end_block)
        logs = w3.eth.get_logs(
            {
                "fromBlock": chunk_start,
                "toBlock": chunk_end,
                "address": Web3.to_checksum_address(USDC_CONTRACT_ADDRESS),
                "topics": [TRANSFER_TOPIC0],
            }
        )
        for raw_log in logs:
            parsed = contract.events.Transfer().process_log(raw_log)
            args = parsed["args"]
            block_number = int(parsed["blockNumber"])
            tx_hash = _hex_to_tx_hash_str(parsed["transactionHash"])
            log_index = int(parsed["logIndex"])
            # 优先使用日志自带时间戳字段，避免每条日志都查询区块
            ts = None
            if isinstance(raw_log, dict) and raw_log.get("blockTimestamp") is not None:
                bts = raw_log.get("blockTimestamp")
                ts = int(bts, 16) if isinstance(bts, str) else int(bts)
            if ts is None:
                ts = _get_block_timestamp(block_number)
            value_raw = int(args["value"])
            value_usdc = value_raw / (10**USDC_DECIMALS)
            rows.append(
                {
                    "transaction_hash": tx_hash,
                    "block_number": block_number,
                    "log_index": log_index,
                    "from": args["from"],
                    "to": args["to"],
                    "value_raw": value_raw,
                    "value_usdc": value_usdc,
                    "timestamp": ts,
                    "datetime": pd.to_datetime(ts, unit="s", utc=True),
                }
            )
        time.sleep(0.05)

    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="Week3：USDC 时间序列分析")
    parser.add_argument(
        "--source",
        choices=["csv", "realtime"],
        default="csv",
        help="数据源：csv 或 realtime",
    )
    parser.add_argument(
        "--csv-path",
        default=None,
        help="指定 CSV 路径；默认取 data 目录下最新的 usdc_transfers_*.csv",
    )
    parser.add_argument(
        "--blocks",
        type=int,
        default=101,
        help="实时模式：从最新区块向前覆盖的区块数量（默认 101，与 week2 练习2 接近）",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10,
        help="实时模式：eth_getLogs 分块大小（默认 10，兼容免费套餐）",
    )
    parser.add_argument(
        "--address",
        default=None,
        help="可选：指定要统计的地址（checksum 或小写均可）",
    )
    parser.add_argument(
        "--output-dir",
        default="data/week3",
        help="分析结果输出目录",
    )
    return parser.parse_args()


def main() -> None:
    """主入口：加载数据、聚合、导出。"""
    # Windows 控制台默认 GBK 时，统一 UTF-8，避免中文与符号乱码
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    args = parse_args()
    project_root = _PROJECT_ROOT
    data_dir = project_root / "data"
    output_dir = project_root / args.output_dir

    if args.source == "csv":
        csv_path = Path(args.csv_path) if args.csv_path else find_latest_usdc_csv(data_dir)
        print(f"[信息] 使用 CSV: {csv_path}")
        df_raw = load_usdc_csv(csv_path)
    else:
        rpc_url = get_alchemy_rpc_url()
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            print("[错误] 无法连接以太坊节点")
            sys.exit(1)
        latest = w3.eth.block_number
        print(f"[信息] 实时模式：最新区块 {latest:,}，覆盖最近 {args.blocks} 个区块")
        df_raw = fetch_usdc_transfers_realtime(
            w3, end_block=latest, block_span=args.blocks, chunk_size=args.chunk_size
        )
        if df_raw.empty:
            print("[警告] 实时模式未获取到任何日志，请扩大区块范围或检查网络")
            sys.exit(0)

    df = ensure_datetime(df_raw)
    daily_volume = compute_daily_volume(df)
    daily_tx = compute_daily_tx_count(df)

    addr_stats = None
    if args.address:
        addr_stats = analyze_address_activity(df, args.address)
        print(f"[信息] 地址统计: {args.address}")

    paths = export_analysis_outputs(daily_volume, daily_tx, addr_stats, output_dir)
    print("\n[完成] 已导出：")
    for k, v in paths.items():
        print(f"  {k}: {v}")

    # 可选：导出 Plotly HTML 图表
    if go is not None and not daily_volume.empty:
        fig_vol = go.Figure(
            data=[
                go.Scatter(
                    x=daily_volume["date"].astype(str),
                    y=daily_volume["daily_volume_usdc"],
                    mode="lines+markers",
                    name="每日转账量",
                )
            ]
        )
        fig_vol.update_layout(
            title="USDC 每日转账总量（样本窗口）",
            xaxis_title="日期 (UTC)",
            yaxis_title="USDC",
        )
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        plot_path = output_dir / f"daily_volume_plot_{ts}.html"
        fig_vol.write_html(str(plot_path))
        print(f"[信息] Plotly 图表已保存: {plot_path}")

    # 控制台摘要
    print("\n📊 时间序列摘要")
    print("-" * 40)
    print(f"样本日志条数: {len(df):,}")
    if not daily_volume.empty:
        peak = daily_volume.loc[daily_volume["daily_volume_usdc"].idxmax()]
        print(f"日期范围: {daily_volume['date'].min()} ~ {daily_volume['date'].max()}")
        print(f"峰值日转账量: {peak['date']} -> {peak['daily_volume_usdc']:,.2f} USDC")
    if addr_stats:
        print("\n📌 地址摘要")
        print("-" * 40)
        print(f"净流入: {addr_stats['net_flow_usdc']:,.6f} USDC")
        print(f"日志条数 in/out/total: {addr_stats['tx_count_in']}/{addr_stats['tx_count_out']}/{addr_stats['tx_count_total']}")
        print(f"去重交易 in/out: {addr_stats['unique_txs_in']}/{addr_stats['unique_txs_out']}")


if __name__ == "__main__":
    os.makedirs(_PROJECT_ROOT / "data" / "week3", exist_ok=True)
    main()
