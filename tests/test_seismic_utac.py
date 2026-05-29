"""Tests for seismic-utac Package 23."""

from __future__ import annotations

import math

import numpy as np
import pytest

from seismic_utac.aftershock import OmoriUtsu
from seismic_utac.b_value_monitor import BValueMonitor
from seismic_utac.benchmark import run_benchmark
from seismic_utac.catalog_loader import SeismicCatalogLoader
from seismic_utac.constants import GAMMA_SEISMIC, GAMMA_SEISMIC_TOL
from seismic_utac.entropy_seismic import SeismicEntropyAnalyzer
from seismic_utac.gutenberg_richter import GutenbergRichterFitter, b_to_gamma
from seismic_utac.strain_accumulation import StrainAccumulationModel
from seismic_utac.system import SeismicUTAC

# ---------------------------------------------------------------------------
# GR b-value
# ---------------------------------------------------------------------------

def test_gr_fitter_b_value() -> None:
    """Synthetic catalog with b=1.0 should recover b ≈ 1.0 ± 0.1."""
    rng = np.random.default_rng(42)
    b_true = 1.0
    M_min = 2.5
    n = 2000
    U = rng.uniform(0.0, 1.0, size=n)
    mags = M_min - np.log(U) / (b_true * math.log(10))
    mags = np.clip(mags, M_min, 8.0)

    fitter = GutenbergRichterFitter()
    result = fitter.fit(mags.tolist(), M_min)
    b_fitted = result["b_value"]
    assert abs(b_fitted - b_true) <= 0.10, f"b={b_fitted:.3f} not within 0.10 of {b_true}"


def test_gr_fitter_raises_on_empty() -> None:
    fitter = GutenbergRichterFitter()
    with pytest.raises(ValueError):
        fitter.fit([], 2.5)


# ---------------------------------------------------------------------------
# Strain accumulation
# ---------------------------------------------------------------------------

def test_strain_accumulation_stays_in_bounds() -> None:
    """H must stay in [0, 1] regardless of input."""
    model = StrainAccumulationModel(loading_rate=0.05)
    rng = np.random.default_rng(7)
    for _ in range(200):
        magnitudes = rng.uniform(2.5, 7.0, size=rng.integers(0, 10)).tolist()
        model.step(0.5, magnitudes)
        assert 0.0 <= model.H <= 1.0


# ---------------------------------------------------------------------------
# CREP Gamma target
# ---------------------------------------------------------------------------

def test_crep_gamma_target() -> None:
    """b_to_gamma at B_SOC_TYPICAL (1.7) should give Gamma ≈ 0.200 ± 0.03."""
    from seismic_utac.constants import B_SOC_TYPICAL
    gamma = b_to_gamma(B_SOC_TYPICAL)
    assert abs(gamma - GAMMA_SEISMIC) <= GAMMA_SEISMIC_TOL, (
        f"Gamma={gamma:.4f} not within {GAMMA_SEISMIC_TOL} of {GAMMA_SEISMIC}"
    )


def test_b_to_gamma_monotone() -> None:
    """Gamma should increase with b above 1.0."""
    gammas = [b_to_gamma(b) for b in [1.1, 1.3, 1.5, 1.7, 2.0, 2.5]]
    assert all(g2 > g1 for g1, g2 in zip(gammas, gammas[1:], strict=False))


# ---------------------------------------------------------------------------
# Diamond interface
# ---------------------------------------------------------------------------

def test_diamond_interface() -> None:
    """SeismicUTAC must have all 5 required Diamond contract methods."""
    required = [
        "run_cycle", "get_crep_state", "get_utac_state", "get_phase_events", "to_zenodo_record",
    ]
    system = SeismicUTAC()
    for method in required:
        assert hasattr(system, method), f"Missing Diamond method: {method}"
        assert callable(getattr(system, method))


def test_diamond_run_cycle_returns_dict() -> None:
    system = SeismicUTAC()
    result = system.run_cycle(duration_years=5.0, seed=42)
    assert isinstance(result, dict)
    for key in ("gamma", "b_value", "H", "H_star", "phase_events"):
        assert key in result, f"Missing key: {key}"


def test_get_crep_state_after_run() -> None:
    system = SeismicUTAC()
    system.run_cycle(duration_years=5.0, seed=42)
    state = system.get_crep_state()
    assert "Gamma" in state
    assert 0.0 < state["Gamma"] < 1.0


def test_get_utac_state() -> None:
    system = SeismicUTAC()
    system.run_cycle(duration_years=5.0)
    utac = system.get_utac_state()
    assert "H" in utac and "H_star" in utac and "K_eff" in utac


def test_to_zenodo_record() -> None:
    system = SeismicUTAC()
    system.run_cycle(duration_years=2.0)
    rec = system.to_zenodo_record()
    assert rec["package_id"] == 23
    assert "crep_state" in rec
    assert "generated_at" in rec


# ---------------------------------------------------------------------------
# Benchmark suite
# ---------------------------------------------------------------------------

def test_benchmark_passes() -> None:
    """All SEISMIC_TARGETS benchmarks must pass."""
    result = run_benchmark(seed=42)
    for r in result["results"]:
        assert r.passed, str(r)


# ---------------------------------------------------------------------------
# Omori-Utsu
# ---------------------------------------------------------------------------

def test_omori_utsu_p() -> None:
    """Fit synthetic Omori sequence and recover p ≈ 1.1 ± 0.1."""
    omori_true = OmoriUtsu(K=50.0, c=0.1, p=1.1)
    t = np.linspace(0.01, 100.0, 200)
    rates = omori_true.rate(t)

    omori_fit = OmoriUtsu()
    fit = omori_fit.fit(t, rates)
    assert fit["success"], f"Fit failed: {fit.get('error')}"
    assert abs(fit["p"] - 1.1) <= 0.10, f"p={fit['p']:.3f} not within 0.10 of 1.1"


def test_omori_cumulative_positive() -> None:
    omori = OmoriUtsu(K=10.0, c=0.1, p=1.1)
    assert omori.cumulative(10.0) > omori.cumulative(1.0)


# ---------------------------------------------------------------------------
# Predict probability
# ---------------------------------------------------------------------------

def test_predict_probability_in_range() -> None:
    """Predicted probability must be in [0, 1]."""
    system = SeismicUTAC()
    system.run_cycle(duration_years=5.0)
    for mag in [5.0, 6.5, 7.5, 8.0]:
        p = system.predict_major_event_probability(magnitude=mag, horizon_days=365.0)
        assert 0.0 <= p <= 1.0, f"p={p} out of [0,1] for M={mag}"


# ---------------------------------------------------------------------------
# Additional coverage
# ---------------------------------------------------------------------------

def test_catalog_loader_synthetic() -> None:
    loader = SeismicCatalogLoader()
    events = loader.load_synthetic(n_events=100, b_value=1.0, seed=42)
    assert len(events) == 100
    for e in events:
        assert "magnitude" in e and "time" in e


def test_b_value_monitor() -> None:
    monitor = BValueMonitor(window_size=50)
    rng = np.random.default_rng(42)
    mags = rng.uniform(2.5, 6.0, size=200)
    for m in mags:
        monitor.update(float(m))
    assert monitor.current_b() is not None
    assert monitor.current_b() > 0


def test_entropy_analyzer() -> None:
    analyzer = SeismicEntropyAnalyzer()
    rng = np.random.default_rng(0)
    mags = rng.uniform(2.5, 5.0, size=100).tolist()
    pe = analyzer.permutation_entropy(mags, order=3)
    assert 0.0 <= pe <= 1.0
    p_comp = analyzer.p_component(mags)
    assert 0.0 <= p_comp <= 1.0
