"""
Pure-Python financial calculations. The agent calls these instead of
letting the LLM do arithmetic, so the numbers are always exact.
"""
from typing import Optional


def growth_rate(old_value: float, new_value: float) -> float:
    """Percentage growth between two values."""
    if old_value == 0:
        raise ValueError("old_value cannot be zero.")
    return round((new_value - old_value) / old_value * 100, 2)


def profit_margin(revenue: float, profit: float) -> float:
    """Net profit margin, as a percentage of revenue."""
    if revenue == 0:
        raise ValueError("revenue cannot be zero.")
    return round(profit / revenue * 100, 2)


def cagr(begin_value: float, end_value: float, years: int) -> float:
    """Compound annual growth rate, as a percentage."""
    if begin_value <= 0 or years <= 0:
        raise ValueError("begin_value and years must be positive.")
    return round(((end_value / begin_value) ** (1 / years) - 1) * 100, 2)


def debt_ratio(liabilities: float, assets: float) -> float:
    """Total liabilities / total assets."""
    if assets == 0:
        raise ValueError("assets cannot be zero.")
    return round(liabilities / assets, 3)


def current_ratio(assets: float, liabilities: float) -> float:
    """Simple assets / liabilities ratio (a proxy when current-only
    asset/liability figures aren't available)."""
    if liabilities == 0:
        raise ValueError("liabilities cannot be zero.")
    return round(assets / liabilities, 3)


def roi(gain: float, cost: float) -> float:
    """Return on investment, as a percentage."""
    if cost == 0:
        raise ValueError("cost cannot be zero.")
    return round((gain - cost) / cost * 100, 2)


CALCULATIONS = {
    "growth_rate": growth_rate,
    "profit_margin": profit_margin,
    "cagr": cagr,
    "debt_ratio": debt_ratio,
    "current_ratio": current_ratio,
    "roi": roi,
}


def run_calculation(name: str, **kwargs) -> Optional[float]:
    if name not in CALCULATIONS:
        raise ValueError(f"Unknown calculation '{name}'. Options: {list(CALCULATIONS)}")
    return CALCULATIONS[name](**kwargs)
