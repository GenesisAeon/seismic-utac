"""CLI for seismic-utac Package 23."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="seismic-utac", help="Seismic SOC analysis — Package 23, GenesisAeon")
console = Console()


@app.command()
def run(
    catalog: str = typer.Option("iris", help="Catalog type: iris or synthetic"),
    region: str = typer.Option("global", help="Region name"),
    duration: float = typer.Option(50.0, help="Duration in years"),
    seed: int = typer.Option(42, help="Random seed"),
) -> None:
    """Run a full UTAC seismic cycle."""
    from seismic_utac.system import SeismicUTAC

    console.print(f"[bold]seismic-utac[/bold] — running {catalog} catalog, region={region}")
    system = SeismicUTAC()
    result = system.run_cycle(duration_years=duration, seed=seed)

    table = Table(title="UTAC Seismic Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Gamma (CREP)", f"{result['gamma']:.4f}")
    table.add_row("b-value (fitted)", f"{result['b_value']:.4f}")
    table.add_row("H (strain)", f"{result['H']:.4f}")
    table.add_row("H* (critical)", f"{result['H_star']:.4f}")
    table.add_row("Phase events", str(len(result["phase_events"])))
    table.add_row("Events processed", str(result["n_events"]))
    console.print(table)


@app.command(name="b-value-monitor")
def b_value_monitor(
    region: str = typer.Option("southern-california", help="Region to monitor"),
    n_events: int = typer.Option(500, help="Number of synthetic events to simulate"),
) -> None:
    """Monitor real-time b-value and phase transition risk."""
    from seismic_utac.b_value_monitor import BValueMonitor
    from seismic_utac.catalog_loader import SeismicCatalogLoader

    loader = SeismicCatalogLoader()
    monitor = BValueMonitor()
    events = loader.load_synthetic(n_events=n_events, region=region)
    for e in events:
        monitor.update(e["magnitude"])

    b = monitor.current_b()
    trend = monitor.b_trend()
    imminent = monitor.phase_imminent()

    console.print(f"[bold]b-value monitor[/bold] — region: {region}")
    console.print(f"  Current b: {b:.3f}" if b else "  Current b: N/A")
    console.print(f"  Trend: {trend:.4f}/window" if trend else "  Trend: N/A")
    console.print(f"  Phase imminent: [{'red' if imminent else 'green'}]{imminent}[/]")


@app.command()
def predict(
    magnitude: float = typer.Option(7.5, help="Target magnitude threshold"),
    horizon: int = typer.Option(365, help="Forecast horizon in days"),
) -> None:
    """Predict probability of major seismic event."""
    from seismic_utac.system import SeismicUTAC

    system = SeismicUTAC()
    system.run_cycle(duration_years=10.0)
    prob = system.predict_major_event_probability(magnitude=magnitude, horizon_days=float(horizon))
    console.print(f"[bold]Seismic Forecast[/bold]")
    console.print(f"  P(M≥{magnitude} within {horizon}d) = [yellow]{prob:.4f}[/yellow]")


@app.command()
def benchmark() -> None:
    """Run all benchmark targets against Bak & Tang (1989)."""
    from seismic_utac.benchmark import run_benchmark

    console.print("[bold]Running seismic-utac benchmark suite...[/bold]")
    result = run_benchmark()

    table = Table(title="Benchmark Results — Bak & Tang (1989)")
    table.add_column("Target", style="cyan")
    table.add_column("Expected", style="white")
    table.add_column("Actual", style="white")
    table.add_column("Status", style="bold")

    for r in result["results"]:
        status = "[green]PASS[/green]" if r.passed else "[red]FAIL[/red]"
        table.add_row(r.target_name, f"{r.expected:.3f} ± {r.tolerance:.3f}", f"{r.actual:.3f}", status)

    console.print(table)
    console.print(f"\n{result['n_passed']}/{result['n_total']} targets passed")
