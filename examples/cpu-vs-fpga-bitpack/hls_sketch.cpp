/*
 * hls_sketch.cpp
 *
 * HLS-style sketch of the bitfield packing kernel.
 *
 * IMPORTANT: This is NOT synthesizable code. It is a structural sketch
 * that illustrates what an HLS implementation would look like — the pragma
 * annotations, the streaming interface pattern, and the pipelining strategy.
 *
 * It is included to help software engineers understand the *shape* of an
 * FPGA implementation without requiring HLS toolchain familiarity.
 *
 * Key differences from the CPU version:
 *
 * 1. INTERFACE: The CPU version operates on arrays in main memory.
 *    The FPGA version would use AXI memory-mapped interfaces for bulk
 *    data transfer (input_records, output_packed) and AXI-Lite for
 *    scalar control signals (num_records, return status).
 *
 * 2. PIPELINING: The CPU processes records sequentially (one at a time,
 *    one field at a time). The FPGA version uses HLS PIPELINE pragmas
 *    to overlap execution — ideally achieving initiation interval (II)
 *    of 1, meaning one new record enters the pipeline every clock cycle.
 *
 * 3. UNROLLING: Inner loops over fields and output bytes are fully
 *    unrolled — executed as parallel combinational logic, not sequential
 *    iteration. This is what gives FPGAs their throughput advantage for
 *    regular, branch-free kernels.
 *
 * The streaming pattern below is the key architectural difference:
 * - CPU version: iterate over records in memory, calling pack_record() per record
 * - FPGA version: records stream through the kernel, one per clock cycle (after
 *   pipeline fill), with no random memory access
 *
 * The host is responsible for:
 *   1. Allocating DMA-capable buffers
 *   2. Copying input data to the device (or mapping host memory)
 *   3. Starting the kernel
 *   4. Waiting for completion
 *   5. Reading results back
 *
 * Steps 1, 2, 4, and 5 are where the "hidden" time lives.
 */

#include <stdint.h>

#define NUM_FIELDS   8
#define OUTPUT_BYTES 7

static const int BIT_WIDTHS[NUM_FIELDS]  = { 4, 3, 12, 12, 8, 5, 5, 3 };
static const int BIT_OFFSETS[NUM_FIELDS] = { 0, 4, 7, 19, 31, 39, 44, 49 };


/*
 * Pack a single record — identical logic to the CPU version,
 * but with unroll pragmas to generate parallel hardware.
 */
static void pack_record_hls(const uint16_t fields[NUM_FIELDS],
                            uint8_t packed[OUTPUT_BYTES])
{
    /* #pragma HLS INLINE */

    uint64_t acc = 0;

    PACK_FIELDS:
    for (int i = 0; i < NUM_FIELDS; i++) {
        /* #pragma HLS UNROLL */
        uint64_t value = (uint64_t)(fields[i]) & ((1ULL << BIT_WIDTHS[i]) - 1);
        acc |= value << (56 - BIT_OFFSETS[i] - BIT_WIDTHS[i]);
    }

    EXTRACT_BYTES:
    for (int b = 0; b < OUTPUT_BYTES; b++) {
        /* #pragma HLS UNROLL */
        packed[b] = (uint8_t)(acc >> (8 * (OUTPUT_BYTES - 1 - b)));
    }
}


/*
 * Top-level kernel function.
 *
 * In a real HLS project, this function signature defines the hardware
 * interfaces. Each parameter maps to an AXI port on the generated IP block.
 */
void pack_batch_hls(
    const uint16_t *input_records,   /* AXI-MM or AXI-Stream in real HLS */
    uint8_t        *output_packed,   /* AXI-MM or AXI-Stream in real HLS */
    int             num_records
)
{
    /* HLS pragma: define AXI interfaces */
    /* #pragma HLS INTERFACE m_axi port=input_records  depth=8000000 */
    /* #pragma HLS INTERFACE m_axi port=output_packed  depth=7000000 */
    /* #pragma HLS INTERFACE s_axilite port=num_records */
    /* #pragma HLS INTERFACE s_axilite port=return */

    BATCH_LOOP:
    for (int r = 0; r < num_records; r++) {
        /* #pragma HLS PIPELINE II=1 */

        uint16_t fields[NUM_FIELDS];
        uint8_t  packed[OUTPUT_BYTES];

        /* Read one record from input stream */
        READ_FIELDS:
        for (int f = 0; f < NUM_FIELDS; f++) {
            /* #pragma HLS UNROLL */
            fields[f] = input_records[r * NUM_FIELDS + f];
        }

        /* Pack */
        pack_record_hls(fields, packed);

        /* Write packed output */
        WRITE_OUTPUT:
        for (int b = 0; b < OUTPUT_BYTES; b++) {
            /* #pragma HLS UNROLL */
            output_packed[r * OUTPUT_BYTES + b] = packed[b];
        }
    }
}


/*
 * ─── What This Sketch Does NOT Show ───
 *
 * 1. Host-side driver code (DMA allocation, kernel launch, synchronization)
 * 2. Error detection or recovery at the hardware level
 * 3. Observability hooks (how do you trace a record through the FPGA?)
 * 4. Multi-kernel partitioning for resource optimization
 * 5. Clock domain crossing or reset logic
 * 6. Toolchain-specific testbench and co-simulation setup
 * 7. Bitstream build and deployment infrastructure
 *
 * Each of these is a non-trivial engineering effort. Together, they constitute
 * the majority of the integration cost discussed in docs/integration-cost-model.md.
 */
