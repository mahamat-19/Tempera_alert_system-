"""
tests/test_generator.py
-----------------------
Tests for Client 1 – TemperatureGenerator.

Covers:
  - Generated temperatures are always within [-10, 40] °C.
  - A temperature is pushed to Redis after send_temperature() is called.
  - The Redis queue is non-empty after the generator thread has had time to run.
"""

import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fakeredis
from client1_generator import TemperatureGenerator, TEMP_MIN, TEMP_MAX
from redis_config import TEMPERATURE_QUEUE_KEY


class TestGenerateTemperature:
    """Unit tests for the temperature generation logic."""

    def setup_method(self):
        self.redis = fakeredis.FakeRedis()
        self.generator = TemperatureGenerator(self.redis, interval=999)

    def test_temperature_within_range(self):
        """Generated temperature must be in [TEMP_MIN, TEMP_MAX]."""
        for _ in range(200):
            temp = self.generator.generate_temperature()
            assert TEMP_MIN <= temp <= TEMP_MAX, (
                f"Temperature {temp} is outside [{TEMP_MIN}, {TEMP_MAX}]"
            )

    def test_temperature_is_float(self):
        """Generated value must be a float."""
        temp = self.generator.generate_temperature()
        assert isinstance(temp, float)

    def test_different_values_produced(self):
        """Generator should not always return the same value."""
        readings = {self.generator.generate_temperature() for _ in range(50)}
        assert len(readings) > 1, "Expected varied readings, got identical values"


class TestSendTemperature:
    """Unit tests for Redis queue interaction."""

    def setup_method(self):
        self.redis = fakeredis.FakeRedis()
        self.generator = TemperatureGenerator(self.redis, interval=999)

    def test_send_puts_value_on_queue(self):
        """send_temperature() should push the given value to Redis."""
        self.generator.send_temperature(20.0)
        assert self.redis.llen(TEMPERATURE_QUEUE_KEY) == 1
        assert float(self.redis.lpop(TEMPERATURE_QUEUE_KEY).decode()) == 20.0  # type: ignore

    def test_send_multiple_readings(self):
        """Multiple calls should place multiple items on the queue."""
        readings = [1.5, -3.0, 37.2]
        for r in readings:
            self.generator.send_temperature(r)
        assert self.redis.llen(TEMPERATURE_QUEUE_KEY) == len(readings)

    def test_queue_receives_correct_value(self):
        """The dequeued value must match exactly what was sent."""
        self.generator.send_temperature(-9.99)
        value = float(self.redis.lpop(TEMPERATURE_QUEUE_KEY).decode())  # type: ignore
        assert value == -9.99


class TestGeneratorThread:
    """Integration-level tests for the background thread."""

    def test_queue_non_empty_after_start(self):
        """After starting, at least one reading should appear quickly."""
        r = fakeredis.FakeRedis()
        gen = TemperatureGenerator(r, interval=0.1)
        gen.start()
        time.sleep(0.4)   # allow a couple of cycles
        gen.stop()
        assert r.llen(TEMPERATURE_QUEUE_KEY) > 0, (  # type: ignore
            "Redis queue should contain at least one reading after start()"
        )

    def test_thread_is_alive_after_start(self):
        """Generator thread should be running after start()."""
        r = fakeredis.FakeRedis()
        gen = TemperatureGenerator(r, interval=999)
        gen.start()
        assert gen.is_alive()
        gen.stop()
