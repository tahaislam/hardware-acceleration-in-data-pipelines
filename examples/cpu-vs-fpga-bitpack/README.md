# CPU vs. FPGA Trade-offs in Bitfield Packing

## Problem Statement

Many data pipelines include a stage that transforms structured records into a compact binary representation — packing fields of varying bit widths into dense bitstreams for storage, transmission, or downstream consumption.

This is a useful acceleration candidate to study because it has properties that look favorable for hardware offload:

- **High arithmetic density:** Shifts, masks, and ORs with no memory allocation.
- **No branching:** The packing logic for a fixed schema is branch-free.
- **Embarrassingly parallel:** Each record is independent.
- **Stable logic:** The packing format rarely changes.

And yet, as the analysis shows, the end-to-end story is more nuanced than the kernel performance alone suggests.

## The Scenario

A data pipeline ingests sensor telemetry records at high throughput. Each record contains 8 fields of varying bit widths (3 to 12 bits), totaling 52 bits per record, packed into a 7-byte output. The pipeline processes batches of 1 million records.

This example provides:

1. **`cpu_baseline.c`** — A straightforward C implementation using bit shifts and masks. Compiles and runs — try it.
2. **`hls_sketch.cpp`** — An HLS-style sketch (C++ with pragmas) showing what an FPGA implementation *would* look like, without being synthesizable or vendor-specific.
3. **`analysis.md`** — A detailed trade-off analysis comparing the two approaches at the system level.

## Quick Start

```bash
make run       # Build with -O3 and run the benchmark
make clean     # Remove build artifacts
```

## What This Example Demonstrates

- That a compute kernel can be "fast" while the system-level improvement is modest.
- That data transfer overhead fundamentally changes the acceleration calculus.
- That a well-optimized CPU implementation may be "good enough" when integration cost is factored in.
- How to reason about batching, transfer amortization, and crossover points.

## What This Example Does Not Demonstrate

- Actual FPGA synthesis results (this would require a specific board and toolchain).
- Production-grade error handling or memory management.
- Real telemetry data or proprietary formats.

The code is intentionally simplified to isolate the trade-off reasoning from implementation complexity.
