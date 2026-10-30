# ChronosMatch — Zero-Copy High-Frequency Trading Engine

## Project Overview

ChronosMatch is an educational low-latency trading-engine prototype exploring memory-mapped communication, Cython-based order matching, and performance measurement.

The project investigates how shared-memory techniques can reduce serialization overhead and how compiled Cython code can improve matching-engine performance compared with a pure Python implementation.

**Domain:** FinTech and Low-Latency Systems

## Current Features

- **Order model:** Represents buy and sell orders with IDs, prices, quantities, and timestamps.
- **Order validation:** Rejects invalid order IDs, sides, prices, and quantities.
- **Memory-mapped ring buffer:** Implements fixed-capacity FIFO storage using `mmap` and `struct`.
- **Batch operations:** Supports pushing multiple orders with fewer lock acquisitions.
- **Market firehose:** Generates simulated orders asynchronously.
- **Producer-consumer pipeline:** Tests order generation, consumption, and integrity.
- **Cross-process IPC audit:** Tests the transfer of one million orders between separate Python processes using memory-mapped communication.
- **Python matching engine:** Implements limit-order matching with price-time priority.
- **Cython matching engine:** Uses C structures and typed variables to reduce Python overhead in the matching path.
- **Reusable trade buffer:** Reduces repeated memory allocation in the Cython matching engine.
- **Latency benchmark:** Measures per-order latency percentiles (p50, p95, p99) and throughput.
- **Pipeline benchmark:** Measures throughput for 100,000 orders.

## Technology Stack

- Python
- Cython
- C
- `asyncio`
- `mmap`
- `struct`
- `pytest`
- `curses` (dashboard development)

## Project Structure

```text
chronosmatch/
├── src/
│   └── chronosmatch/
│       ├── order.py
│       ├── ring_buffer.py
│       └── matching_core.pyx
├── tests/
├── matching_engine.py
├── benchmark_pipeline.py
├── benchmark_matching.py
├── benchmark_latency.py
├── setup_matching_core.py
├── dashboard.py
├── README.md
└── .gitignore
```

## Setup

Open PowerShell in the project directory.

Activate the existing virtual environment:

```powershell
..\.venv\Scripts\Activate.ps1
```

Install the required packages if needed:

```powershell
python -m pip install --upgrade pip
python -m pip install cython setuptools pytest
```

## Building the Cython Engine

From the project root, run:

```powershell
python setup_matching_core.py build_ext --inplace
```

This compiles the Cython matching engine into a Python extension module.

## Running Tests

Set the source directory on the Python path:

```powershell
$env:PYTHONPATH = "$PWD\src"
```

Run the test suite:

```powershell
python -m pytest -q
```

The latest confirmed complete test run passed all 31 tests, including the mmap IPC and Cython matching integration test.

## Benchmark Results

The following are local development measurements. Results depend on hardware, operating-system scheduling, Python version, and benchmark implementation.

### 1. 100,000-Order Pipeline Benchmark

| Run | Orders | Elapsed time | Throughput |
|---|---:|---:|---:|
| 1 | 100,000 | 0.5964 s | 167,684 orders/s |
| 2 | 100,000 | 0.3877 s | 257,946 orders/s |
| 3 | 100,000 | 0.4335 s | 230,692 orders/s |
| Average | 100,000 per run | — | 218,774 orders/s |

Run:

```powershell
python benchmark_pipeline.py
```

### 2. Python vs Cython Matching Benchmark

Recorded local benchmark:

| Metric | Python | Cython |
|---|---:|---:|
| Average execution time | 0.030662 s | 0.003478 s |
| Throughput | 19,699 orders/s | 173,653 orders/s |

Measured speed ratio: approximately 8.82x.

Run:

```powershell
$env:PYTHONPATH = "$PWD\src"
python benchmark_matching.py
```

The benchmark also checks that trade results and final order books match.

### 3. Per-Order Latency Benchmark

Recorded middle-trial measurements for 5,000 orders:

| Metric | Python | Cython |
|---|---:|---:|
| p50 latency | 43.9 µs | 1.2 µs |
| p95 latency | 104.8 µs | 1.6 µs |
| p99 latency | 189.4 µs | 1.9 µs |
| Maximum observed | 583.6 µs | 13.4 µs |
| Throughput | 20,164 orders/s | 726,702 orders/s |

Aggregate throughput across five trials:

- Python: 19,516 orders/s
- Cython: 634,708 orders/s
- Measured throughput ratio: 32.52x

Run:

```powershell
$env:PYTHONPATH = "$PWD\src"
python benchmark_latency.py
```

Per-order measurements include Python-call and timer overhead. These results are local benchmark observations, not production HFT latency guarantees.

### 4. One-Million-Order IPC Audit

Recorded local cross-process benchmark:

| Metric | mmap IPC | Pickle baseline |
|---|---:|---:|
| Orders transferred | 1,000,000 | 1,000,000 |
| Elapsed time | 40.941 s | 51.895 s |
| Throughput | 24,425 orders/s | 19,270 orders/s |

The mmap test used a ring-buffer capacity of 4,096 and batches of 256 orders. Data-integrity checks passed.

These measurements describe the tested implementation and environment; they are not universal performance comparisons.
### 5. Batch IPC and Cython Matching Benchmark

This benchmark transfers 10,000 orders between separate Python processes and processes them using the Cython matching engine.

Original single-order IPC measurement:

| Mode | Elapsed time | Throughput |
|---|---:|---:|
| Single-order operations | 21.695360 s | 461 orders/s |

Batch IPC measurements using a batch size of 512:

| Trial | Elapsed time | Throughput |
|---|---:|---:|
| 1 | 1.385881 s | 7,216 orders/s |
| 2 | 1.197580 s | 8,350 orders/s |
| 3 | 1.356586 s | 7,371 orders/s |
| Average | 1.313 s | 7,646 orders/s |

Measured throughput improvement over the original single-order benchmark: approximately 16.6x.

Run:

```powershell
$env:PYTHONPATH = "$PWD\src"
python benchmark_ipc_cython.py

## Current Limitations

- The matching engine is a prototype, not a production exchange engine.
- The mutable Cython matching engine is not thread-safe without external synchronization.
- Local benchmark results do not establish worst-case latency guarantees.
- End-to-end latency under 50 microseconds has not been established for the complete system.
- Additional stress testing, process synchronization checks, and failure-recovery tests are needed before production use.
- The terminal dashboard requires further integration and validation.

## Next Development Goals

1. Integrate the IPC pipeline with the Cython matching engine.
2. Verify order-book correctness under larger and more varied workloads.
3. Improve C-level performance and reduce Python interactions in critical paths.
4. Integrate the real-time terminal latency dashboard.
5. Add stress, concurrency, and failure-recovery tests.
6. Improve reproducibility of benchmarks and document hardware/software details.

## Project Status

**Completed development milestones:** Order validation, mmap ring buffer, batch ring-buffer operations, producer-consumer tests, 100,000-order pipeline benchmark, one-million-order IPC audit, Cython matching engine, reusable trade buffer, matching correctness checks, mmap IPC and Cython integration, per-order latency benchmarking, and batch IPC benchmark optimization.

ChronosMatch is an educational prototype under active development. Performance claims are reported as measured local results and should not be interpreted as guarantees for production trading systems.