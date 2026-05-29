"""Seismic entropy analysis for SOC detection."""

from __future__ import annotations

import itertools
import math
from collections import Counter

import numpy as np


class SeismicEntropyAnalyzer:
    """Compute various entropy measures from seismic magnitude sequences."""

    def permutation_entropy(self, magnitudes: list[float] | np.ndarray, order: int = 3) -> float:
        """Compute normalized permutation entropy of magnitude sequence.

        PE = -sum(p_i * log(p_i)) / log(m!)
        Returns value in [0, 1]. 1 = maximum entropy (random), 0 = ordered.
        """
        mags = np.asarray(magnitudes, dtype=float)
        n = len(mags)
        if n < order:
            return 1.0  # not enough data -> assume max entropy

        # Extract all order-length windows and get their rank permutations
        perms: list[tuple[int, ...]] = []
        for i in range(n - order + 1):
            window = mags[i : i + order]
            ranks = tuple(int(r) for r in np.argsort(np.argsort(window)))
            perms.append(ranks)

        # Count frequencies
        counts = Counter(perms)
        total = len(perms)
        max_entropy = math.log(math.factorial(order))

        pe = 0.0
        for count in counts.values():
            p = count / total
            pe -= p * math.log(p)

        return pe / max_entropy if max_entropy > 0 else 0.0

    def magnitude_distribution_entropy(
        self,
        magnitudes: list[float] | np.ndarray,
        n_bins: int = 20,
    ) -> float:
        """Compute Shannon entropy of magnitude histogram.

        Returns normalized entropy in [0, 1].
        """
        mags = np.asarray(magnitudes, dtype=float)
        if len(mags) == 0:
            return 1.0

        counts, _ = np.histogram(mags, bins=n_bins)
        counts = counts[counts > 0]
        total = counts.sum()
        probs = counts / total
        entropy = -float(np.sum(probs * np.log(probs)))
        max_entropy = math.log(n_bins)
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def information_entropy_decreasing(
        self,
        magnitudes: list[float] | np.ndarray,
        window: int = 50,
        order: int = 3,
    ) -> bool:
        """Return True if permutation entropy shows decreasing trend (ordering).

        Decreasing entropy = system becoming more ordered = approaching criticality.
        """
        mags = np.asarray(magnitudes, dtype=float)
        if len(mags) < 2 * window:
            return False

        # Compare entropy in first vs second half of recent data
        first_half = mags[-2 * window : -window]
        second_half = mags[-window:]

        pe_first = self.permutation_entropy(first_half, order=order)
        pe_second = self.permutation_entropy(second_half, order=order)

        return pe_second < pe_first

    def p_component(self, magnitudes: list[float] | np.ndarray, order: int = 3) -> float:
        """Return P component for CREP: P = 1 - permutation_entropy_normalized."""
        pe = self.permutation_entropy(magnitudes, order=order)
        return 1.0 - pe
