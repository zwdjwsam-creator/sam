"""
聚宽新规 A 股分钟 K 线时钟标签（JQ R1A）。

本模块只负责 clock label / scheduler trigger 对齐，不涉及：
- DataProvider 数据可见性
- 上一分钟 bar 数据 lag
- 撮合状态机

规则依据：JQ 官方新规（新建 文本文档 (2).txt）— 240 根分钟 K：
  上午 09:31–11:30（含），下午 13:01–15:00（含）；不含 09:30、午休 12:00–13:00。
"""

from __future__ import annotations

from datetime import date, datetime, time as Time, timedelta
from typing import List, Tuple

# 日频 handle_data 默认触发时刻（聚宽新规首条数据 09:31）
JQ_DAY_HANDLE_TIME = Time(9, 31)

# 分钟 K 线标签边界
JQ_MORNING_FIRST = Time(9, 31)
JQ_MORNING_LAST = Time(11, 30)
JQ_AFTERNOON_FIRST = Time(13, 1)
JQ_AFTERNOON_LAST = Time(15, 0)

JQ_MINUTE_LABEL_COUNT = 240


def iter_jq_minute_datetimes(target_date: date) -> List[datetime]:
    """生成单个交易日的 240 个聚宽分钟 clock 标签（datetime，秒=0）。"""
    labels: List[datetime] = []

    current = datetime.combine(target_date, JQ_MORNING_FIRST)
    morning_end = datetime.combine(target_date, JQ_MORNING_LAST)
    while current <= morning_end:
        labels.append(current)
        current += timedelta(minutes=1)

    current = datetime.combine(target_date, JQ_AFTERNOON_FIRST)
    afternoon_end = datetime.combine(target_date, JQ_AFTERNOON_LAST)
    while current <= afternoon_end:
        labels.append(current)
        current += timedelta(minutes=1)

    return labels


def iter_jq_minute_times(target_date: date) -> List[Time]:
    """返回分钟标签的 time 部分列表。"""
    return [dt.time() for dt in iter_jq_minute_datetimes(target_date)]


def jq_day_handle_datetime(target_date: date) -> datetime:
    """日频 handle_data 默认触发 datetime（09:31:00）。"""
    return datetime.combine(target_date, JQ_DAY_HANDLE_TIME)


def is_jq_minute_label(dt: datetime) -> bool:
    """判断 datetime 是否为聚宽有效分钟标签时刻。"""
    if dt.second != 0 or dt.microsecond != 0:
        return False
    t = dt.time()
    if JQ_MORNING_FIRST <= t <= JQ_MORNING_LAST:
        return True
    if JQ_AFTERNOON_FIRST <= t <= JQ_AFTERNOON_LAST:
        return True
    return False


def validate_jq_minute_window(target_date: date) -> Tuple[bool, List[str]]:
    """
    静态校验分钟窗口；返回 (passed, error_messages)。
    供报告目录验证脚本调用，不连接数据。
    """
    labels = iter_jq_minute_times(target_date)
    errors: List[str] = []
    label_set = set(labels)

    first = labels[0] if labels else None
    last = labels[-1] if labels else None
    if len(labels) != JQ_MINUTE_LABEL_COUNT:
        errors.append(f"count={len(labels)} expected={JQ_MINUTE_LABEL_COUNT}")
    if first != JQ_MORNING_FIRST:
        errors.append(f"first={first} expected={JQ_MORNING_FIRST}")
    if last != JQ_AFTERNOON_LAST:
        errors.append(f"last={last} expected={JQ_AFTERNOON_LAST}")
    if Time(9, 30) in label_set:
        errors.append("09:30 must not be included")
    if JQ_MORNING_LAST not in label_set:
        errors.append("11:30 must be included")
    if JQ_AFTERNOON_FIRST not in label_set:
        errors.append("13:01 must be included")
    if JQ_AFTERNOON_LAST not in label_set:
        errors.append("15:00 must be included")
    if Time(12, 0) in label_set:
        errors.append("12:00 must not be included (noon break)")
    if Time(13, 0) in label_set:
        errors.append("13:00 must not be included (afternoon starts 13:01)")

    return (len(errors) == 0, errors)


__all__ = [
    "JQ_DAY_HANDLE_TIME",
    "JQ_MORNING_FIRST",
    "JQ_MORNING_LAST",
    "JQ_AFTERNOON_FIRST",
    "JQ_AFTERNOON_LAST",
    "JQ_MINUTE_LABEL_COUNT",
    "iter_jq_minute_datetimes",
    "iter_jq_minute_times",
    "jq_day_handle_datetime",
    "is_jq_minute_label",
    "validate_jq_minute_window",
]
