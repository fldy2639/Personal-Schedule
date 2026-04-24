#!/usr/bin/env python3
"""
分析模块：提供 Week 3 复用的 Pandas 聚合分析函数。

从 Week 2 导出的 USDC Transfer CSV 出发，完成时间序列聚合与地址维度统计。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd

# Week 2 CSV 必备列（与 week2_events 导出格式一致）
REQUIRED_COLUMNS = {
    "transaction_hash",
    "block_number",
    "log_index",
    "from",
    "to",
    "value_raw",
    "value_usdc",
    "timestamp",
    "datetime",
}


def load_usdc_csv(path: str | Path) -> pd.DataFrame:
    """
    读取 Week 2 产出的 USDC Transfer 事件 CSV。

    参数:
        path: CSV 文件路径。

    返回:
        pd.DataFrame: 原始数据表。

    异常:
        FileNotFoundError: 文件不存在时抛出。
    """
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 文件不存在: {csv_path}")
    return pd.read_csv(csv_path)


def ensure_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """
    将时间列规范为 UTC，并派生按日聚合用的 date 列；校验数值列可解析。

    若 datetime 列无法解析，会回退使用 timestamp（秒级 Unix 时间）。

    参数:
        df: 原始 DataFrame，须包含 REQUIRED_COLUMNS 所列字段。

    返回:
        pd.DataFrame: 含规范化后的 datetime、date 与数值型 value_usdc 的副本。

    异常:
        ValueError: 缺少必备列、存在无法解析的时间或金额时抛出。
    """
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"缺少必要列: {sorted(missing)}")

    out = df.copy()
    # 优先解析 datetime 字符串为 UTC；失败则使用链上 timestamp（秒）
    out["datetime"] = pd.to_datetime(out["datetime"], errors="coerce", utc=True)
    if out["datetime"].isna().all():
        out["datetime"] = pd.to_datetime(out["timestamp"], unit="s", utc=True, errors="coerce")

    if out["datetime"].isna().any():
        bad_count = int(out["datetime"].isna().sum())
        raise ValueError(f"存在无法解析的时间数据，条数: {bad_count}")

    # 按 UTC 日历日聚合（避免本地时区导致跨日错位）
    out["date"] = out["datetime"].dt.date
    out["value_usdc"] = pd.to_numeric(out["value_usdc"], errors="coerce")
    if out["value_usdc"].isna().any():
        bad_count = int(out["value_usdc"].isna().sum())
        raise ValueError(f"存在无法解析的 value_usdc 数据，条数: {bad_count}")

    return out


def compute_daily_volume(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算每日 USDC 转账总量（按日志金额求和）。

    参数:
        df: 已调用 ensure_datetime 的 DataFrame。

    返回:
        pd.DataFrame: 列 date, daily_volume_usdc，按日期升序。
    """
    grouped = (
        df.groupby("date", as_index=False)["value_usdc"]
        .sum()
        .rename(columns={"value_usdc": "daily_volume_usdc"})
        .sort_values("date")
    )
    return grouped


def compute_daily_tx_count(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算每日 Transfer 日志条数（同一笔交易可能对应多条日志）。

    参数:
        df: 已调用 ensure_datetime 的 DataFrame。

    返回:
        pd.DataFrame: 列 date, daily_tx_count，按日期升序。
    """
    grouped = (
        df.groupby("date", as_index=False)
        .size()
        .rename(columns={"size": "daily_tx_count"})
        .sort_values("date")
    )
    return grouped


def analyze_address_activity(df: pd.DataFrame, address: str) -> dict[str, Any]:
    """
    统计指定地址在样本内的收发笔数、金额与净流入；时间范围仅统计该地址参与过的行。

    参数:
        df: 已调用 ensure_datetime 的 DataFrame。
        address: 待分析的以太坊地址（大小写不敏感）。

    返回:
        dict: 包含笔数、金额、净流入、首次/末次出现时间等字段。
    """
    addr = address.lower()
    incoming = df[df["to"].str.lower() == addr].copy()
    outgoing = df[df["from"].str.lower() == addr].copy()

    total_received = float(incoming["value_usdc"].sum()) if not incoming.empty else 0.0
    total_sent = float(outgoing["value_usdc"].sum()) if not outgoing.empty else 0.0

    # 该地址作为 from 或 to 出现过的所有行（用于 first/last_seen）
    mask = (df["to"].str.lower() == addr) | (df["from"].str.lower() == addr)
    involved = df.loc[mask]
    if not involved.empty:
        first_seen = str(involved["datetime"].min())
        last_seen = str(involved["datetime"].max())
    else:
        first_seen = None
        last_seen = None

    return {
        "address": address,
        "tx_count_in": int(len(incoming)),
        "tx_count_out": int(len(outgoing)),
        "tx_count_total": int(len(incoming) + len(outgoing)),
        "unique_txs_in": int(incoming["transaction_hash"].nunique()) if not incoming.empty else 0,
        "unique_txs_out": int(outgoing["transaction_hash"].nunique()) if not outgoing.empty else 0,
        "total_received_usdc": total_received,
        "total_sent_usdc": total_sent,
        "net_flow_usdc": total_received - total_sent,
        "first_seen": first_seen,
        "last_seen": last_seen,
    }


def export_analysis_outputs(
    daily_volume_df: pd.DataFrame,
    daily_tx_count_df: pd.DataFrame,
    address_stats: Optional[dict[str, Any]],
    output_dir: str | Path,
) -> dict[str, str]:
    """
    将每日聚合结果与可选的地址统计写入 data/week3 等目录。

    参数:
        daily_volume_df: compute_daily_volume 的输出。
        daily_tx_count_df: compute_daily_tx_count 的输出。
        address_stats: analyze_address_activity 的返回值；可为 None（仍写出空 JSON 占位）。
        output_dir: 输出目录，不存在则创建。

    返回:
        dict: 写出文件的绝对路径字符串，键为 daily_volume_csv、daily_tx_count_csv、address_stats_json。
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    volume_path = out_dir / f"daily_volume_{ts}.csv"
    tx_count_path = out_dir / f"daily_tx_count_{ts}.csv"
    stats_path = out_dir / f"address_stats_{ts}.json"

    daily_volume_df.to_csv(volume_path, index=False)
    daily_tx_count_df.to_csv(tx_count_path, index=False)

    payload = address_stats if address_stats is not None else {}
    stats_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "daily_volume_csv": str(volume_path),
        "daily_tx_count_csv": str(tx_count_path),
        "address_stats_json": str(stats_path),
    }
