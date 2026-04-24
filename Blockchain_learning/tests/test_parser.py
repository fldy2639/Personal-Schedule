#!/usr/bin/env python3
"""
parser 模块单元测试
"""

from __future__ import annotations

import pandas as pd

import realtime.parser as parser_module


class _FakeTransferEvent:
    """伪造 Transfer 事件解析器。"""

    @staticmethod
    def process_log(raw_log):
        """直接将测试数据包装为解析结果。"""
        return {
            "args": {
                "from": raw_log["mock_from"],
                "to": raw_log["mock_to"],
                "value": raw_log["mock_value"],
            },
            "blockNumber": raw_log["blockNumber"],
            "transactionHash": raw_log["transactionHash"],
            "logIndex": raw_log["logIndex"],
        }


class _FakeEvents:
    """伪造 events 命名空间。"""

    @staticmethod
    def Transfer():
        """返回伪造 Transfer 事件对象。"""
        return _FakeTransferEvent()


class _FakeContract:
    """伪造合约对象。"""

    events = _FakeEvents()


class _FakeTxHash:
    """伪造交易哈希对象。"""

    def __init__(self, value: str):
        self._value = value

    def hex(self):
        """返回十六进制字符串。"""
        return self._value


class _FakeEth:
    """伪造 eth 接口。"""

    @staticmethod
    def get_block(block_number: int):
        """返回固定时间戳区块。"""
        if block_number == 100:
            return {"timestamp": 1_700_000_000}
        return {"timestamp": 1_700_000_100}


class _FakeWeb3:
    """伪造 Web3 客户端。"""

    eth = _FakeEth()


def test_parse_usdc_transfer_logs_basic(monkeypatch):
    """验证解析后字段完整性、单位换算与时间解析。"""
    monkeypatch.setattr(parser_module, "create_usdc_contract", lambda w3, contract_address: _FakeContract())

    raw_logs = [
        {
            "blockNumber": 100,
            "transactionHash": _FakeTxHash("0xabc"),
            "logIndex": 0,
            "mock_from": "0x0000000000000000000000000000000000000001",
            "mock_to": "0x0000000000000000000000000000000000000002",
            "mock_value": 1_500_000,  # 1.5 USDC
            "blockTimestamp": "0x6553f100",
        }
    ]

    df = parser_module.parse_usdc_transfer_logs(
        w3=_FakeWeb3(),
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        raw_logs=raw_logs,
    )

    assert len(df) == 1
    assert df.loc[0, "transaction_hash"] == "0xabc"
    assert df.loc[0, "value_raw"] == 1_500_000
    assert df.loc[0, "value_usdc"] == 1.5
    assert isinstance(df.loc[0, "datetime"], pd.Timestamp)
    assert str(df.loc[0, "datetime"].tz) in {"UTC", "UTC+00:00"}


def test_extract_timestamp_fallback_get_block(monkeypatch):
    """当日志缺失 blockTimestamp 时，回退使用区块时间戳。"""
    monkeypatch.setattr(parser_module, "create_usdc_contract", lambda w3, contract_address: _FakeContract())

    raw_logs = [
        {
            "blockNumber": 100,
            "transactionHash": _FakeTxHash("0xdef"),
            "logIndex": 1,
            "mock_from": "0x0000000000000000000000000000000000000003",
            "mock_to": "0x0000000000000000000000000000000000000004",
            "mock_value": 2_000_000,
        }
    ]

    df = parser_module.parse_usdc_transfer_logs(
        w3=_FakeWeb3(),
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        raw_logs=raw_logs,
    )

    assert len(df) == 1
    assert df.loc[0, "timestamp"] == 1_700_000_000
