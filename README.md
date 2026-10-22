# ChronosMatch — Zero-Copy High-Frequency Trading Engine

## Project Overview

ChronosMatch is a low-latency trading-engine prototype exploring memory-mapped communication, order validation, asynchronous market-data generation, and producer-consumer pipelines using Python.

The project investigates how a fixed-layout binary buffer can reduce the overhead associated with passing structured order data between components.

**Domain:** FinTech and Low-Latency Systems

## Current Features

- **Order model:** Represents buy and sell orders with IDs, prices, quantities, and timestamps.
- **Order validation:** Rejects negative order IDs, invalid sides, non-positive prices, and non-positive quantities.
- **Memory-mapped ring buffer:** Implements fixed-capacity FIFO storage using `mmap` and `struct`.
- **Market firehose:** Generates simulated orders asynchronously.
- **Producer-consumer pipeline:** Tests order generation, consumption, and order integrity.
- **Benchmark script:** Measures throughput across three runs of 100,000 orders.

## Technology Stack

- Python
- `asyncio`
- `mmap`
- `struct`
- `unittest`
- Cython — planned for the matching-engine phase

## Project Structure

```text
chronosmatch/
├── src/
│   └── chronosmatch/
│       ├── order.py
│       ├── ring_buffer.py
│       └── firehose.py
├── tests/
├── test_order.py
├── test_invalid_orders.py
├── test_ring_buffer.py
├── test_firehose.py
├── test_pipeline.py
├── test_live_pipeline.py
├── test_serialization.py
├── benchmark_pipeline.py
├── README.md
└── .gitignore
```

## Setup

Open PowerShell in the project directory and activate the existing virtual environment:

```powershell
..\.venv\Scripts\Activate.ps1
```

If the environment has not been created, create it from the parent directory:

```powershell
cd ..
python -m venv .venv
.\.venv\Scripts\Activate.ps1
cd chronosmatch
```

## Running the Tests

Run the tests from the project root:

```powershell
python test_order.py
python test_invalid_orders.py
python test_ring_buffer.py
python test_firehose.py
python test_pipeline.py
python test_live_pipeline.py
```

The reliability checkpoint completed five repeated ring-buffer test runs and five repeated live-pipeline test runs successfully.

## Preliminary Benchmark Results

The following results were measured during development on the local machine.

### Live Pipeline

- Orders generated: 10,000
- Orders consumed: 10,000
- Elapsed time: approximately 0.1003 seconds
- Observed throughput: approximately 99,729 orders/second

### 100,000-Order Benchmark

| Run | Orders | Elapsed time | Throughput |
|---|---:|---:|---:|
| 1 | 100,000 | 0.5964 s | 167,684 orders/s |
| 2 | 100,000 | 0.3877 s | 257,946 orders/s |
| 3 | 100,000 | 0.4335 s | 230,692 orders/s |
| Average | 100,000 per run | — | 218,774 orders/s |

Run the benchmark with:

```powershell
python benchmark_pipeline.py
```

These measurements are preliminary and depend on the local machine, Python runtime, operating-system scheduling, and benchmark implementation. They are not a controlled comparison with production trading systems.

## Current Limitations

- The Cython-compiled matching engine and full limit order book are not yet implemented.
- The current live pipeline is a Python producer-consumer test, not a verified cross-process trading pipeline.
- The ring buffer has not yet been validated for safe concurrent access by independent processes.
- Throughput measurements do not establish worst-case latency or tail-latency guarantees.
- The project has not yet demonstrated the target of under 50 microseconds for end-to-end order processing.

## Next Development Phase

1. Implement a limit order book and matching rules.
2. Build and integrate a Cython-compiled matching engine.
3. Define and validate a binary IPC message format.
4. Test cross-process communication and synchronization.
5. Add stronger correctness tests and controlled latency benchmarks.
6. Develop the terminal monitoring dashboard.

## Project Status

**Week 1 checkpoint:** Order validation, memory-mapped ring-buffer tests, asynchronous order generation, pipeline integration tests, preliminary throughput benchmarks, and repeated reliability checks completed.

ChronosMatch is an educational prototype under active development. Performance claims will be updated only when supported by reproducible measurements.
