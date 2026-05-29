"""CREP (Criticality-Readiness-Energy-Permutation) seismic implementation."""

from __future__ import annotations

import numpy as np

from seismic_utac.entropy_seismic import SeismicEntropyAnalyzer
from seismic_utac.gutenberg_richter import GutenbergRichterFitter, b_to_gamma, crep_r_component


class SeismicCREP:
    """Compute CREP state vector for seismic SOC assessment.

    Gamma is the primary output using b_to_gamma(b_value).
    C, R, E, P components are computed separately.
    """

    def __init__(
        self,
        spatial_correlation: float = 0.8,
        avalanche_quality: float = 0.85,
        m_min: float = 2.5,
    ) -> None:
        self.spatial_correlation = spatial_correlation
        self.avalanche_quality = avalanche_quality
        self.m_min = m_min
        self._entropy = SeismicEntropyAnalyzer()
        self._gr_fitter = GutenbergRichterFitter()

    def compute(
        self,
        magnitudes: list[float] | np.ndarray,
        b_value: float | None = None,
    ) -> dict[str, float]:
        """Compute CREP state from magnitude sequence.

        Returns dict with keys: C, R, E, P, eta, Gamma, b_value.

        Gamma uses b_to_gamma(b_value) as primary formula.
        eta uses (C*R*E*P)^0.25 for reference.
        """
        mags = np.asarray(magnitudes, dtype=float)

        # Fit b-value if not provided
        if b_value is None:
            try:
                result = self._gr_fitter.fit(mags, self.m_min)
                b_value = result["b_value"]
            except ValueError:
                b_value = 1.0

        # C: spatial correlation (input parameter)
        C = self.spatial_correlation

        # R: from b-value
        R = crep_r_component(b_value)

        # E: avalanche quality (input parameter)
        E = self.avalanche_quality

        # P: from permutation entropy
        P = self._entropy.p_component(mags, order=3)

        # eta: geometric mean of components
        product = C * R * E * P
        eta = product**0.25 if product > 0 else 0.0

        # Gamma: primary formula from b-value
        Gamma = b_to_gamma(b_value)

        return {
            "C": C,
            "R": R,
            "E": E,
            "P": P,
            "eta": eta,
            "Gamma": Gamma,
            "b_value": b_value,
        }
