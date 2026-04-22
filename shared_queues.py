"""
shared_queues.py
----------------
Defines the two shared message queues used by all three clients.

- temperature_queue : point-to-point channel between the Generator (Client 1)
                      and the Processor (Client 2).
- alert_queue       : point-to-point channel between the Processor (Client 2)
                      and the Reporter (Client 3).
"""

import queue

# Queue for raw temperature readings (Client 1 → Client 2)
temperature_queue: queue.Queue = queue.Queue()

# Queue for alert notifications (Client 2 → Client 3)
alert_queue: queue.Queue = queue.Queue()
