"""Omori-Utsu aftershock decay model."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.optimize import curve_fit

from seismic_utac.constants import OMORI_C, OMORI_P


def _omori_rate(t: np.ndarray, K: float, c: float, p: float) -> np.ndarray:
    """Omori-Utsu rate function."""
    return K / (t + c) ** p


class OmoriUtsu:
    """Omori-Utsu aftershock sequence model.

    rate(t) = K / (t + c)^p
    """

    def __init__(
        self,
        K: float = 10.0,
        c: float = OMORI_C,
        p: float = OMORI_P,
    ) -> None:
        self.K = K
        self.c = c
        self.p = p
        self._mainshock_time: float | None = None
        self._mainshock_magnitude: float | None = None

    def rate(self, t: float | np.ndarray) -> float | np.ndarray:
        """Aftershock rate at time t after mainshock."""
        t_arr = np.asarray(t, dtype=float)
        result = self.K / (t_arr + self.c) ** self.p
        if np.ndim(t) == 0:
            return float(result)
        return result

    def cumulative(self, t: float | np.ndarray) -> float | np.ndarray:
        """Cumulative aftershock count from 0 to t.

        For p != 1: integral of K/(t+c)^p dt from 0 to t
        = K / (1-p) * [(t+c)^(1-p) - c^(1-p)]
        """
        t_arr = np.asarray(t, dtype=float)
        p = self.p
        K = self.K
        c = self.c

        if abs(p - 1.0) < 1e-8:
            result = K * (np.log(t_arr + c) - math.log(c))
        else:
            result = K / (1.0 - p) * ((t_arr + c) ** (1.0 - p) - c ** (1.0 - p))

        if np.ndim(t) == 0:
            return float(result)
        return result

    def fit(
        self,
        times: list[float] | np.ndarray,
        rates: list[float] | np.ndarray,
    ) -> dict[str, Any]:
        """Fit Omori-Utsu parameters to observed rate data.

        Parameters
        ----------
        times : array of time values (days after mainshock)
        rates : observed aftershock rates
        """
        t = np.asarray(times, dtype=float)
        r = np.asarray(rates, dtype=float)

        p0 = [self.K, self.c, self.p]
        bounds = ([0.0, 1e-6, 0.5], [1e6, 10.0, 2.0])

        try:
            popt, pcov = curve_fit(_omori_rate, t, r, p0=p0, bounds=bounds, maxfev=10000)
            self.K, self.c, self.p = float(popt[0]), float(popt[1]), float(popt[2])
            perr = np.sqrt(np.diag(pcov))
            return {
                "K": self.K,
                "c": self.c,
                "p": self.p,
                "K_err": float(perr[0]),
                "c_err": float(perr[1]),
                "p_err": float(perr[2]),
                "success": True,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "K": self.K, "c": self.c, "p": self.p}

    def register_mainshock(self, time: float, magnitude: float) -> None:
        """Register a mainshock event."""
        self._mainshock_time = time
        self._mainshock_magnitude = magnitude
        # Scale K with mainshock magnitude (Bath's law)
        self.K = 10.0 ** (magnitude - 4.0)

    @property
    def mainshock_time(self) -> float | None:
        return self._mainshock_time

    @property
    def mainshock_magnitude(self) -> float | None:
        return self._mainshock_magnitude
