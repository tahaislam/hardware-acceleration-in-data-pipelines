# Benchmark Methodology for Hardware Acceleration

**How to measure acceleration honestly — and how most benchmarks lie by omission.**

---

## The Core Problem

Most published acceleration benchmarks measure **kernel throughput in isolation**. This is like measuring a car engine's horsepower on a dyno and claiming that as the vehicle's 0–60 time. The engine matters, but so does the drivetrain, the tires, and the weight of the car.

An honest acceleration benchmark measures **end-to-end pipeline throughput** with the accelerator integrated into the actual (or faithfully simulated) data path.

---

## What to Measure

### 1. End-to-End Wall-Clock Time

The time from "input data is available in the pipeline" to "output data is committed to the next stage." This includes:

- Data marshalling (converting from pipeline format to accelerator format)
- Transfer to device (PCIe DMA, memory copy, network transfer)
- Kernel execution
- Transfer from device
- Data unmarshalling (converting back to pipeline format)
- Any synchronization overhead

**Not just kernel execution.** Kernel-only benchmarks are misleading because they exclude the overhead that dominates real-world performance.

### 2. Throughput Under Sustained Load

Peak throughput during a single burst tells you little about production behavior. Measure throughput over sustained operation:

- Run for at least 60 seconds continuously.
- Report p50, p95, and p99 latency, not just mean.
- Measure throughput degradation over time (thermal throttling, memory fragmentation, driver state accumulation).

### 3. The Comparison Baseline

The baseline must be **a well-optimized CPU implementation**, not a naive one. If you compare an FPGA implementation against an unoptimized single-threaded CPU loop, you are benchmarking your CPU optimization effort, not the FPGA's advantage.

A fair baseline includes:
- Compiler optimization (`-O3 -march=native` or equivalent).
- Appropriate use of SIMD intrinsics where the workload permits.
- Multithreading if the workload is parallelizable.
- Cache-friendly memory access patterns.

### 4. Total Cost of Ownership

Performance per dollar matters more than raw performance in most production contexts. Include:

- Hardware cost (instance cost, device cost).
- Engineering time for integration and maintenance.
- Operational cost (monitoring, incident response, team training).
- Opportunity cost (what else could the team have built?).

---

## Common Benchmark Lies

These are patterns that produce impressive but misleading numbers. If you see these in a benchmark report (or catch yourself doing them), the results should be treated with skepticism.

**"We measured kernel throughput."**
This excludes transfer overhead, which may dominate end-to-end latency. Always report system-level throughput alongside kernel throughput.

**"We compared against a naive CPU baseline."**
A single-threaded, unoptimized CPU loop is not a fair baseline for a pipelined, parallelized accelerator. Optimize the CPU path first, then compare.

**"We used batch size X."**
Large batches amortize transfer overhead and inflate throughput numbers. Report performance across a range of batch sizes, including sizes that are representative of your actual pipeline.

**"We used synthetic, perfectly regular data."**
Real data has irregularities — null fields, variable-length records, out-of-range values. If the benchmark uses perfectly uniform synthetic data, it overstates performance on real workloads.

**"We report peak throughput."**
Sustained throughput under continuous load is the relevant metric. Peak throughput during a single burst says little about production behavior.

**"We excluded warm-up time."**
FPGA bitstream loading, driver initialization, and device memory allocation are real costs that production systems pay. Either include them or document them separately.

---

## Benchmark Reporting Template

For any acceleration benchmark, report these fields:

```
Workload:           [description of what is being computed]
Input data:         [size, format, source (synthetic/real), regularity]
Batch size:         [records per batch, and range tested]
Duration:           [total benchmark runtime]

CPU Baseline:
  Hardware:         [CPU model, core count, clock speed]
  Optimization:     [compiler flags, SIMD usage, thread count]
  Throughput:       [mean, p50, p95, p99]
  Latency:          [per-record or per-batch, same percentiles]

Accelerated Path:
  Hardware:         [device model, memory, interface]
  Transfer time:    [H2D, D2H, separately]
  Kernel time:      [compute only]
  Overhead:         [marshalling, synchronization, driver]
  Total time:       [end-to-end, including all overhead]
  Throughput:       [system-level, same percentiles]

System-Level Comparison:
  Speedup:          [accelerated / baseline, end-to-end]
  Cost ratio:       [$/throughput for each path]
  Integration cost: [estimated person-weeks, referencing cost model]
```

---

## A Note on Reproducibility

If possible, make your benchmark code and data publicly available. If the data is proprietary, provide a synthetic generator that produces data with the same statistical properties (field distributions, null rates, record length distribution).

Benchmarks that cannot be reproduced cannot be verified. In the context of acceleration decisions — where the cost of a wrong decision is months of engineering time — reproducibility matters.

---

*This document is part of the [hardware-acceleration-in-data-pipelines](../README.md) repository.*
