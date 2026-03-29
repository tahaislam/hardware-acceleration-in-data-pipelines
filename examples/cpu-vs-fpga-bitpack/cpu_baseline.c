#define _POSIX_C_SOURCE 199309L

/*
 * cpu_baseline.c
 *
 * Baseline CPU implementation of bitfield packing for sensor telemetry records.
 *
 * Each input record has 8 fields with the following bit widths:
 *   field[0]:  4 bits   (sensor_type)
 *   field[1]:  3 bits   (priority)
 *   field[2]: 12 bits   (reading_a)
 *   field[3]: 12 bits   (reading_b)
 *   field[4]:  8 bits   (quality_flag)
 *   field[5]:  5 bits   (region_id)
 *   field[6]:  5 bits   (channel)
 *   field[7]:  3 bits   (reserved)
 *   ──────────────────
 *   Total:    52 bits → packed into 7 bytes (56 bits, 4 bits padding)
 *
 * This is a simplified, non-proprietary example intended to demonstrate
 * the structure of a packing kernel, not to represent any real telemetry format.
 *
 * Compile: gcc -O3 -march=native -o bitpack cpu_baseline.c
 * Run:     ./bitpack
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define NUM_FIELDS     8
#define NUM_RECORDS    1000000
#define OUTPUT_BYTES   7          /* ceil(52 / 8) = 7 */
#define ITERATIONS     10

/* Bit widths for each field */
static const int BIT_WIDTHS[NUM_FIELDS] = { 4, 3, 12, 12, 8, 5, 5, 3 };

/* Bit offset (MSB-first packing) for each field, precomputed */
static const int BIT_OFFSETS[NUM_FIELDS] = { 0, 4, 7, 19, 31, 39, 44, 49 };

/*
 * Pack a single record's fields into a 7-byte output buffer.
 *
 * This is the "kernel" — the function that an accelerator would replace.
 * It is deliberately simple: shifts, masks, ORs, no allocation, no branching.
 */
static inline void pack_record(const uint16_t fields[NUM_FIELDS],
                               uint8_t output[OUTPUT_BYTES])
{
    /*
     * Accumulate into a 64-bit integer (we only use 52 bits),
     * then extract bytes. This avoids byte-boundary bookkeeping.
     */
    uint64_t packed = 0;

    for (int i = 0; i < NUM_FIELDS; i++) {
        uint64_t value = (uint64_t)(fields[i]) & ((1ULL << BIT_WIDTHS[i]) - 1);
        packed |= value << (56 - BIT_OFFSETS[i] - BIT_WIDTHS[i]);
    }

    /* Extract 7 bytes, MSB first */
    for (int b = 0; b < OUTPUT_BYTES; b++) {
        output[b] = (uint8_t)(packed >> (8 * (OUTPUT_BYTES - 1 - b)));
    }
}

/*
 * Generate synthetic input data.
 * Values are random but masked to valid bit widths.
 */
static void generate_input(uint16_t *records, int num_records)
{
    srand(42);  /* Deterministic for reproducibility */
    for (int r = 0; r < num_records; r++) {
        for (int f = 0; f < NUM_FIELDS; f++) {
            uint16_t mask = (1 << BIT_WIDTHS[f]) - 1;
            records[r * NUM_FIELDS + f] = (uint16_t)(rand()) & mask;
        }
    }
}

/*
 * Return wall-clock time in seconds (monotonic).
 */
static double now_seconds(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

int main(void)
{
    /* Allocate input and output buffers */
    uint16_t *input  = malloc(NUM_RECORDS * NUM_FIELDS * sizeof(uint16_t));
    uint8_t  *output = malloc(NUM_RECORDS * OUTPUT_BYTES);

    if (!input || !output) {
        fprintf(stderr, "Allocation failed\n");
        return 1;
    }

    generate_input(input, NUM_RECORDS);

    /* Warm-up run (populate caches, trigger any lazy allocation) */
    for (int r = 0; r < NUM_RECORDS; r++) {
        pack_record(&input[r * NUM_FIELDS], &output[r * OUTPUT_BYTES]);
    }

    /* Timed runs */
    double total_time = 0.0;

    for (int iter = 0; iter < ITERATIONS; iter++) {
        memset(output, 0, NUM_RECORDS * OUTPUT_BYTES);

        double t0 = now_seconds();
        for (int r = 0; r < NUM_RECORDS; r++) {
            pack_record(&input[r * NUM_FIELDS], &output[r * OUTPUT_BYTES]);
        }
        double t1 = now_seconds();

        double elapsed = t1 - t0;
        total_time += elapsed;
        printf("Iteration %2d: %.4f ms  (%.2f M records/sec)\n",
               iter + 1, elapsed * 1000.0,
               NUM_RECORDS / elapsed / 1e6);
    }

    double avg = total_time / ITERATIONS;
    printf("\nAverage over %d iterations: %.4f ms  (%.2f M records/sec)\n",
           ITERATIONS, avg * 1000.0, NUM_RECORDS / avg / 1e6);
    printf("Per-record average: %.1f ns\n", avg / NUM_RECORDS * 1e9);

    /* Sanity check: print first packed record */
    printf("\nFirst record packed output: ");
    for (int b = 0; b < OUTPUT_BYTES; b++) {
        printf("%02x ", output[b]);
    }
    printf("\n");

    free(input);
    free(output);
    return 0;
}
