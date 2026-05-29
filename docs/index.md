# seismic-utac

**Package 23 — Earthquake Seismicity & Gutenberg-Richter SOC**
GenesisAeon · MOR Research Collective

Models global earthquake seismicity as a **UTAC** (Unified Threshold-Activated Criticality)
system, grounding the Gutenberg-Richter power law as a CREP-mediated Self-Organized Critical
(SOC) phenomenon. Calibrated against the IRIS 50-year global catalog (154,383 earthquakes).

## Quickstart

```bash
pip install seismic-utac
# or
uv tool install seismic-utac
```

```python
from seismic_utac import SeismicUTAC

system = SeismicUTAC()
result = system.run_cycle(duration_years=50.0)
print(f"Γ = {result['gamma']:.4f}")          # ≈ 0.200
print(f"b-value = {result['b_value']:.3f}")  # ≈ 1.7
print(f"Phase events: {len(result['phase_events'])}")
```

## CREP Criticality Spectrum

| Domain | Package | Γ |
|--------|---------|---|
| Qubit decoherence | P24 | 0.050 |
| Apoptosis ATP threshold | P25 | 0.090 |
| **Seismic b-value (GR)** | **P23** | **0.200** |
| AMOC / Neural criticality | P18/P20 | 0.251 |
| BTW Sandpile (SOC) | P22 | 0.296 |

## CLI Commands

| Command | Description |
|---------|-------------|
| `seismic-utac run` | Run a full UTAC seismic cycle |
| `seismic-utac b-value-monitor` | Monitor b-value and phase risk |
| `seismic-utac predict` | Forecast major event probability |
| `seismic-utac benchmark` | Run Bak & Tang (1989) benchmarks |

## References

- Bak & Tang (1989). [DOI: 10.1029/JB094iB11p15635](https://doi.org/10.1029/JB094iB11p15635)
- Al-Kindy & Main (2003). [DOI: 10.1029/2002JB002230](https://doi.org/10.1029/2002JB002230)
- da Silva et al. (2021). [DOI: 10.1016/j.chaos.2020.110634](https://doi.org/10.1016/j.chaos.2020.110634)
- IRIS Global Seismic Catalog: 154,383 earthquakes, 50-year record, 6 global regions
