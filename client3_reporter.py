

import threading

import redis

from redis_config import ALERT_QUEUE_KEY


class AlertReporter:
    """
    Listens on a Redis list and prints every alert message it receives.

    Parameters
    ----------
    redis_client : redis.Redis
        Connected Redis client used to consume alert messages.
    alert_key : str
        Redis key to consume alert messages from (blpop).
    """

    def __init__(self, redis_client: redis.Redis, alert_key: str = ALERT_QUEUE_KEY):
        self._redis = redis_client
        self._alert_key = alert_key
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

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def report_alert(self, message: str) -> None:
        """Print one alert message."""
        print(f"\n{'='*60}")
        print(f"  ⚠  {message}")
        print(f"{'='*60}\n")

    def _run(self) -> None:
        """Main loop: blocking pop from Redis, print every alert."""
        while not self._stop_event.is_set():
            # blpop returns (key, value) or None on timeout
            result = self._redis.blpop(self._alert_key, timeout=1)
            if result is None:
                continue
            _, raw = result
            self.report_alert(raw.decode())


# ---------------------------------------------------------------------------
# Stand-alone entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import time
    from redis_config import make_redis_client

    reporter = AlertReporter(make_redis_client())
    reporter.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        reporter.stop()
        print("\n[Reporter] Stopped.")
