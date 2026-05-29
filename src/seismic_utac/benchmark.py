"""Benchmark suite for seismic-utac Package 23."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from seismic_utac.aftershock import OmoriUtsu
from seismic_utac.catalog_loader import SeismicCatalogLoader
from seismic_utac.constants import B_SOC_TYPICAL, GAMMA_SEISMIC, GAMMA_SEISMIC_TOL
from seismic_utac.crep_seismic import SeismicCREP
from seismic_utac.gutenberg_richter import GutenbergRichterFitter, b_to_gamma


SEISMIC_TARGETS: dict[str, tuple[float, float]] = {
    "b_value_global": (1.0, 0.10),
    "b_value_swarm_max": (2.5, 0.30),
    "gamma_seismic": (GAMMA_SEISMIC, GAMMA_SEISMIC_TOL),
    "aftershock_omori_p": (1.1, 0.10),
}


@dataclass
class BenchmarkResult:
    target_name: str
    expected: float
    tolerance: float
    actual: float
    passed: bool

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] {self.target_name}: "
            f"expected {self.expected:.3f} ± {self.tolerance:.3f}, "
            f"got {self.actual:.3f}"
        )


def run_benchmark(seed: int = 42) -> dict[str, Any]:
    """Run all benchmark targets and return results dict."""
    rng = np.random.default_rng(seed)
    loader = SeismicCatalogLoader()
    gr_fitter = GutenbergRichterFitter()

    results: list[BenchmarkResult] = []

    # --- b_value_global: synthetic catalog with b=1.0, fit should recover ~1.0 ---
    events_global = loader.load_synthetic(
        n_events=2000, b_value=1.0, M_min=2.5, M_max=8.0,
        duration_years=50.0, seed=seed, region="global"
    )
    mags_global = [e["magnitude"] for e in events_global]
    gr_global = gr_fitter.fit(mags_global, 2.5)
    b_global = gr_global["b_value"]
    exp, tol = SEISMIC_TARGETS["b_value_global"]
    results.append(BenchmarkResult(
        "b_value_global", exp, tol, b_global,
        abs(b_global - exp) <= tol
    ))

    # --- b_value_swarm_max: high-b swarm catalog ---
    events_swarm = loader.load_synthetic(
        n_events=500, b_value=2.5, M_min=2.5, M_max=6.0,
        duration_years=1.0, seed=seed + 1, region="swarm"
    )
    mags_swarm = [e["magnitude"] for e in events_swarm]
    gr_swarm = gr_fitter.fit(mags_swarm, 2.5)
    b_swarm = gr_swarm["b_value"]
    exp, tol = SEISMIC_TARGETS["b_value_swarm_max"]
    results.append(BenchmarkResult(
        "b_value_swarm_max", exp, tol, b_swarm,
        abs(b_swarm - exp) <= tol
    ))

    # --- gamma_seismic: use B_SOC_TYPICAL catalog ---
    events_soc = loader.load_synthetic(
        n_events=2000, b_value=B_SOC_TYPICAL, M_min=2.5, M_max=8.0,
        duration_years=50.0, seed=seed, region="soc"
    )
    mags_soc = [e["magnitude"] for e in events_soc]
    gr_soc = gr_fitter.fit(mags_soc, 2.5)
    gamma = b_to_gamma(gr_soc["b_value"])
    exp, tol = SEISMIC_TARGETS["gamma_seismic"]
    results.append(BenchmarkResult(
        "gamma_seismic", exp, tol, gamma,
        abs(gamma - exp) <= tol
    ))

    # --- aftershock_omori_p: generate synthetic Omori sequence and fit ---
    omori_true = OmoriUtsu(K=50.0, c=0.1, p=1.1)
    t_vals = np.linspace(0.01, 100.0, 200)
    r_vals = omori_true.rate(t_vals)
    noise = rng.normal(0, 0.02 * r_vals)
    r_noisy = np.maximum(r_vals + noise, 1e-6)

    omori_fit = OmoriUtsu()
    fit_result = omori_fit.fit(t_vals, r_noisy)
    p_fitted = fit_result.get("p", omori_true.p)
    exp, tol = SEISMIC_TARGETS["aftershock_omori_p"]
    results.append(BenchmarkResult(
        "aftershock_omori_p", exp, tol, p_fitted,
        abs(p_fitted - exp) <= tol
    ))

    all_passed = all(r.passed for r in results)
    return {
        "results": results,
        "all_passed": all_passed,
        "n_passed": sum(1 for r in results if r.passed),
        "n_total": len(results),
        "summary": {r.target_name: {"actual": r.actual, "passed": r.passed} for r in results},
    }
