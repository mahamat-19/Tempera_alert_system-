
import threading

import redis

from redis_config import TEMPERATURE_QUEUE_KEY, ALERT_QUEUE_KEY

# Thresholds that define an abnormal reading
ABNORMAL_LOW: float = -5.0
ABNORMAL_HIGH: float = 35.0

# Number of abnormal readings that triggers one alert
ALERT_THRESHOLD: int = 5


class TemperatureProcessor:
    """
    Reads temperature readings from a Redis list, identifies abnormal values,
    and dispatches an alert after every ALERT_THRESHOLD abnormal readings.

    Parameters
    ----------
    redis_client : redis.Redis
        Connected Redis client used for both reading and writing.
    temp_key : str
        Redis key to consume temperature readings from (blpop).
    alert_key : str
        Redis key to push alert messages to (rpush).
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        temp_key: str = TEMPERATURE_QUEUE_KEY,
        alert_key: str = ALERT_QUEUE_KEY,
    ):
        self._redis = redis_client
        self._temp_key = temp_key
        self._alert_key = alert_key
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
        Side-effect-free regarding threading so it can be called in unit tests.
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
        """Build and push an alert message to the Redis alert queue."""
        self._total_alerts_sent += 1
        message = (
            f"ALERT: {ALERT_THRESHOLD} abnormal temperature readings "
            f"have been detected. "
            f"(Total abnormal so far: {self._abnormal_count})"
        )
        self._redis.rpush(self._alert_key, message)
        print("[Processor] Alert dispatched → alert_queue")

    def _run(self) -> None:
        """Main loop: blocking pop from Redis, process each reading."""
        while not self._stop_event.is_set():
            # blpop returns (key, value) or None on timeout
            result = self._redis.blpop(self._temp_key, timeout=1)
            if result is None:
                continue
            _, raw = result
            self.process_reading(float(raw))


# ---------------------------------------------------------------------------
# Stand-alone entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import time
    from redis_config import make_redis_client

    processor = TemperatureProcessor(make_redis_client())
    processor.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        processor.stop()
        print("\n[Processor] Stopped.")
