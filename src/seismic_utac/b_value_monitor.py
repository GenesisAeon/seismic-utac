"""Real-time b-value monitoring for seismic SOC detection."""

from __future__ import annotations

import math
from collections import deque

import numpy as np

from seismic_utac.constants import B_CRITICAL, LOG10_E


class BValueMonitor:
    """Monitor evolving b-value from a sliding window of magnitudes."""

    def __init__(self, window_size: int = 100, m_min: float = 2.5) -> None:
        self.window_size = window_size
        self.m_min = m_min
        self._magnitudes: deque[float] = deque(maxlen=window_size)
        self._b_history: list[float] = []

    def update(self, magnitude: float) -> float | None:
        """Add a new magnitude observation and return current b-value if enough data."""
        if magnitude >= self.m_min:
            self._magnitudes.append(magnitude)
        if len(self._magnitudes) < 10:
            return None
        b = self._compute_b()
        self._b_history.append(b)
        return b

    def _compute_b(self) -> float:
        mags = np.array(self._magnitudes)
        mean_m = float(np.mean(mags))
        if mean_m <= self.m_min:
            return float("nan")
        return LOG10_E / (mean_m - self.m_min)

    def current_b(self) -> float | None:
        """Return most recent b-value estimate."""
        if not self._b_history:
            return None
        return self._b_history[-1]

    def b_trend(self, n: int = 10) -> float | None:
        """Return linear trend (slope) of b-value over last n estimates.

        Positive = b increasing (moving away from criticality if b>1).
        Negative = b decreasing (potentially approaching criticality).
        """
        if len(self._b_history) < 2:
            return None
        recent = self._b_history[-n:]
        x = np.arange(len(recent), dtype=float)
        y = np.array(recent)
        if len(x) < 2:
            return None
        coeffs = np.polyfit(x, y, 1)
        return float(coeffs[0])

    def phase_imminent(self, threshold_b: float = B_CRITICAL + 0.2) -> bool:
        """Return True if b-value is dropping toward or below threshold.

        Indicates potential major seismic phase transition.
        """
        b = self.current_b()
        if b is None:
            return False
        trend = self.b_trend()
        # Imminent if b is near threshold or dropping fast
        near = b <= threshold_b
        dropping = trend is not None and trend < -0.01
        return near or dropping

    @property
    def b_history(self) -> list[float]:
        return list(self._b_history)
