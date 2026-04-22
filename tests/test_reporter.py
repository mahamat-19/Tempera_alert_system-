"""
tests/test_reporter.py
-----------------------
Tests for Client 3 – AlertReporter.

Covers:
  - report_alert() prints the correct message to stdout.
  - The reporter thread reads from the queue and calls report_alert().
  - Multiple sequential alerts are all reported.
"""

import queue
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from client3_reporter import AlertReporter


class TestReportAlert:
    """Unit tests for the console-output method."""

    def setup_method(self):
        self.q = queue.Queue()
        self.reporter = AlertReporter(self.q)

    def test_report_alert_prints_message(self, capsys):
        """report_alert() should print the supplied message to stdout."""
        msg = "ALERT: 5 abnormal temperature readings have been detected."
        self.reporter.report_alert(msg)
        captured = capsys.readouterr()
        assert msg in captured.out

    def test_report_alert_prints_separator(self, capsys):
        """report_alert() should include a visible separator line."""
        self.reporter.report_alert("test alert")
        captured = capsys.readouterr()
        assert "=" * 10 in captured.out   # at least 10 '=' chars present

    def test_report_different_messages(self, capsys):
        """Each call prints the specific message passed to it."""
        self.reporter.report_alert("First alert")
        self.reporter.report_alert("Second alert")
        captured = capsys.readouterr()
        assert "First alert" in captured.out
        assert "Second alert" in captured.out


class TestReporterThread:
    """Integration-level tests — reporter thread reads from the queue."""

    def _make_reporter(self):
        q = queue.Queue()
        reporter = AlertReporter(q)
        return reporter, q

    def test_reporter_reads_single_alert(self, capsys):
        """A message placed on the queue should be printed by the thread."""
        reporter, q = self._make_reporter()
        reporter.start()
        msg = "ALERT: 5 abnormal temperature readings have been detected."
        q.put(msg)
        time.sleep(0.3)   # give thread time to process
        reporter.stop()
        captured = capsys.readouterr()
        assert msg in captured.out

    def test_reporter_reads_multiple_alerts(self, capsys):
        """All messages placed on the queue should eventually be printed."""
        reporter, q = self._make_reporter()
        reporter.start()
        messages = [
            "ALERT: 5 abnormal temperature readings have been detected.",
            "ALERT: 5 abnormal temperature readings have been detected. (Total abnormal so far: 10)",
            "ALERT: 5 abnormal temperature readings have been detected. (Total abnormal so far: 15)",
        ]
        for m in messages:
            q.put(m)
        time.sleep(0.5)
        reporter.stop()
        captured = capsys.readouterr()
        for m in messages:
            assert m in captured.out

    def test_thread_is_alive_after_start(self):
        """Reporter thread should be running after start()."""
        reporter, _ = self._make_reporter()
        reporter.start()
        assert reporter.is_alive()
        reporter.stop()

    def test_reporter_handles_empty_queue_gracefully(self):
        """Reporter should not crash when the queue stays empty."""
        reporter, _ = self._make_reporter()
        reporter.start()
        time.sleep(0.3)   # no messages — should remain silent
        assert reporter.is_alive()
        reporter.stop()
