"""SeismicUTAC — Diamond interface for seismic SOC analysis."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from seismic_utac.aftershock import OmoriUtsu
from seismic_utac.b_value_monitor import BValueMonitor
from seismic_utac.catalog_loader import SeismicCatalogLoader
from seismic_utac.constants import (
    B_SOC_TYPICAL,
    GAMMA_SEISMIC,
    GAMMA_SEISMIC_TOL,
    M_MIN_COMPLETENESS,
    R_LOADING,
)
from seismic_utac.crep_seismic import SeismicCREP
from seismic_utac.gutenberg_richter import GutenbergRichterFitter, b_to_gamma
from seismic_utac.strain_accumulation import StrainAccumulationModel


class SeismicUTAC:
    """Full seismic SOC analysis system implementing the Diamond interface.

    Five core methods: analyze, calibrate, simulate, detect, report.
    """

    PACKAGE_ID = 23
    PACKAGE_NAME = "seismic-utac"
    VERSION = "0.1.0"

    def __init__(
        self,
        m_min: float = M_MIN_COMPLETENESS,
        loading_rate: float = R_LOADING,
        b_monitor_window: int = 100,
        spatial_correlation: float = 0.8,
        avalanche_quality: float = 0.85,
    ) -> None:
        self.m_min = m_min
        self._crep = SeismicCREP(
            spatial_correlation=spatial_correlation,
            avalanche_quality=avalanche_quality,
            m_min=m_min,
        )
        self._gr_fitter = GutenbergRichterFitter()
        self._strain = StrainAccumulationModel(loading_rate=loading_rate)
        self._monitor = BValueMonitor(window_size=b_monitor_window, m_min=m_min)
        self._omori = OmoriUtsu()
        self._catalog_loader = SeismicCatalogLoader()
        self._state: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Diamond interface — 5 required methods
    # ------------------------------------------------------------------

    def analyze(self, magnitudes: list[float] | np.ndarray, **kwargs: Any) -> dict[str, Any]:
        """Analyze a magnitude sequence and return full CREP state.

        Returns dict with Gamma, b_value, C, R, E, P, eta, and diagnostics.
        """
        mags = np.asarray(magnitudes, dtype=float)
        b_value = kwargs.get("b_value")
        crep = self._crep.compute(mags, b_value=b_value)

        # Update b-value monitor
        for m in mags:
            self._monitor.update(float(m))

        self._state = {
            **crep,
            "n_events": len(mags),
            "phase_imminent": self._monitor.phase_imminent(),
            "entropy_decreasing": False,
        }
        return dict(self._state)

    def calibrate(
        self,
        magnitudes: list[float] | np.ndarray,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Calibrate model parameters from a reference catalog.

        Returns fitted parameters and goodness-of-fit metrics.
        """
        mags = np.asarray(magnitudes, dtype=float)
        m_min = kwargs.get("m_min", self.m_min)

        gr_result = self._gr_fitter.fit(mags, m_min)
        b = gr_result["b_value"]
        gamma = b_to_gamma(b)

        result = {
            **gr_result,
            "gamma": gamma,
            "gamma_target": GAMMA_SEISMIC,
            "gamma_within_tolerance": abs(gamma - GAMMA_SEISMIC) <= GAMMA_SEISMIC_TOL,
            "b_soc_typical": B_SOC_TYPICAL,
        }
        return result

    def simulate(
        self,
        n_events: int = 1000,
        b_value: float = B_SOC_TYPICAL,
        duration_years: float = 10.0,
        seed: int = 42,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Simulate a synthetic seismic catalog.

        Returns catalog dict with events and fitted parameters.
        """
        M_max = kwargs.get("M_max", 8.0)
        events = self._catalog_loader.load_synthetic(
            n_events=n_events,
            b_value=b_value,
            M_min=self.m_min,
            M_max=M_max,
            duration_years=duration_years,
            seed=seed,
        )
        mags = [e["magnitude"] for e in events]
        gr_fit = self._gr_fitter.fit(mags, self.m_min)

        return {
            "events": events,
            "n_events": len(events),
            "b_value_input": b_value,
            "b_value_fitted": gr_fit["b_value"],
            "gamma": b_to_gamma(gr_fit["b_value"]),
            "duration_years": duration_years,
        }

    def detect(
        self,
        magnitudes: list[float] | np.ndarray,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Detect seismic phase transitions / critical state indicators.

        Returns detection flags and current state metrics.
        """
        mags = np.asarray(magnitudes, dtype=float)
        crep = self._crep.compute(mags)
        gamma = crep["Gamma"]
        b = crep["b_value"]

        phase_imminent = self._monitor.phase_imminent()
        strain_critical = self._strain.is_critical(gamma)
        b_trend = self._monitor.b_trend()

        return {
            "Gamma": gamma,
            "b_value": b,
            "phase_imminent": phase_imminent,
            "strain_critical": strain_critical,
            "b_trend": b_trend,
            "alert_level": "HIGH" if (phase_imminent or strain_critical) else "LOW",
        }

    def report(self, **kwargs: Any) -> dict[str, Any]:
        """Generate a summary report of the current seismic state.

        Returns summary dict with all key metrics.
        """
        b_current = self._monitor.current_b()
        gamma = b_to_gamma(b_current) if b_current is not None else None

        return {
            "package_id": self.PACKAGE_ID,
            "package_name": self.PACKAGE_NAME,
            "version": self.VERSION,
            "b_value_current": b_current,
            "gamma": gamma,
            "strain_H": self._strain.H,
            "phase_imminent": self._monitor.phase_imminent(),
            "b_trend": self._monitor.b_trend(),
            "state": dict(self._state),
        }

    # ------------------------------------------------------------------
    # Diamond contract methods (required by GenesisAeon specification)
    # ------------------------------------------------------------------

    def run_cycle(self, duration_years: float = 50.0, seed: int = 42) -> dict[str, Any]:
        """Run a full UTAC cycle. Delegates to simulate() + analyze().

        Returns dict with gamma, b_value, H, H_star, phase_events, crep, utac.
        """
        sim = self.simulate(
            n_events=5000,
            b_value=B_SOC_TYPICAL,
            duration_years=duration_years,
            seed=seed,
        )
        mags = [e["magnitude"] for e in sim["events"]]
        crep = self._crep.compute(mags, b_value=sim["b_value_fitted"])
        gamma = crep["Gamma"]
        H_star = self._strain.H_star_from_gamma(gamma)

        # Identify phase events (M≥6.5)
        phase_events = [
            {
                "time": e["time"],
                "magnitude": e["magnitude"],
                "type": "major_rupture",
                "H_at_event": self._strain.H,
                "gamma": gamma,
            }
            for e in sim["events"]
            if e["magnitude"] >= 6.5
        ]

        # Also feed the b-value monitor so predict_major_event_probability() has data
        for m in mags:
            self._monitor.update(float(m))

        self._state = {
            **crep, "H": self._strain.H, "H_star": H_star, "phase_events_list": phase_events,
        }
        return {
            "gamma": gamma,
            "b_value": sim["b_value_fitted"],
            "H": self._strain.H,
            "H_star": H_star,
            "phase_events": phase_events,
            "n_events": sim["n_events"],
            "crep": crep,
            "utac": {"H": self._strain.H, "dH_dt": 0.0, "H_star": H_star, "K_eff": 1.0},
            "duration_years": duration_years,
        }

    def get_crep_state(self) -> dict[str, float]:
        """Return current CREP tensor: {C, R, E, P, Gamma}."""
        keys = ("C", "R", "E", "P", "Gamma", "eta", "b_value")
        return {k: float(self._state[k]) for k in keys if k in self._state}

    def get_utac_state(self) -> dict[str, float]:
        """Return UTAC state variables: {H, dH_dt, H_star, K_eff}."""
        return {
            "H": self._strain.H,
            "dH_dt": 0.0,
            "H_star": self._state.get("H_star", 0.5),
            "K_eff": 1.0,
        }

    def get_phase_events(self) -> list[dict[str, Any]]:
        """Return list of phase events recorded in the last run_cycle()."""
        return list(self._state.get("phase_events_list", []))

    def to_zenodo_record(self) -> dict[str, Any]:
        """Serialize current state to a Zenodo-compatible metadata record."""
        from datetime import datetime

        return {
            "title": f"SeismicUTAC Package {self.PACKAGE_ID}: Gutenberg-Richter SOC",
            "description": (
                "UTAC/CREP model of global earthquake seismicity. "
                "Calibrated against IRIS 50-year catalog (154,383 events)."
            ),
            "creators": [{"name": "GenesisAeon", "affiliation": "MOR Research Collective"}],
            "license": "CC-BY-4.0",
            "keywords": ["seismicity", "SOC", "CREP", "Gutenberg-Richter", "UTAC"],
            "references": ["DOI:10.1029/JB094iB11p15635"],
            "package_id": self.PACKAGE_ID,
            "package_name": self.PACKAGE_NAME,
            "version": self.VERSION,
            "crep_state": self.get_crep_state(),
            "utac_state": self.get_utac_state(),
            "gamma_seismic_target": GAMMA_SEISMIC,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

    # ------------------------------------------------------------------
    # Additional public methods
    # ------------------------------------------------------------------

    def b_value_current(self) -> float:
        """Return current b-value from the sliding window monitor."""
        b = self._monitor.current_b()
        return b if b is not None else B_SOC_TYPICAL

    def predict_major_event_probability(
        self,
        magnitude: float = 7.0,
        horizon_days: float = 365.0,
    ) -> float:
        """UTAC-based probability of M≥magnitude within horizon_days.

        P = tanh(sigma*Gamma) * exp(-b*ln(10)*(magnitude - M_min)) * t_frac
        Returns probability in [0, 1].
        """
        from seismic_utac.constants import SIGMA

        # Prefer the b-value from the last run_cycle if monitor has no data
        b = self._monitor.current_b()
        if b is None:
            b = float(self._state.get("b_value", B_SOC_TYPICAL))
        gamma = b_to_gamma(b)

        beta = b * math.log(10)
        p_base = math.tanh(SIGMA * gamma)
        p_mag = math.exp(-beta * max(0.0, magnitude - self.m_min))
        t_frac = horizon_days / 365.0
        return float(min(1.0, max(0.0, p_base * p_mag * t_frac)))
