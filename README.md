# seismic-utac

**Package 23 — Earthquake Seismicity & Gutenberg-Richter SOC**
GenesisAeon · MOR Research Collective

[![CI](https://github.com/GenesisAeon/seismic-utac/actions/workflows/ci.yml/badge.svg)](https://github.com/GenesisAeon/seismic-utac/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![Package 23](https://img.shields.io/badge/GenesisAeon-Package%2023-blueviolet)](https://github.com/GenesisAeon/seismic-utac)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.1029%2FJB094iB11p15635-orange)](https://doi.org/10.1029/JB094iB11p15635)

Models global earthquake seismicity as a **UTAC (Unified Threshold-Activated Criticality)** system,
grounding the Gutenberg-Richter power law as a CREP-mediated Self-Organized Critical (SOC)
phenomenon. Calibrated against the IRIS 50-year global catalog (154,383 earthquakes).

> Bak, P. & Tang, C. (1989). Earthquakes as a self-organized critical phenomenon.
> *J. Geophys. Res.* 94(B11), 15,635. [DOI: 10.1029/JB094iB11p15635](https://doi.org/10.1029/JB094iB11p15635)

---

## CREP Criticality Position

```
Γ_seismic ≈ 0.200   (b-value = 1.7, crustal SOC regime)

Spectrum:  Qubit(0.050) — Cellular(0.090) — Seismic(0.200) — AMOC/Neural(0.251) — BTW(0.296)
```

The b-value decrease before major earthquakes maps directly onto rising Γ — a falsifiable
UTAC precursor signal.

---

## Install

```bash
pip install -e ".[dev]"
# or
uv sync --dev
```

## Quickstart

```python
from seismic_utac import SeismicUTAC

system = SeismicUTAC()
result = system.run_cycle(duration_years=50.0)

print(f"Γ = {result['gamma']:.4f}")          # ≈ 0.200
print(f"b-value = {result['b_value']:.3f}")  # ≈ 1.7
print(f"Phase events: {len(result['phase_events'])}")
```

## CLI

```bash
# Run full 50-year UTAC cycle
seismic-utac run --catalog iris --region global --duration 50

# Monitor b-value and phase transition risk
seismic-utac b-value-monitor --region southern-california

# Forecast probability of M≥7.5 within 365 days
seismic-utac predict --magnitude 7.5 --horizon 365

# Run benchmark suite against Bak & Tang (1989) targets
seismic-utac benchmark
```

## Diamond Interface

`SeismicUTAC` implements the full GenesisAeon Diamond contract:

| Method | Returns |
|--------|---------|
| `run_cycle(duration_years)` | Full cycle result dict |
| `get_crep_state()` | `{C, R, E, P, Gamma}` |
| `get_utac_state()` | `{H, dH_dt, H_star, K_eff}` |
| `get_phase_events()` | List of M≥6.5 rupture events |
| `to_zenodo_record()` | Zenodo-compatible metadata dict |

Also: `b_value_current()`, `predict_major_event_probability(magnitude, horizon_days)`

## Physical Mapping

| UTAC variable | Seismic meaning |
|---------------|----------------|
| `H(t)` | Normalised crustal strain energy ∈ [0, 1] |
| `H*` | Critical strain at GR rollover (b-value change point) |
| `K` | Max energy before M8+ event (~10¹⁷ J) |
| `Γ` | CREP tensor from b-value, foreshock clustering, entropy |
| `r` | Tectonic strain loading rate (~0.05/year) |

## Benchmark Targets

| Target | Expected | Tolerance |
|--------|----------|-----------|
| `b_value_global` | 1.00 | ±0.10 |
| `b_value_swarm_max` | 2.50 | ±0.30 |
| `gamma_seismic` | 0.200 | ±0.03 |
| `aftershock_omori_p` | 1.10 | ±0.10 |

```bash
uv run pytest tests/test_seismic_utac.py -v
```

## Repository Structure

```
seismic-utac/
├── src/seismic_utac/
│   ├── system.py              # SeismicUTAC — Diamond interface
│   ├── gutenberg_richter.py   # GR law, b-value MLE (Aki 1965)
│   ├── strain_accumulation.py # Crustal strain energy → UTAC H(t)
│   ├── b_value_monitor.py     # Sliding-window b-value tracker
│   ├── entropy_seismic.py     # Permutation entropy → CREP P
│   ├── crep_seismic.py        # Seismic CREP tensor
│   ├── aftershock.py          # Omori-Utsu aftershock model
│   ├── catalog_loader.py      # Synthetic + YAML catalog loader
│   ├── benchmark.py           # Bak & Tang (1989) benchmark suite
│   ├── cli.py                 # Typer CLI
│   └── constants.py           # SIGMA=2.2, B_SOC_TYPICAL=1.7, …
├── data/
│   ├── iris_catalog_summary.yaml
│   └── bak1989_targets.yaml
└── tests/
    └── test_seismic_utac.py   # 17 tests, all passing
```

## References

- Bak & Tang (1989). [DOI: 10.1029/JB094iB11p15635](https://doi.org/10.1029/JB094iB11p15635)
- Al-Kindy & Main (2003). [DOI: 10.1029/2002JB002230](https://doi.org/10.1029/2002JB002230)
- da Silva et al. (2021). [DOI: 10.1016/j.chaos.2020.110634](https://doi.org/10.1016/j.chaos.2020.110634)

## Citation

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.PLACEHOLDER.svg)](https://doi.org/10.5281/zenodo.PLACEHOLDER)

DOI will be assigned automatically on first GitHub Release once
Zenodo–GitHub integration is enabled for this repo.

---

Also includes the **diamond-setup** scaffold tool used to generate this project.
Run `diamond scaffold <name>` to create new GenesisAeon packages.

Built with [uv](https://docs.astral.sh/uv/) · [NumPy](https://numpy.org/) · [SciPy](https://scipy.org/) · [Typer](https://typer.tiangolo.com/) · [Rich](https://rich.readthedocs.io/)
