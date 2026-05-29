"""Seismic catalog loading and filtering utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import yaml

from seismic_utac.gutenberg_richter import generate_gr_magnitudes

Event = dict[str, Any]


class SeismicCatalogLoader:
    """Load and filter seismic event catalogs."""

    def load_synthetic(
        self,
        n_events: int = 1000,
        b_value: float = 1.0,
        M_min: float = 2.5,
        M_max: float = 8.0,
        duration_years: float = 10.0,
        seed: int = 42,
        region: str = "synthetic",
    ) -> list[Event]:
        """Generate a synthetic seismic catalog from GR distribution."""
        rng = np.random.default_rng(seed)
        magnitudes = generate_gr_magnitudes(n_events, b_value, M_min, M_max, rng)

        # Generate random times (Poisson process)
        times_raw = rng.uniform(0.0, duration_years, size=n_events)
        times_raw.sort()

        # Random locations (simplified)
        lats = rng.uniform(-90.0, 90.0, size=n_events)
        lons = rng.uniform(-180.0, 180.0, size=n_events)
        depths = rng.uniform(5.0, 70.0, size=n_events)

        events: list[Event] = []
        for i in range(n_events):
            events.append(
                {
                    "time": float(times_raw[i]),
                    "magnitude": float(magnitudes[i]),
                    "lat": float(lats[i]),
                    "lon": float(lons[i]),
                    "depth": float(depths[i]),
                    "region": region,
                }
            )
        return events

    def load_yaml(self, path: str | Path) -> list[Event]:
        """Load catalog from YAML file."""
        p = Path(path)
        with p.open() as f:
            data = yaml.safe_load(f)

        events = data.get("events", [])
        return [dict(e) for e in events]

    def filter_by_magnitude(
        self,
        events: list[Event],
        M_min: float | None = None,
        M_max: float | None = None,
    ) -> list[Event]:
        """Filter events by magnitude range."""
        filtered = events
        if M_min is not None:
            filtered = [e for e in filtered if e["magnitude"] >= M_min]
        if M_max is not None:
            filtered = [e for e in filtered if e["magnitude"] <= M_max]
        return filtered

    def filter_by_region(self, events: list[Event], region: str) -> list[Event]:
        """Filter events by region name."""
        return [e for e in events if e.get("region") == region]

    def get_magnitudes(self, events: list[Event]) -> list[float]:
        """Extract magnitude list from events."""
        return [e["magnitude"] for e in events]
