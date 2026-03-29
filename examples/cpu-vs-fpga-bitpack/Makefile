# Makefile for cpu-vs-fpga-bitpack example
#
# This builds and runs the CPU baseline only. The HLS sketch is
# included for architectural reference and is not compilable without
# a vendor HLS toolchain (Vitis HLS, Intel HLS, etc.).

CC       = gcc
CFLAGS   = -O3 -march=native -Wall -Wextra -std=c11
LDFLAGS  = -lrt
TARGET   = bitpack

.PHONY: all run clean

all: $(TARGET)

$(TARGET): cpu_baseline.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

run: $(TARGET)
	@echo "=== Bitfield Packing CPU Baseline ==="
	@echo "Records: 1,000,000 | Fields: 8 | Packed size: 7 bytes/record"
	@echo ""
	@./$(TARGET)

clean:
	rm -f $(TARGET)
