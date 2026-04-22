# Temperature Alert System

A multi-threaded Python application that simulates real-time temperature monitoring using message queues. Three independent clients communicate through point-to-point queues to generate, process, and report abnormal temperature readings.

---

## How It Works

```text
[Client 1: Generator] → temperature_queue → [Client 2: Processor] → alert_queue → [Client 3: Reporter]
```

| Component | Role |
| --- | --- |
| **Client 1 — Generator** | Produces a random temperature reading (°C) every 3 seconds and puts it on `temperature_queue` |
| **Client 2 — Processor** | Reads from `temperature_queue`, counts abnormal readings (below -5 °C or above 35 °C), and sends an alert to `alert_queue` after every 5 abnormals |
| **Client 3 — Reporter** | Reads from `alert_queue` and prints the alert to the console |

Each client runs in its own daemon thread. The system shuts down cleanly on `Ctrl+C`.

---

## Project Structure

```text
temperature_alert_system/
├── main.py                  # Entry point — launches all three clients
├── shared_queues.py         # Defines temperature_queue and alert_queue
├── client1_generator.py     # Component 1: Temperature Generation Client
├── client2_processor.py     # Component 2: Temperature Monitoring Processor
├── client3_reporter.py      # Component 3: Alert Reporting Client
├── requirements.txt         # Project dependencies
└── tests/
    ├── test_generator.py    # Tests for Client 1
    ├── test_processor.py    # Tests for Client 2
    └── test_reporter.py     # Tests for Client 3
```

---

## Requirements

- Python 3.8+

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/temperature_alert_system.git
cd temperature_alert_system
```

### 2. (Optional) Create and activate a virtual environment

```bash
# Create
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Application

```bash
python main.py
```

Press `Ctrl+C` to stop all clients gracefully.

**Example output:**

```text
============================================================
   Temperature Alert System — starting up
   Press Ctrl+C to stop
============================================================

[Reporter]  Starting — listening on alert_queue.
[Processor] Starting — monitoring temperature_queue.
[Generator] Starting — will produce a reading every 3.0s.
[Generator] Sent temperature reading: 12.45 °C
[Processor] Received 12.45 °C — normal
[Generator] Sent temperature reading: 36.80 °C
[Processor] Received 36.80 °C — ABNORMAL
[Processor] Abnormal count: 1
...
============================================================
  ⚠  ALERT: 5 abnormal temperature readings have been detected.
============================================================
```

---

## Running the Tests

```bash
# Recommended (works on all platforms, no PATH issues)
python -m pytest tests/ -v

# If pytest.exe is in your PATH
pytest tests/ -v
```

**Run a specific test file:**

```bash
python -m pytest tests/test_generator.py -v
python -m pytest tests/test_processor.py -v
python -m pytest tests/test_reporter.py -v
```

**Run a specific test class or test:**

```bash
python -m pytest tests/test_processor.py::TestIsAbnormal -v
python -m pytest tests/test_processor.py::TestAlertDispatching::test_alert_sent_at_threshold -v
```

**Run with summary (no verbose):**

```bash
python -m pytest tests/
```

**Expected result: 42 tests passed.**

---

## Running Individual Clients (standalone)

Each client can be run on its own for debugging:

```bash
python client1_generator.py   # generates and prints readings
python client2_processor.py   # listens on temperature_queue
python client3_reporter.py    # listens on alert_queue
```

---

## Temperature Thresholds

| Parameter | Value |
| --- | --- |
| Generation range | -10 °C to 40 °C |
| Normal range | -5 °C to 35 °C |
| Abnormal (triggers count) | below -5 °C or above 35 °C |
| Alert sent after | every 5 abnormal readings |
| Reading interval | every 3 seconds |

---

## Test Coverage

| Area | Test Class |
| --- | --- |
| Temperature generation range and randomness | `TestGenerateTemperature` |
| Queue send / receive correctness | `TestSendTemperature`, `TestGeneratorThread` |
| Abnormal reading identification (boundary & parametrized) | `TestIsAbnormal` |
| Abnormal counter accumulation | `TestAbnormalCounter` |
| Alert dispatch after every 5 abnormals | `TestAlertDispatching` |
| Console output and separator formatting | `TestReportAlert` |
| Reporter thread reads queue correctly | `TestReporterThread` |
