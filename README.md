# Hardware Acceleration in Data Pipelines

**A systems-level decision framework for evaluating GPU, FPGA, and custom accelerator integration in production data infrastructure.**

Companion repository to the Medium article:
*"Why Most Data Pipelines Shouldn't Use FPGAs — and When They Should."*

---

## What This Repository Is

This is not an FPGA tutorial. It is not a vendor showcase. It does not contain proprietary code.

This repository presents a structured, experience-informed framework for reasoning about **when and whether hardware acceleration belongs in your data pipeline** — and what it actually costs when it does.

It is aimed at engineers who have already read the marketing material and now need to make real architectural decisions under real constraints: team skill availability, integration surface area, observability requirements, and total cost of ownership.

## What This Repository Is Not

- Not a micro-benchmark suite (those are plentiful and often misleading)
- Not an HLS/RTL tutorial (Xilinx and Intel have extensive documentation)
- Not a product recommendation
- Not a claim that FPGAs are always wrong or always right

## Who This Is For

- Data and ML infrastructure engineers evaluating acceleration options
- Performance engineers reasoning about end-to-end throughput vs. kernel speedup
- Staff/Principal engineers making build-vs-buy and architecture decisions
- Anyone tired of seeing "100x speedup" claims without integration context

## Repository Structure

```
hardware-acceleration-in-data-pipelines/
│
├── README.md                          # You are here
│
├── docs/
│   ├── acceleration-decision-framework.md   # Core decision framework
│   ├── integration-cost-model.md            # Hidden costs taxonomy
│   └── observability-gaps.md                # What you lose when you offload
│
├── diagrams/
│   ├── pipeline-acceleration-zones.svg      # Where acceleration fits in a pipeline
│   ├── decision-tree.svg                    # When to accelerate (and when not to)
│   └── integration-surface-area.svg         # The iceberg of integration work
│
├── examples/
│   └── cpu-vs-fpga-bitpack/                 # Worked example: bitfield packing
│       ├── README.md                        # Problem statement and context
│       ├── cpu_baseline.c                   # Pure C implementation (compiles and runs)
│       ├── hls_sketch.cpp                   # HLS-style sketch (non-synthesizable)
│       ├── Makefile                         # Build and run the baseline
│       └── analysis.md                      # Trade-off analysis and discussion
│
├── tools/
│   └── crossover_analysis.py               # Interactive acceleration crossover explorer
│
├── benchmarks/
│   └── methodology.md                       # How to benchmark acceleration honestly
│
├── CONTRIBUTING.md
└── LICENSE
```

### Why This Structure

| Directory | Purpose | Design Rationale |
|-----------|---------|------------------|
| `docs/` | Long-form decision frameworks and analysis | Separates conceptual content from code. These are the documents engineers actually need when making architecture decisions. |
| `diagrams/` | Architectural and decision diagrams | Visual artifacts referenced by docs. SVG for version control and editability. |
| `examples/` | Small, self-contained, non-proprietary code | Demonstrates trade-offs concretely without exposing real workloads. Each example is a self-contained directory with its own README and analysis. |
| `tools/` | Runnable analysis utilities | Parameterized scripts that let engineers explore trade-offs with their own numbers. |
| `benchmarks/` | Methodology only — not raw numbers | Raw benchmark numbers without methodology are misleading. This documents *how* to measure, not *what* we measured. |

## Key Principles

1. **End-to-end reasoning over kernel speedup.** A 50x kernel speedup inside a pipeline bottlenecked by I/O serialization is a 1x pipeline speedup.

2. **Integration cost is the dominant cost.** The accelerator kernel is the easy part. Driver compatibility, data marshalling, failure handling, CI/CD integration, team ramp-up — these dominate real-world timelines.

3. **Observability is non-negotiable.** If you cannot trace a request through the accelerated path with the same fidelity as the CPU path, you have created a black box in production.

4. **Acceleration is a spectrum.** The decision is not "CPU vs. FPGA." It is "where on the spectrum of {algorithmic optimization → SIMD → GPU → FPGA → ASIC} does the return on complexity peak for this workload, this team, and this operational environment?"

5. **Vendor neutrality is a design requirement.** Architectures that couple to a specific accelerator vendor's runtime or memory model become liabilities when that vendor's roadmap diverges from yours.

## How to Read This Repository

**If you are evaluating whether to accelerate:**
Start with [`docs/acceleration-decision-framework.md`](docs/acceleration-decision-framework.md).

**If you have already decided to accelerate and are planning integration:**
Read [`docs/integration-cost-model.md`](docs/integration-cost-model.md) and [`docs/observability-gaps.md`](docs/observability-gaps.md).

**If you want to see a concrete trade-off example:**
See [`examples/cpu-vs-fpga-bitpack/`](examples/cpu-vs-fpga-bitpack/).

**If you want to explore crossover points with your own numbers:**
Run [`tools/crossover_analysis.py`](tools/crossover_analysis.py).

**If you are designing benchmarks for an acceleration proposal:**
See [`benchmarks/methodology.md`](benchmarks/methodology.md).

## Quick Start

```bash
# Build and run the CPU baseline example
cd examples/cpu-vs-fpga-bitpack
make run

# Explore acceleration crossover points
pip install matplotlib numpy
python tools/crossover_analysis.py
```

## Related

- Medium article: *"Why Most Data Pipelines Shouldn't Use FPGAs — and When They Should."* (link TBD)

## Author

[Islam Taha](https://linkedin.com/in/taha-islam) — Data & Platform Engineer with a background in hardware/software co-design (FPGA, HLS, embedded systems) and production data infrastructure (Python, Airflow, PostgreSQL, cloud deployments).

## License

[MIT](LICENSE)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Contributions that add vendor-neutral analysis, real-world integration experience, or architectural diagrams are especially welcome.
