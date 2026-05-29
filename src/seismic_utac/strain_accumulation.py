"""Strain energy accumulation model for seismic SOC."""

from __future__ import annotations

import math

from seismic_utac.constants import K_ENERGY, R_LOADING


def energy_released_J(M: float) -> float:
    """Seismic energy in Joules from Kanamori formula."""
    return 10.0 ** (1.5 * M + 4.8)


class StrainAccumulationModel:
    """Model tectonic strain loading and stress release via earthquakes.

    H in [0, 1] represents normalized strain state.
    """

    def __init__(
        self,
        loading_rate: float = R_LOADING,
        k_energy: float = K_ENERGY,
        H_initial: float = 0.5,
    ) -> None:
        self.loading_rate = loading_rate
        self.k_energy = k_energy
        self.H = H_initial
        self._history: list[float] = [H_initial]

    def step(self, dt: float, event_magnitudes: list[float] | None = None) -> float:
        """Advance model by dt years, releasing energy from events.

        Returns new H value.
        """
        released = 0.0
        if event_magnitudes:
            for M in event_magnitudes:
                released += energy_released_J(M) / self.k_energy

        dH = self.loading_rate * dt - released
        self.H = max(0.0, min(1.0, self.H + dH))
        self._history.append(self.H)
        return self.H

    def reset(self, H_initial: float = 0.5) -> None:
        """Reset model to initial state."""
        self.H = H_initial
        self._history = [H_initial]

    def H_star_from_gamma(self, gamma: float) -> float:
        """Compute critical strain threshold from Gamma.

        H* = 1 - exp(-gamma * pi)  (phenomenological mapping)
        """
        return 1.0 - math.exp(-gamma * math.pi)

    def is_critical(self, gamma: float) -> bool:
        """Return True if current H exceeds critical threshold."""
        return self.H >= self.H_star_from_gamma(gamma)

    @property
    def history(self) -> list[float]:
        return list(self._history)
