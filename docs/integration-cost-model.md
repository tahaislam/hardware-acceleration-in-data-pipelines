# Integration Cost Model

**A taxonomy of the costs that acceleration proposals typically undercount.**

---

## Overview

When an engineer proposes hardware acceleration for a pipeline stage, the proposal typically includes the kernel performance improvement and sometimes the hardware cost. It rarely includes a complete accounting of the integration, operational, and organizational costs.

This document catalogs those costs — not to discourage acceleration, but to ensure that proposals are evaluated against a complete picture.

---

## Cost Categories

### 1. Data Marshalling and Memory Management

The accelerator operates on data in a specific format, in a specific memory space. Your pipeline's data is almost certainly not in that format or that memory space.

**Costs include:**
- Serialization/deserialization between pipeline formats and accelerator input format.
- DMA buffer allocation and lifecycle management (pinned memory, huge pages, device memory).
- Zero-copy optimization work (aligning pipeline memory layouts to avoid copies).
- Handling of variable-length records, nulls, and edge cases in the marshalling layer.

**Why this is underestimated:** Engineers often prototype with small, regular, pre-formatted data. Production data is irregular, and the marshalling layer must handle every edge case the pipeline handles.

### 2. Error Handling and Fallback

The accelerated path introduces failure modes that do not exist in the CPU path.

**New failure modes include:**
- Device driver crashes or hangs.
- Device memory exhaustion (separate from host memory).
- Thermal throttling or power limiting (especially on shared cloud instances).
- Bitstream corruption or version mismatch (FPGA-specific).
- CUDA context errors or GPU reset events (GPU-specific).
- Timeout on kernel completion (how long do you wait before declaring failure?).

**Fallback requirements:**
- A CPU path that produces identical (or acceptably close) results.
- A switching mechanism that is itself reliable and observable.
- Testing of the fallback path under load (not just functional correctness).

### 3. Testing Infrastructure

Testing an accelerated path requires infrastructure beyond standard CI.

**What you need:**
- Accelerator hardware in CI (or a robust emulation/simulation layer).
- Bit-exact comparison tests between CPU and accelerated paths.
- Performance regression tests (not just correctness).
- Fault injection tests (what happens when the device is unavailable, slow, or returns garbage?).
- Cross-compilation and bitstream build pipelines (for FPGAs).

**What this costs:** CI runners with GPUs or FPGAs are significantly more expensive than standard runners. FPGA synthesis can take hours per build. Most teams underinvest here and discover the gap when a regression ships to production.

### 4. CI/CD and Deployment

Deploying accelerated code is not the same as deploying software.

**FPGA-specific costs:**
- Bitstream versioning and compatibility management.
- Deployment tooling that handles FPGA flashing alongside software deployment.
- Rollback procedures (re-flashing takes minutes, not milliseconds).
- Instance type constraints (your deployment target must have the right accelerator).

**GPU-specific costs:**
- Driver version management across the fleet.
- CUDA/cuDNN version compatibility matrices.
- Container configuration for GPU passthrough.

### 5. Observability

See [Observability Gaps](observability-gaps.md) for a full treatment. The short version: your existing monitoring stack cannot see inside the accelerator. Building that visibility is a project in itself.

### 6. Team Ramp-Up and Knowledge Distribution

**The bus-factor problem:** If only one engineer understands the accelerated path, that path is a liability. Ramp-up costs include training, documentation, and pair programming time.

**Ongoing cost:** The accelerated path must be maintained alongside the CPU path. Bug fixes, feature changes, and performance tuning must be applied to both. This is not a one-time cost — it is a permanent tax on development velocity.

---

## Cost Estimation Template

For any acceleration proposal, fill in this template before committing:

| Cost Category | Estimated Effort (person-weeks) | Confidence | Notes |
|---|---|---|---|
| Kernel implementation | | | |
| Data marshalling | | | |
| Error handling + fallback | | | |
| Testing infrastructure | | | |
| CI/CD integration | | | |
| Observability | | | |
| Documentation + ramp-up | | | |
| **Total initial integration** | | | |
| Ongoing maintenance (per quarter) | | | |

Compare this total against the cost of achieving similar gains through CPU optimization, architectural changes, or scaling horizontally.

---

## The 15/85 Rule (Opinion, Based on Experience)

In projects I have been involved with or studied closely, the kernel implementation represented roughly 15% of the total effort. The remaining 85% was everything in this document.

This ratio is not universal, but it is a useful corrective to proposals that budget engineering time based on "how long it takes to get the kernel working." Getting the kernel working is the beginning, not the end.

---

*This document is part of the [hardware-acceleration-in-data-pipelines](../README.md) repository.*
