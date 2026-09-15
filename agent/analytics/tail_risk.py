"""Tail risk analytics: Historical Value at Risk (VaR) and Conditional VaR (Expected Shortfall).

Mathematical Formulas & Sign Convention:
1. Historical Value at Risk (VaR):
   Given daily simple returns R_1, ..., R_N and confidence level c (e.g. c = 0.95):
   Let \\alpha = 1 - c (e.g. \\alpha = 0.05 for 95% confidence).
   Let q_\\alpha = \\text{Quantile}(R, \\alpha) be the lower \\alpha-quantile of returns.

   Sign Convention:
   VaR is represented as a POSITIVE LOSS MAGNITUDE:
     VaR_c = - q_\\alpha = - \\text{Quantile}(R, 1 - c)
   Example: If the 5th percentile return is -0.025 (-2.5%), VaR_0.95 = +0.025 (+2.5%).

2. Historical Conditional VaR (CVaR / Expected Shortfall):
   CVaR is the expected loss given that loss exceeds the VaR threshold:
     CVaR_c = - \\mathbb{E}[ R \\mid R \\le -VaR_c ] = - \\frac{1}{K} \\sum_{R_i \\le q_\\alpha} R_i
   Follows the identical positive loss convention as VaR (CVaR >= VaR).
"""

from typing import Optional
import numpy as np
import pandas as pd

from agent.analytics.types import TailRiskMetrics


def calculate_historical_var(
    returns: pd.Series,
    confidence_level: float = 0.95,
) -> Optional[float]:
    """Calculate historical Value at Risk (VaR) as a positive loss magnitude.

    Parameters:
        returns: pd.Series of daily simple returns.
        confidence_level: Confidence level in (0.0, 1.0), typically 0.95 or 0.99.

    Returns:
        VaR as a positive float representing percentage loss magnitude (e.g. 0.025 for 2.5%),
        or None if insufficient data or invalid confidence level.
    """
    if returns is None or returns.empty:
        return None

    if not (0.0 < confidence_level < 1.0):
        return None

    clean = returns.dropna()
    if len(clean) < 2:
        return None

    alpha = 1.0 - confidence_level
    # Use standard linear quantile interpolation
    quantile_val = float(clean.quantile(alpha, interpolation="linear"))

    if np.isnan(quantile_val):
        return None

    # Positive loss convention: loss magnitude = -quantile
    var = -quantile_val
    return float(var)


def calculate_historical_cvar(
    returns: pd.Series,
    confidence_level: float = 0.95,
) -> Optional[float]:
    """Calculate historical Conditional VaR (CVaR / Expected Shortfall).

    Represents the expected loss magnitude in the worst (1 - confidence_level) tail.

    Parameters:
        returns: pd.Series of daily simple returns.
        confidence_level: Confidence level in (0.0, 1.0), typically 0.95 or 0.99.

    Returns:
        CVaR as a positive float representing percentage loss magnitude (e.g. 0.038 for 3.8%),
        or None if insufficient data or invalid confidence level.
    """
    if returns is None or returns.empty:
        return None

    if not (0.0 < confidence_level < 1.0):
        return None

    clean = returns.dropna()
    if len(clean) < 2:
        return None

    alpha = 1.0 - confidence_level
    quantile_val = float(clean.quantile(alpha, interpolation="linear"))

    if np.isnan(quantile_val):
        return None

    # Tail includes all returns at or below the quantile threshold
    tail = clean[clean <= quantile_val]
    if tail.empty:
        # Fallback to closest observation
        tail = clean.nsmallest(max(1, int(np.ceil(alpha * len(clean)))))

    expected_shortfall = float(tail.mean())
    if np.isnan(expected_shortfall):
        return None

    # Positive loss convention: loss magnitude = -expected_shortfall
    cvar = -expected_shortfall
    return float(cvar)


def compute_tail_risk_metrics(
    returns: pd.Series,
    custom_confidence: float = 0.99,
) -> TailRiskMetrics:
    """Compute standard 95% and custom confidence VaR and CVaR tail metrics.

    Parameters:
        returns: pd.Series of daily simple returns.
        custom_confidence: Custom confidence level (default 0.99).

    Returns:
        TailRiskMetrics dataclass.
    """
    clean = returns.dropna() if returns is not None else pd.Series(dtype=float)
    n = len(clean)

    var_95 = calculate_historical_var(clean, confidence_level=0.95)
    cvar_95 = calculate_historical_cvar(clean, confidence_level=0.95)

    var_custom = calculate_historical_var(clean, confidence_level=custom_confidence)
    cvar_custom = calculate_historical_cvar(clean, confidence_level=custom_confidence)

    return TailRiskMetrics(
        var_95=var_95,
        cvar_95=cvar_95,
        confidence_level=custom_confidence,
        var_custom=var_custom,
        cvar_custom=cvar_custom,
        total_observations=n,
    )
