"""
策略设置函数

提供各种策略配置功能
"""

from dataclasses import dataclass
from datetime import date as Date
from typing import Optional, Dict, Any, Iterable


@dataclass
class OrderCost:
    """
    交易费用设置（标准回测 R1）

    Attributes:
        open_tax: 买入印花税（A股通常 0）
        close_tax: 卖出印花税；<0 表示按交易日自动切档
            （2023-08-28 前 0.001，之后 0.0005；财政部/税务总局公告2023年第39号）
        open_commission / close_commission: 券商佣金（默认万三，全佣口径含经手费+证管费）
        min_commission: 最小佣金
        transfer_fee_rate: 过户费费率；<0 表示按日自动
            （2022-04-29 起 0.00001 双边；中国结算）
        transfer_fee_bilateral: 过户费是否双边收取
        commission_includes_regulatory: True=全佣（不再另加经手/证管）
        fee_schedule_id: 费用表版本号
        close_today_commission: 平今佣金（期货用）
        commission_type: 佣金计费方式（兼容聚宽，默认 by_money）
    """
    open_tax: float = 0.0
    close_tax: float = -1.0  # <0 = date-aware stamp tax
    open_commission: float = 0.0003
    close_commission: float = 0.0003
    min_commission: float = 5.0
    transfer_fee_rate: float = -1.0  # <0 = date-aware
    transfer_fee_bilateral: bool = True
    commission_includes_regulatory: bool = True
    fee_schedule_id: str = "CN_A_SHARE_FEE_R1_20230828"
    close_today_commission: float = 0.0
    commission_type: str = "by_money"

    def resolve_close_tax(self, asof=None) -> float:
        from .match_guardrails_r1 import stamp_tax_rate

        if self.close_tax is not None and self.close_tax >= 0:
            return float(self.close_tax)
        return stamp_tax_rate(asof)

    def resolve_transfer_fee_rate(self, asof=None) -> float:
        from .match_guardrails_r1 import transfer_fee_rate

        if self.transfer_fee_rate is not None and self.transfer_fee_rate >= 0:
            return float(self.transfer_fee_rate)
        return transfer_fee_rate(asof)

    def calculate_tax(self, amount: float, is_buy: bool, asof=None) -> float:
        if is_buy:
            return amount * self.open_tax
        return amount * self.resolve_close_tax(asof)

    def calculate_commission(self, amount: float, is_buy: bool) -> float:
        if is_buy:
            commission = amount * self.open_commission
        else:
            commission = amount * self.close_commission
        return max(commission, self.min_commission)

    def calculate_transfer_fee(self, amount: float, asof=None) -> float:
        return abs(float(amount)) * self.resolve_transfer_fee_rate(asof)

    def effective_cost_estimate(self, amount: float, is_buy: bool, asof=None) -> dict:
        from .match_guardrails_r1 import effective_cost_estimate as _est

        return _est(
            amount,
            is_buy,
            asof=asof,
            open_commission=self.open_commission,
            close_commission=self.close_commission,
            min_commission=self.min_commission,
            close_tax_override=self.close_tax if self.close_tax >= 0 else None,
            transfer_fee_override=self.transfer_fee_rate if self.transfer_fee_rate >= 0 else None,
            apply_transfer_fee=True,
        )


def _default_order_costs() -> Dict[str, OrderCost]:
    """返回各资产类别的默认费用配置（标准回测 R1）。"""
    return {
        "stock": OrderCost(
            open_tax=0.0,
            close_tax=-1.0,  # date-aware 0.001 → 0.0005
            open_commission=0.0003,
            close_commission=0.0003,
            min_commission=5.0,
            transfer_fee_rate=-1.0,
            fee_schedule_id="CN_A_SHARE_FEE_R1_20230828",
        ),
        "fund": OrderCost(
            open_tax=0.0,
            close_tax=0.0,
            open_commission=0.0003,
            close_commission=0.0003,
            min_commission=5.0,
            transfer_fee_rate=0.0,  # ETF/场内基金默认不计股票过户费
            fee_schedule_id="CN_A_SHARE_FEE_R1_20230828",
        ),
        "money_market_fund": OrderCost(
            open_tax=0.0,
            close_tax=0.0,
            open_commission=0.0,
            close_commission=0.0,
            min_commission=0.0,
            transfer_fee_rate=0.0,
            fee_schedule_id="CN_A_SHARE_FEE_R1_20230828",
        ),
    }


@dataclass
class FixedSlippage:
    """
    固定滑点
    
    Attributes:
        value: 滑点绝对值（单边，元）
    """
    value: float = 0.0
    
    def calculate_slippage(self, price: float, is_buy: bool) -> float:
        """
        计算滑点后的价格
        
        Args:
            price: 原始价格
            is_buy: 是否买入
            
        Returns:
            滑点后的价格
        """
        # 模拟价差的一半落到单边（行业通用写法）
        half = self.value / 2.0
        return price + half if is_buy else price - half

    @property
    def ratio(self) -> float:
        """兼容旧有按比例用法，便于序列化；绝对滑点使用 value。"""
        return self.value

    def to_dict(self) -> Dict[str, Any]:
        return {'type': 'fixed', 'value': self.value}


@dataclass
class PriceRelatedSlippage:
    """按比例滑点（聚宽语义）。"""
    ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {'type': 'price_related', 'ratio': float(self.ratio)}


@dataclass
class StepRelatedSlippage:
    """按跳数滑点（聚宽语义，按 tick 步长计算绝对价差）。"""
    steps: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {'type': 'step_related', 'steps': int(self.steps)}


@dataclass
class PerTrade:
    """聚宽兼容：按买入/卖出费率和最小佣金设置股票费用。"""
    buy_cost: float = 0.0003
    sell_cost: float = 0.0013
    min_cost: float = 5.0


class StrategySettings:
    """策略设置管理器"""
    
    def __init__(self):
        self.benchmark: Optional[str] = None  # 基准
        self.order_cost: Dict[str, OrderCost] = _default_order_costs()  # 不同类型的交易费用
        self.slippage: Optional[FixedSlippage] = None  # 滑点
        self.slippage_map: Dict[str, Any] = {}  # 兼容聚宽的新滑点配置
        self.order_cost_overrides: Dict[str, OrderCost] = {}  # 代码级费用覆盖
        self.options: Dict[str, Any] = {
            # STANDARD_BACKTEST_R1 defaults (HAND causal-aligned)
            "use_real_price": True,
            "avoid_future_data": True,
            "order_volume_ratio": 0.05,
            "order_match_mode": "bar_end",  # avoid immediate same-bar fill
            "exec_price_policy": "next_bar_open",
            "match_by_signal": False,
            "reject_missing_bar_volume": True,
            "reject_limit_bound_fills": True,
            "allow_synthetic_limit_fallback": False,
            "impact_k": 0.0,  # disabled until live calibration
            "fq_ref_date": Date.today(),
        }

    def reset(self):
        """重置所有设置"""
        self.benchmark = None
        self.order_cost = _default_order_costs()
        self.slippage = None
        self.slippage_map = {}
        self.order_cost_overrides = {}
        self.options = {
            "use_real_price": True,
            "avoid_future_data": True,
            "order_volume_ratio": 0.05,
            "order_match_mode": "bar_end",
            "exec_price_policy": "next_bar_open",
            "match_by_signal": False,
            "reject_missing_bar_volume": True,
            "reject_limit_bound_fills": True,
            "allow_synthetic_limit_fallback": False,
            "impact_k": 0.0,
            "fq_ref_date": Date.today(),
        }


# 全局设置实例
_settings = StrategySettings()


def set_benchmark(security: str):
    """
    设置基准
    
    Args:
        security: 基准标的代码，如 '000300.XSHG'（沪深300）
    """
    _settings.benchmark = security


def set_order_cost(order_cost: OrderCost, type: str = 'stock', ref: Optional[str] = None):
    """
    设置交易费用
    
    Args:
        order_cost: OrderCost对象
        type: 交易类型（'stock', 'fund', 'futures'等）
        ref: 代码级覆盖（如 '601318.XSHG'）
    """
    if ref:
        _settings.order_cost_overrides[f'{type}_{ref}'] = order_cost
    else:
        _settings.order_cost[type] = order_cost


def set_commission(per_trade: PerTrade):
    """
    兼容聚宽：按买卖费率设置股票手续费（印花税为0）。
    """
    cost = OrderCost(
        open_tax=0,
        close_tax=0,
        open_commission=per_trade.buy_cost,
        close_commission=per_trade.sell_cost,
        min_commission=per_trade.min_cost,
        commission_type='by_money',
    )
    set_order_cost(cost, type='stock')


def set_universe(stocks: Iterable[str]):
    """
    兼容聚宽：设置策略标的池。
    """
    if isinstance(stocks, str):
        universe = (stocks,)
    else:
        universe = tuple(stocks)
    _settings.options['universe'] = universe


def _normalize_slippage_keys(type: Optional[str], ref: Optional[str]) -> Iterable[str]:
    """
    生成与聚宽一致的滑点键。
    """
    keys = []
    if type:
        type = type.lower()
    if type in ('lof', 'fjm', 'fjb', 'fja', 'etf', 'mmf'):
        type = 'fund'

    if type == 'index_futures':
        if ref:
            keys.append(f'futures_{ref}')
        else:
            keys.extend(['futures_IF', 'futures_IH', 'futures_IC'])
    elif type == 'futures':
        if ref:
            keys.append(f'{type}_{ref}')
        else:
            keys.extend([type, 'futures_IF', 'futures_IH', 'futures_IC'])
    elif type in ('fund', 'stock'):
        if ref:
            keys.append(f'{type}_{ref}')
        else:
            keys.append(type)
    else:
        if ref:
            keys.append(ref)
        else:
            keys.append('all')
    return keys


def set_slippage(slippage: Any, type: Optional[str] = None, ref: Optional[str] = None):
    """
    设置滑点
    
    Args:
        slippage: FixedSlippage/PriceRelatedSlippage/StepRelatedSlippage对象
        type: 交易类型（'stock', 'fund', 'futures'等）
        ref: 具体代码或期货前缀，如 'IF'、'RB1809.XSGE'
    """
    if not isinstance(slippage, (FixedSlippage, PriceRelatedSlippage, StepRelatedSlippage)):
        raise TypeError("slippage 必须是 FixedSlippage/PriceRelatedSlippage/StepRelatedSlippage")

    _settings.slippage = slippage
    keys = list(_normalize_slippage_keys(type, ref))
    for key in keys:
        _settings.slippage_map[key] = slippage


def set_option(key: str, value: Any):
    """
    设置选项
    
    Args:
        key: 选项名称
            - 'use_real_price': 是否使用真实价格（动态复权）
            - 'avoid_future_data': 是否避免未来数据
            - 'force_no_engine': 是否强制不使用数据源引擎
            - 'order_volume_ratio': 成交量比例
            - 'order_match_mode': 下单撮合模式（'bar_end'|'immediate'）
            - 'match_by_signal': 限价资金检查使用信号价(True)或撮合价(False)
            - 'fq_ref_date': 前复权参考日期（datetime.date）
        value: 选项值
    """
    _settings.options[key] = value


def get_settings() -> StrategySettings:
    """获取设置实例"""
    return _settings


def reset_settings():
    """重置所有设置"""
    _settings.reset()


__all__ = [
    'OrderCost', 'PerTrade',
    'FixedSlippage', 'PriceRelatedSlippage', 'StepRelatedSlippage',
    'set_benchmark', 'set_order_cost', 'set_commission', 'set_universe', 'set_slippage', 'set_option',
    'get_settings', 'reset_settings'
]
