
import random
import time
import threading

import redis

from redis_config import TEMPERATURE_QUEUE_KEY

# How often a new reading is produced (seconds)
GENERATION_INTERVAL: float = 3.0

# Valid temperature range for this sensor
TEMP_MIN: float = -10.0
TEMP_MAX: float = 40.0


class TemperatureGenerator:
    """
    Generates random temperature readings and pushes them to a Redis list.

    Parameters
    ----------
    redis_client : redis.Redis
        Connected Redis client used to push readings.
    temp_key : str
        Redis key for the temperature queue list.
    interval : float
        Seconds between readings (default 3).
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        temp_key: str = TEMPERATURE_QUEUE_KEY,
        interval: float = GENERATION_INTERVAL,
    ):
        self._redis = redis_client
        self._temp_key = temp_key
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
        """Push a single temperature reading onto the Redis queue."""
        self._redis.rpush(self._temp_key, str(temperature))

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
    from redis_config import make_redis_client

    generator = TemperatureGenerator(make_redis_client())
    generator.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        generator.stop()
        print("\n[Generator] Stopped.")
