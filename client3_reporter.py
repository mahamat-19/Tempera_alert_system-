"""
client3_reporter.py
--------------------
Component 3 – Alert Reporting Client.

Reads alert messages from alert_queue and prints them to the console.
"""

import threading
import queue


class AlertReporter:
    """
    Listens on *alert_queue* and prints every alert message it receives.

    Parameters
    ----------
    alert_queue : queue.Queue  – source of alert notification strings.
    """

    def __init__(self, alert_queue: queue.Queue):
        self._queue = alert_queue
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="ReporterThread"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the reporter thread."""
        print("[Reporter] Starting — listening on alert_queue.")
        self._thread.start()

    def stop(self) -> None:
        """Signal the reporter thread to stop."""
        self._stop_event.set()
        self._queue.put(None)   # unblock blocking get()

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def report_alert(self, message: str) -> None:
        """Print one alert message. Called directly from the run loop."""
        print(f"\n{'='*60}")
        print(f"  ⚠  {message}")
        print(f"{'='*60}\n")

    def _run(self) -> None:
        """Main loop: block on queue, print every alert that arrives."""
        while not self._stop_event.is_set():
            try:
                message = self._queue.get(timeout=1)
                if message is None:   # sentinel sent by stop()
                    break
                self.report_alert(message)
                self._queue.task_done()
            except queue.Empty:
                continue


# ---------------------------------------------------------------------------
# Stand-alone entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import time
    from shared_queues import alert_queue

    reporter = AlertReporter(alert_queue)
    reporter.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        reporter.stop()
        print("\n[Reporter] Stopped.")
