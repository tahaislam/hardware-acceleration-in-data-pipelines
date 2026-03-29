#!/usr/bin/env python3
"""
crossover_analysis.py

Interactive exploration of acceleration crossover points.

This script visualizes when hardware acceleration produces meaningful
system-level speedup versus when transfer overhead and integration
costs dominate. All parameters are configurable — plug in your own
numbers to evaluate your specific workload.

Usage:
    python crossover_analysis.py                    # Generate all plots
    python crossover_analysis.py --interactive      # Interactive mode (requires terminal)

Requirements:
    pip install matplotlib numpy

Output:
    Generates PNG plots in the current directory:
    - crossover_batch_size.png      : System speedup vs. batch size
    - crossover_compute_fraction.png: System speedup vs. pipeline compute fraction
    - amdahl_heatmap.png            : Amdahl's Law heatmap

No FPGA hardware required. All analysis is parametric.
"""

import argparse
import sys

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend (works without display)
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
except ImportError:
    print("Error: matplotlib is required. Install with: pip install matplotlib numpy")
    sys.exit(1)


# ─── Default Parameters (override with your own numbers) ───────────────

DEFAULTS = {
    # CPU baseline: records per second (single-core, optimized)
    "cpu_throughput_rps": 50_000_000,

    # Accelerator kernel: records per second (on-device, no transfer)
    "accel_kernel_throughput_rps": 200_000_000,

    # PCIe transfer bandwidth (bytes/sec, practical)
    "transfer_bandwidth_bps": 12_000_000_000,  # ~12 GB/s (PCIe Gen3 x16)

    # Per-record sizes
    "input_bytes_per_record": 16,   # 8 fields × 2 bytes
    "output_bytes_per_record": 7,   # 52 bits packed

    # Fixed overhead per batch (DMA setup, sync, driver calls)
    "fixed_overhead_sec": 0.0005,   # 0.5 ms
}


def system_speedup_vs_batch_size(params: dict, batch_sizes: np.ndarray) -> np.ndarray:
    """
    Calculate system-level speedup (accelerated vs. CPU) as a function of batch size.

    For small batches, fixed overhead dominates and the accelerator is slower.
    For large batches, transfer overhead is amortized and the kernel speed matters.
    """
    cpu_time = batch_sizes / params["cpu_throughput_rps"]

    bytes_per_batch = batch_sizes * (
        params["input_bytes_per_record"] + params["output_bytes_per_record"]
    )
    transfer_time = bytes_per_batch / params["transfer_bandwidth_bps"]
    kernel_time = batch_sizes / params["accel_kernel_throughput_rps"]
    accel_time = transfer_time + kernel_time + params["fixed_overhead_sec"]

    return cpu_time / accel_time


def amdahl_speedup(compute_fraction: np.ndarray, kernel_speedup: np.ndarray) -> np.ndarray:
    """
    Amdahl's Law: pipeline speedup given compute fraction and kernel speedup.

    Returns a 2D array: [compute_fraction, kernel_speedup] -> pipeline_speedup
    """
    f = compute_fraction[:, np.newaxis]
    s = kernel_speedup[np.newaxis, :]
    return 1.0 / ((1.0 - f) + f / s)


def plot_batch_size_crossover(params: dict, output_path: str = "crossover_batch_size.png"):
    """
    Plot: System speedup vs. batch size.

    Shows the crossover point where acceleration becomes beneficial,
    and how it depends on transfer overhead vs. compute.
    """
    batch_sizes = np.logspace(2, 8, 500)  # 100 to 100M records
    speedups = system_speedup_vs_batch_size(params, batch_sizes)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.semilogx(batch_sizes, speedups, linewidth=2, color="#2E86AB")
    ax.axhline(y=1.0, color="#E74C3C", linestyle="--", linewidth=1, label="Break-even (1x)")

    # Find crossover point
    crossover_idx = np.searchsorted(speedups, 1.0)
    if crossover_idx < len(batch_sizes):
        crossover_batch = batch_sizes[crossover_idx]
        ax.axvline(x=crossover_batch, color="#F39C12", linestyle=":", linewidth=1)
        ax.annotate(
            f"Crossover: {crossover_batch:,.0f} records",
            xy=(crossover_batch, 1.0),
            xytext=(crossover_batch * 5, 0.6),
            arrowprops=dict(arrowstyle="->", color="#555"),
            fontsize=10, color="#555",
        )

    ax.set_xlabel("Batch Size (records)", fontsize=12)
    ax.set_ylabel("System Speedup (accelerated / CPU)", fontsize=12)
    ax.set_title("System-Level Speedup vs. Batch Size\n"
                 "(includes transfer overhead and fixed costs)", fontsize=13)
    ax.set_ylim(0, max(speedups) * 1.15)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # Add parameter annotation
    param_text = (
        f"CPU: {params['cpu_throughput_rps']/1e6:.0f}M rec/s | "
        f"Accel kernel: {params['accel_kernel_throughput_rps']/1e6:.0f}M rec/s\n"
        f"PCIe BW: {params['transfer_bandwidth_bps']/1e9:.0f} GB/s | "
        f"Fixed overhead: {params['fixed_overhead_sec']*1000:.1f}ms"
    )
    ax.text(0.02, 0.98, param_text, transform=ax.transAxes,
            fontsize=8, verticalalignment="top", color="#777",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"  Saved: {output_path}")
    plt.close(fig)


def plot_compute_fraction_impact(output_path: str = "crossover_compute_fraction.png"):
    """
    Plot: Pipeline speedup vs. compute fraction for different kernel speedups.

    Demonstrates Amdahl's Law visually — even a 100x kernel speedup produces
    minimal pipeline improvement when the compute fraction is small.
    """
    fractions = np.linspace(0.05, 0.95, 200)
    kernel_speedups = [2, 5, 10, 50, 100]
    colors = ["#3498DB", "#2ECC71", "#F39C12", "#E74C3C", "#9B59B6"]

    fig, ax = plt.subplots(figsize=(10, 6))

    for s, color in zip(kernel_speedups, colors):
        pipeline_speedup = 1.0 / ((1.0 - fractions) + fractions / s)
        ax.plot(fractions * 100, pipeline_speedup, linewidth=2, color=color,
                label=f"Kernel speedup: {s}x")

    ax.axhline(y=1.0, color="#999", linestyle="--", linewidth=0.5)
    ax.axvline(x=30, color="#E74C3C", linestyle=":", linewidth=1, alpha=0.5)
    ax.text(31, ax.get_ylim()[1] * 0.9, "30% threshold\n(framework minimum)",
            fontsize=9, color="#E74C3C", alpha=0.7)

    ax.set_xlabel("Compute Stage as % of Pipeline Runtime", fontsize=12)
    ax.set_ylabel("Pipeline Speedup (Amdahl's Law)", fontsize=12)
    ax.set_title("Pipeline Speedup vs. Compute Fraction\n"
                 "(why kernel speedup alone doesn't determine system improvement)", fontsize=13)
    ax.legend(fontsize=10, loc="upper left")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"  Saved: {output_path}")
    plt.close(fig)


def plot_amdahl_heatmap(output_path: str = "amdahl_heatmap.png"):
    """
    Heatmap: Pipeline speedup as a function of both compute fraction and kernel speedup.

    This is the complete picture — it shows the narrow region where acceleration
    produces meaningful results (high compute fraction AND high kernel speedup).
    """
    fractions = np.linspace(0.05, 0.95, 50)
    kernel_speedups = np.logspace(np.log10(2), np.log10(100), 50)

    speedup_matrix = amdahl_speedup(fractions, kernel_speedups)

    fig, ax = plt.subplots(figsize=(10, 7))

    im = ax.pcolormesh(
        kernel_speedups, fractions * 100, speedup_matrix,
        cmap="RdYlGn", shading="auto", vmin=1.0, vmax=8.0
    )

    # Add contour lines
    contour_levels = [1.5, 2.0, 3.0, 5.0]
    cs = ax.contour(kernel_speedups, fractions * 100, speedup_matrix,
                    levels=contour_levels, colors="black", linewidths=0.8, alpha=0.6)
    ax.clabel(cs, inline=True, fontsize=9, fmt="%.1fx")

    ax.set_xscale("log")
    ax.set_xlabel("Kernel Speedup (accelerated / CPU)", fontsize=12)
    ax.set_ylabel("Compute Stage as % of Pipeline Runtime", fontsize=12)
    ax.set_title("Pipeline Speedup (Amdahl's Law)\n"
                 "Meaningful gains require BOTH high compute fraction AND high kernel speedup",
                 fontsize=12)

    cbar = fig.colorbar(im, ax=ax, label="Pipeline Speedup")
    cbar.ax.tick_params(labelsize=10)

    # Annotate the "most pipelines live here" region
    ax.annotate(
        "Most data pipelines\nlive here",
        xy=(5, 15), fontsize=10, color="white", fontweight="bold",
        ha="center",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#E74C3C", alpha=0.8),
    )

    ax.annotate(
        "Acceleration\nsweet spot",
        xy=(30, 75), fontsize=10, color="white", fontweight="bold",
        ha="center",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#27AE60", alpha=0.8),
    )

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"  Saved: {output_path}")
    plt.close(fig)


def interactive_mode(params: dict):
    """Simple interactive parameter exploration."""
    print("\n=== Acceleration Crossover Analysis (Interactive Mode) ===\n")
    print("Current parameters:")
    for k, v in params.items():
        print(f"  {k}: {v:,}")

    print("\nAdjust parameters by entering: key=value")
    print("Type 'plot' to generate charts, 'quit' to exit.\n")

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if line.lower() in ("quit", "exit", "q"):
            break
        elif line.lower() == "plot":
            generate_all_plots(params)
        elif "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            if key in params:
                try:
                    params[key] = float(val.strip().replace(",", "").replace("_", ""))
                    print(f"  {key} = {params[key]:,.0f}")
                except ValueError:
                    print(f"  Error: could not parse '{val.strip()}' as a number")
            else:
                print(f"  Unknown parameter: '{key}'")
                print(f"  Valid: {', '.join(params.keys())}")
        elif line:
            print("  Commands: key=value, plot, quit")


def generate_all_plots(params: dict):
    """Generate all analysis plots."""
    print("\nGenerating plots...")
    plot_batch_size_crossover(params)
    plot_compute_fraction_impact()
    plot_amdahl_heatmap()
    print("Done.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Acceleration crossover analysis — explore when hardware "
                    "acceleration produces meaningful system-level speedup.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crossover_analysis.py                           # Generate all plots
  python crossover_analysis.py --interactive             # Explore interactively
  python crossover_analysis.py --cpu-throughput 100e6    # Override CPU baseline

All plots are saved as PNG files in the current directory.
No FPGA hardware required — analysis is purely parametric.
        """,
    )
    parser.add_argument("--interactive", action="store_true",
                        help="Interactive parameter exploration mode")
    parser.add_argument("--cpu-throughput", type=float, default=None,
                        help="CPU throughput in records/sec (default: 50M)")
    parser.add_argument("--accel-throughput", type=float, default=None,
                        help="Accelerator kernel throughput in records/sec (default: 200M)")
    parser.add_argument("--transfer-bw", type=float, default=None,
                        help="Transfer bandwidth in bytes/sec (default: 12 GB/s)")
    parser.add_argument("--fixed-overhead", type=float, default=None,
                        help="Fixed per-batch overhead in seconds (default: 0.5ms)")

    args = parser.parse_args()

    params = dict(DEFAULTS)
    if args.cpu_throughput:
        params["cpu_throughput_rps"] = args.cpu_throughput
    if args.accel_throughput:
        params["accel_kernel_throughput_rps"] = args.accel_throughput
    if args.transfer_bw:
        params["transfer_bandwidth_bps"] = args.transfer_bw
    if args.fixed_overhead:
        params["fixed_overhead_sec"] = args.fixed_overhead

    if args.interactive:
        interactive_mode(params)
    else:
        generate_all_plots(params)


if __name__ == "__main__":
    main()
