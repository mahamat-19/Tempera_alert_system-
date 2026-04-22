"""
client1_generator.py
---------------------
Component 1 – Temperature Generation Client.

Connects to temperature_queue (point-to-point) and sends a randomly generated
temperature reading (°C) every 3 seconds.
Normal range: -10 °C to 40 °C.
"""

import random
import time
import threading
import queue


# How often a new reading is produced (seconds)
GENERATION_INTERVAL: float = 3.0

# Valid temperature range for this sensor
TEMP_MIN: float = -10.0
TEMP_MAX: float = 40.0


class TemperatureGenerator:
    """
    Generates random temperature readings and puts them on the given queue.

    Parameters
    ----------
    temp_queue : queue.Queue
        The destination queue for temperature readings.
    interval : float
        Seconds between readings (default 3).
    """

    def __init__(self, temp_queue: queue.Queue, interval: float = GENERATION_INTERVAL):
        self._queue = temp_queue
        self._interval = interval
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="GeneratorThread")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the generator thread."""
        print("[Generator] Starting — will produce a reading every "
              f"{self._interval}s.")
        self._thread.start()

    def stop(self) -> None:
        """Signal the generator thread to stop gracefully."""
        self._stop_event.set()

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def generate_temperature(self) -> float:
        """Return a random temperature within [TEMP_MIN, TEMP_MAX]."""
        return round(random.uniform(TEMP_MIN, TEMP_MAX), 2)

    def send_temperature(self, temperature: float) -> None:
        """Put a single temperature reading onto the queue."""
        self._queue.put(temperature)

    def _run(self) -> None:
        """Main loop: generate → send → sleep."""
        while not self._stop_event.is_set():
            temp = self.generate_temperature()
            self.send_temperature(temp)
            print(f"[Generator] Sent temperature reading: {temp:.2f} °C")
            self._stop_event.wait(self._interval)   # interruptible sleep


# ---------------------------------------------------------------------------
# Stand-alone entry-point (run this file directly to see the generator alone)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from shared_queues import temperature_queue

    generator = TemperatureGenerator(temperature_queue)
    generator.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        generator.stop()
        print("\n[Generator] Stopped.")
