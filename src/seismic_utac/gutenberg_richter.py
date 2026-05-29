"""Gutenberg-Richter law implementation and b-value utilities."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from numpy.random import Generator

from seismic_utac.constants import B_CRITICAL, B_MAX, LOG10_E, SIGMA


def b_to_gamma(b: float) -> float:
    """Convert b-value to CREP Gamma using arctanh formula.

    gamma = arctanh(1 - 1/b) / SIGMA  for b > 1
    """
    if b <= 1.0:
        return 0.0
    eta = 1.0 - 1.0 / b
    # clip to avoid arctanh domain issues
    eta = min(eta, 0.9999)
    return math.atanh(eta) / SIGMA


def crep_r_component(b: float) -> float:
    """Compute R component of CREP from b-value."""
    return 1.0 - abs(b - B_CRITICAL) / B_MAX


def generate_gr_magnitudes(
    n: int,
    b: float,
    M_min: float,
    M_max: float,
    rng: Generator,
) -> np.ndarray:
    """Generate magnitudes from Gutenberg-Richter distribution via inverse CDF.

    M = M_min - ln(U) / (b * ln(10))  where U ~ Uniform(0,1)
    Clipped to [M_min, M_max].
    """
    U = rng.uniform(0.0, 1.0, size=n)
    # avoid log(0)
    U = np.clip(U, 1e-15, 1.0)
    M = M_min - np.log(U) / (b * math.log(10))
    return np.clip(M, M_min, M_max)


class GutenbergRichterFitter:
    """Fit Gutenberg-Richter b-value via Maximum Likelihood Estimation."""

    def fit(self, magnitudes: list[float] | np.ndarray, m_min: float) -> dict[str, Any]:
        """Fit b-value using MLE.

        b = log10(e) / (mean(M) - M_min)
        """
        mags = np.asarray(magnitudes, dtype=float)
        mags = mags[mags >= m_min]
        if len(mags) == 0:
            raise ValueError("No magnitudes at or above m_min")

        mean_m = float(np.mean(mags))
        if mean_m <= m_min:
            raise ValueError("Mean magnitude must exceed m_min")

        b = LOG10_E / (mean_m - m_min)
        n = len(mags)
        # Standard uncertainty: sigma_b = b / sqrt(n)
        b_uncertainty = b / math.sqrt(n)

        return {
            "b_value": b,
            "b_uncertainty": b_uncertainty,
            "n_events": n,
            "mean_magnitude": mean_m,
            "m_min": m_min,
            "a_value": math.log10(n) + b * m_min,
        }


def kappa_gr_pdf(M: float, b: float, M_min: float, kappa: float = 0.5) -> float:
    """Kaniadakis-modified GR PDF.

    Standard GR: p(M) = b * ln(10) * 10^(-b*(M-M_min))
    Kaniadakis modification replaces exponential with kappa-exponential.
    For kappa->0 recovers standard GR.
    """
    beta = b * math.log(10)
    x = beta * (M - M_min)
    if kappa == 0.0:
        return beta * math.exp(-x)
    # kappa-exponential: exp_kappa(x) = (sqrt(1 + kappa^2 * x^2) + kappa*x)^(1/kappa)
    # kappa-PDF normalization differs; we use the standard form here
    exp_k = math.pow(math.sqrt(1.0 + kappa**2 * x**2) + kappa * x, 1.0 / kappa)
    # Normalization constant (approximate for small kappa)
    norm = beta  # approximation valid for small kappa
    return norm * math.exp(-x) * math.pow(exp_k / math.exp(x), 0.5)
