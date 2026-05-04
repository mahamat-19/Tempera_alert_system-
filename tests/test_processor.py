"""
tests/test_processor.py
-----------------------
Tests for Client 2 – TemperatureProcessor.

Covers:
  - Correct identification of normal vs abnormal readings.
  - Accurate accumulation of the abnormal counter.
  - Alert is pushed to Redis after every 5 abnormal readings.
  - No alert is sent before 5 abnormal readings accumulate.
  - Alert message content is correct.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fakeredis
import pytest
from client2_processor import (
    TemperatureProcessor,
    ABNORMAL_LOW,
    ABNORMAL_HIGH,
    ALERT_THRESHOLD,
)
from redis_config import ALERT_QUEUE_KEY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_processor():
    """Return a fresh processor with its own isolated fakeredis client."""
    r = fakeredis.FakeRedis()
    return TemperatureProcessor(r), r


# ---------------------------------------------------------------------------
# is_abnormal()
# ---------------------------------------------------------------------------

class TestIsAbnormal:

    def setup_method(self):
        self.proc, _ = make_processor()

    def test_normal_low_boundary(self):
        """Exactly ABNORMAL_LOW is normal (not below)."""
        assert not self.proc.is_abnormal(ABNORMAL_LOW)

    def test_normal_high_boundary(self):
        """Exactly ABNORMAL_HIGH is normal (not above)."""
        assert not self.proc.is_abnormal(ABNORMAL_HIGH)

    def test_normal_midpoint(self):
        assert not self.proc.is_abnormal(15.0)

    def test_abnormal_below_low(self):
        """Temperature just below ABNORMAL_LOW is abnormal."""
        assert self.proc.is_abnormal(ABNORMAL_LOW - 0.01)

    def test_abnormal_above_high(self):
        """Temperature just above ABNORMAL_HIGH is abnormal."""
        assert self.proc.is_abnormal(ABNORMAL_HIGH + 0.01)

    def test_very_cold(self):
        assert self.proc.is_abnormal(-10.0)

    def test_very_hot(self):
        assert self.proc.is_abnormal(40.0)

    @pytest.mark.parametrize("temp", [-5.0, 0.0, 10.0, 20.0, 35.0])
    def test_normal_range_parametrized(self, temp):
        assert not self.proc.is_abnormal(temp)

    @pytest.mark.parametrize("temp", [-5.1, -10.0, 35.1, 40.0])
    def test_abnormal_range_parametrized(self, temp):
        assert self.proc.is_abnormal(temp)


# ---------------------------------------------------------------------------
# process_reading() — counter accumulation
# ---------------------------------------------------------------------------

class TestAbnormalCounter:

    def setup_method(self):
        self.proc, self.redis = make_processor()

    def test_counter_starts_at_zero(self):
        assert self.proc.abnormal_count == 0

    def test_normal_reading_does_not_increment_counter(self):
        self.proc.process_reading(20.0)
        assert self.proc.abnormal_count == 0

    def test_abnormal_reading_increments_counter(self):
        self.proc.process_reading(36.0)
        assert self.proc.abnormal_count == 1

    def test_multiple_abnormal_readings_accumulate(self):
        for temp in [36.0, -6.0, 37.5, -7.0]:
            self.proc.process_reading(temp)
        assert self.proc.abnormal_count == 4

    def test_mixed_readings_only_abnormal_counted(self):
        readings = [20.0, 36.0, 15.0, -6.0, 10.0]   # 2 abnormal
        for t in readings:
            self.proc.process_reading(t)
        assert self.proc.abnormal_count == 2


# ---------------------------------------------------------------------------
# process_reading() — alert dispatching
# ---------------------------------------------------------------------------

class TestAlertDispatching:

    def setup_method(self):
        self.proc, self.redis = make_processor()

    def _send_abnormal(self, n: int):
        """Helper: feed n abnormal readings to the processor."""
        for _ in range(n):
            self.proc.process_reading(40.0)   # always abnormal

    def test_no_alert_before_threshold(self):
        """Fewer than ALERT_THRESHOLD abnormal readings → no alert."""
        self._send_abnormal(ALERT_THRESHOLD - 1)
        assert self.redis.llen(ALERT_QUEUE_KEY) == 0

    def test_alert_sent_at_threshold(self):
        """Exactly ALERT_THRESHOLD abnormal readings → one alert."""
        self._send_abnormal(ALERT_THRESHOLD)
        assert self.redis.llen(ALERT_QUEUE_KEY) == 1
        assert self.proc.total_alerts_sent == 1

    def test_alert_sent_every_threshold(self):
        """Two full batches → two alerts."""
        self._send_abnormal(ALERT_THRESHOLD * 2)
        assert self.proc.total_alerts_sent == 2
        assert self.redis.llen(ALERT_QUEUE_KEY) == 2

    def test_alert_message_content(self):
        """Alert message must contain the expected text."""
        self._send_abnormal(ALERT_THRESHOLD)
        message = self.redis.lpop(ALERT_QUEUE_KEY).decode()  # type: ignore
        assert "abnormal temperature readings" in message.lower()
        assert str(ALERT_THRESHOLD) in message

    def test_no_alert_for_normal_readings_only(self):
        """Sending only normal readings never triggers an alert."""
        for _ in range(ALERT_THRESHOLD * 3):
            self.proc.process_reading(20.0)
        assert self.redis.llen(ALERT_QUEUE_KEY) == 0

    def test_partial_batch_after_alert_no_extra_alert(self):
        """After one alert, 3 more abnormal readings (< threshold) = no second alert."""
        self._send_abnormal(ALERT_THRESHOLD)       # triggers alert #1
        self._send_abnormal(ALERT_THRESHOLD - 2)   # not enough for alert #2
        assert self.proc.total_alerts_sent == 1
