# Observability Gaps in Accelerated Pipelines

**What you lose when you offload compute — and how to get it back.**

---

## The Observability Contract

In a well-instrumented data pipeline, every record's journey is traceable: when it arrived, how long each stage took, what transformations were applied, and where it went. When something goes wrong, an engineer can reconstruct what happened from logs, metrics, and traces.

Hardware acceleration breaks this contract by default. The accelerator is a black box: data goes in, results come out, and the internals are not visible to your standard observability stack (OpenTelemetry, Prometheus, Datadog, or equivalent).

This is not a theoretical concern. In production, it manifests as:

- *"The pipeline is slow, but I can't tell if it's the FPGA or the DMA transfer."*
- *"Records are coming out corrupted, but I can't tell which stage introduced the error."*
- *"The accelerator appears healthy, but throughput dropped 40% and I don't know why."*

---

## What Standard Tools Cannot See

### Execution Timing Granularity

**CPU path:** You can instrument individual function calls, measure per-record latency, and profile with nanosecond resolution using `perf`, `dtrace`, or application-level timers.

**Accelerated path:** You can measure host-side wall-clock time for the entire offload operation (transfer + compute + return). You typically cannot break this down further without custom hardware instrumentation or vendor-specific profiling tools that may not integrate with your pipeline's monitoring stack.

### Internal State

**CPU path:** You can log intermediate values, add assertions, dump state on failure, and attach a debugger to a running process.

**Accelerated path:** Internal state is on the device. For GPUs, `cuda-gdb` and `nsight` provide some visibility but add overhead and complexity. For FPGAs, internal state inspection requires ILA (Integrated Logic Analyzer) cores baked into the bitstream, which consume FPGA resources and must be planned at design time — not added after a production incident.

### Error Attribution

**CPU path:** Stack traces, exception handlers, and structured logging make it straightforward to attribute errors to specific code paths.

**Accelerated path:** When the accelerator returns incorrect results, attributing the error to kernel logic vs. data marshalling vs. DMA corruption vs. driver issues requires elimination debugging across hardware-software boundaries. This is time-consuming and requires cross-domain expertise.

### Resource Utilization

**CPU path:** Standard system metrics (CPU utilization, memory usage, cache hit rates) are available from the OS and well-supported by every monitoring tool.

**Accelerated path:** GPU utilization is available through `nvidia-smi` or DCGM, but integrating it into your pipeline's dashboards requires custom exporters. FPGA utilization metrics are often limited to what the vendor's runtime exposes (if anything), and may not correlate meaningfully with application-level performance.

---

## Strategies for Closing the Gap

These are not free — each requires engineering investment. But they are the minimum for operating an accelerated pipeline in production.

### 1. Envelope Timing

Measure wall-clock time for each phase of the offload operation separately:

```
T_marshal    = time to prepare data for transfer
T_transfer_h2d = time to move data host → device
T_compute    = time from kernel launch to completion signal
T_transfer_d2h = time to move results device → host
T_unmarshal  = time to integrate results back into pipeline
```

This won't tell you what happened inside the kernel, but it will tell you *where* the time is going, which is sufficient for most production debugging.

### 2. Canary Records

Inject known-answer records into the data stream at a regular interval. Compare the accelerator's output for these records against precomputed expected results. This provides continuous correctness monitoring without full output verification.

**Design constraints:** Canary records must be representative of real data shapes (not trivial edge cases) and must be identifiable in the output stream without disrupting downstream consumers.

### 3. Shadow Mode

Run the accelerated path and the CPU fallback path simultaneously on a sample of production traffic. Compare outputs. Alert on divergence.

**Cost:** Doubles the compute for the sampled fraction. Worth it during initial deployment and as a periodic regression check.

### 4. Device Health Monitoring

Expose accelerator-level metrics (temperature, power draw, error counters, utilization) as first-class pipeline metrics alongside application metrics.

For GPUs, this means integrating DCGM or `nvidia-smi` output into your metrics pipeline. For FPGAs, this means reading device status registers through the runtime API and exporting them.

### 5. Structured Logging at Boundaries

Log entry/exit events at every host-device boundary with correlation IDs that tie into your pipeline's distributed tracing:

```json
{
  "event": "accelerator_offload",
  "correlation_id": "abc-123",
  "stage": "bitpack",
  "batch_size": 1000000,
  "t_marshal_ms": 2.3,
  "t_transfer_h2d_ms": 1.1,
  "t_compute_ms": 0.8,
  "t_transfer_d2h_ms": 0.9,
  "t_unmarshal_ms": 1.4,
  "device_id": "fpga-0",
  "canary_pass": true
}
```

This log line alone gives you enough to diagnose most production issues without touching the device internals.

---

## The Observability Tax

Building and maintaining this observability infrastructure is a non-trivial, ongoing cost. It should be included in any acceleration proposal (see the [Integration Cost Model](integration-cost-model.md)).

The alternative — operating an accelerated pipeline without this visibility — is not a cost saving. It is a deferred cost that arrives as extended incident response times, harder-to-diagnose bugs, and reduced confidence in the system.

---

*This document is part of the [hardware-acceleration-in-data-pipelines](../README.md) repository.*
