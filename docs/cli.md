# CLI Reference

## `seismic-utac run`

Run a full UTAC seismic cycle and print results.

```
Usage: seismic-utac run [OPTIONS]

Options:
  --catalog TEXT     Catalog type: iris or synthetic  [default: iris]
  --region TEXT      Region name                      [default: global]
  --duration FLOAT   Duration in years                [default: 50.0]
  --seed INTEGER     Random seed                      [default: 42]
```

**Example**

```bash
seismic-utac run --catalog iris --region global --duration 50
```

---

## `seismic-utac b-value-monitor`

Monitor the sliding b-value and phase transition risk for a region.

```
Usage: seismic-utac b-value-monitor [OPTIONS]

Options:
  --region TEXT       Region to monitor   [default: southern-california]
  --n-events INTEGER  Events to simulate  [default: 500]
```

```bash
seismic-utac b-value-monitor --region southern-california
```

Outputs current b-value, trend (slope per window), and phase-imminent flag.

---

## `seismic-utac predict`

UTAC-based probability forecast for a major seismic event.

```
Usage: seismic-utac predict [OPTIONS]

Options:
  --magnitude FLOAT  Target magnitude threshold  [default: 7.5]
  --horizon INTEGER  Forecast horizon in days    [default: 365]
```

```bash
seismic-utac predict --magnitude 7.5 --horizon 365
```

---

## `seismic-utac benchmark`

Run all benchmark targets against Bak & Tang (1989) and print a results table.

```bash
seismic-utac benchmark
```

Benchmark targets:

| Target | Expected | Tolerance |
|--------|----------|-----------|
| `b_value_global` | 1.00 | ±0.10 |
| `b_value_swarm_max` | 2.50 | ±0.30 |
| `gamma_seismic` | 0.200 | ±0.03 |
| `aftershock_omori_p` | 1.10 | ±0.10 |

---

## `diamond` scaffold tool

This repo also ships the **diamond-setup** scaffold CLI for generating new GenesisAeon packages.

```bash
diamond scaffold my-new-package --template genesis
diamond list-templates
diamond validate path/to/project
```
