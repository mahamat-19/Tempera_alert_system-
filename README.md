# Temperature Alert System

A multi-threaded Python application that simulates real-time temperature monitoring using message queues.

---

## How the Data Flows

```text
Generator → temperatureQueue → Processor → alertQueue → Reporter
```

---

## Component 1: Temperature Generator

### What it does

- Connects to `temperatureQueue`
- Every 3 seconds, sends a random number
- Temperature range: -10 to 40 °C

### Example messages

```text
12
-3
37
-8
```

> This component only sends messages, it never reads anything.

---

## Component 2: Monitoring Processor

This is the brain of the system.

### Processor responsibilities

- Reads messages from `temperatureQueue`
- Checks if temperature is abnormal

### Abnormal conditions

- Below -5 °C
- Above 35 °C

So:

```text
-6 → abnormal ❌
36 → abnormal ❌
10 → normal  ✅
```

### Important logic

It must count abnormal readings:

- Keep a counter
- Every time you detect abnormal → increment counter
- When counter reaches 5:
  - Send message to `alertQueue`
  - Reset counter back to 0

### Example flow

Temperatures received:

```text
10  → normal
37  → abnormal (1)
-7  → abnormal (2)
36  → abnormal (3)
-8  → abnormal (4)
38  → abnormal (5) → SEND ALERT
```

Then reset counter.

---

## Component 3: Alert Reporter

### Reporter responsibilities

- Reads from `alertQueue`
- Prints message to console

### Example output

```text
5 abnormal temperature readings have been detected.
```

> This component does not process data, just displays alerts.

---

## Key Concepts You're Practicing

### 1. Message Queues

- Decouples components (they don't know about each other directly)
- Common tools: RabbitMQ, Kafka, ActiveMQ

### 2. Point-to-Point Communication

- `temperatureQueue` is consumed by only one processor
- Messages are not duplicated

### 3. Event-driven Logic

- Processor reacts when messages arrive
- Reporter reacts when alerts arrive

---

## What You Need to Make Sure Works (Tests)

### Sending & receiving messages

- Generator actually sends
- Processor actually receives
- Reporter actually receives alerts

### Correct abnormal detection

Make sure your condition is EXACT:

```text
temp < -5  OR  temp > 35
```

### Correct counting logic

- Count only abnormal values
- Send alert exactly at 5
- Reset counter after sending

---

## Common Mistakes

- Counting normal values too
- Forgetting to reset counter after 5
- Wrong condition (e.g., using ≤ instead of <)
- Sending alert too early or too late

---

## Simple Mental Model

```text
🌡️ Sensor      →  sends data
🧠 Controller  →  checks & counts
🚨 Alarm       →  announces problems
```

---

## Project Structure

```text
temperature_alert_system/
├── main.py                  # Entry point — launches all three clients
├── shared_queues.py         # Defines temperature_queue and alert_queue
├── client1_generator.py     # Component 1: Temperature Generator
├── client2_processor.py     # Component 2: Monitoring Processor
├── client3_reporter.py      # Component 3: Alert Reporter
└── tests/
    ├── test_generator.py    # Tests for Component 1
    ├── test_processor.py    # Tests for Component 2
    └── test_reporter.py     # Tests for Component 3
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
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
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

---

## Running the Tests

```bash
python -m pytest tests/ -v
```

Run a specific component:

```bash
python -m pytest tests/test_generator.py -v
python -m pytest tests/test_processor.py -v
python -m pytest tests/test_reporter.py -v
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
