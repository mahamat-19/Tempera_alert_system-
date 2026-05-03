"""
client2_processor.py
---------------------
Component 2 – Temperature Monitoring Processor.

Exclusively reads temperature readings from temperature_queue.
A reading is ABNORMAL if it is below -5 °C or above 35 °C.
After every 5 abnormal readings an alert message is sent to alert_queue.
"""

import threading
import queue

# Thresholds that define an abnormal reading
ABNORMAL_LOW: float = -5.0
ABNORMAL_HIGH: float = 35.0

# Number of abnormal readings that triggers one alert
ALERT_THRESHOLD: int = 5


class TemperatureProcessor:
    """
    Reads temperature readings from *temp_queue*, identifies abnormal values,
    and dispatches an alert to *alert_queue* after every ALERT_THRESHOLD
    abnormal readings.

    Parameters
    ----------
    temp_queue  : queue.Queue  – source of raw temperature readings.
    alert_queue : queue.Queue  – destination for alert notifications.
    """

    def __init__(self, temp_queue: queue.Queue, alert_queue: queue.Queue):
        self._temp_queue = temp_queue
        self._alert_queue = alert_queue
        self._abnormal_count: int = 0
        self._total_alerts_sent: int = 0
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="ProcessorThread"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the processor thread."""
        print("[Processor] Starting — monitoring temperature_queue.")
        self._thread.start()

    def stop(self) -> None:
        """Signal the processor thread to stop."""
        self._stop_event.set()
        # Unblock the blocking get() so the thread can exit
        self._temp_queue.put(None)

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    @property
    def abnormal_count(self) -> int:
        """Total abnormal readings received so far."""
        return self._abnormal_count

    @property
    def total_alerts_sent(self) -> int:
        """Total alerts dispatched so far."""
        return self._total_alerts_sent

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def is_abnormal(self, temperature: float) -> bool:
        """Return True when *temperature* is outside the normal range."""
        return temperature < ABNORMAL_LOW or temperature > ABNORMAL_HIGH

    def process_reading(self, temperature: float) -> None:
        """
        Evaluate one reading and send an alert if the threshold is reached.
        This method is intentionally side-effect-free regarding threading so
        it can be called directly in unit tests.
        """
        _RED   = "\033[91m"
        _RESET = "\033[0m"

        if self.is_abnormal(temperature):
            self._abnormal_count += 1
            status = f"{_RED}ABNORMAL{_RESET}"
            print(f"[Processor] Received {temperature:.2f} °C — {status}")
            print(f"{_RED}[Processor] Abnormal count: {self._abnormal_count}{_RESET}")
            if self._abnormal_count == ALERT_THRESHOLD:
                self._send_alert()
                self._abnormal_count = 0
        else:
            print(f"[Processor] Received {temperature:.2f} °C — normal")

    def _send_alert(self) -> None:
        """Build and enqueue an alert message."""
        self._total_alerts_sent += 1
        message = (
            f"ALERT: {ALERT_THRESHOLD} abnormal temperature readings "
            f"have been detected. "
            f"(Total abnormal so far: {self._abnormal_count})"
        )
        self._alert_queue.put(message)
        print(f"[Processor] Alert dispatched → alert_queue")

    def _run(self) -> None:
        """Main loop: block on queue, process each reading."""
        while not self._stop_event.is_set():
            try:
                reading = self._temp_queue.get(timeout=1)
                if reading is None:          # sentinel sent by stop()
                    break
                self.process_reading(reading)
                self._temp_queue.task_done()
            except queue.Empty:
                continue


# ---------------------------------------------------------------------------
# Stand-alone entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import time
    from shared_queues import temperature_queue, alert_queue

    processor = TemperatureProcessor(temperature_queue, alert_queue)
    processor.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        processor.stop()
        print("\n[Processor] Stopped.")
