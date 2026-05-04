
import time
import sys

from redis_config import make_redis_client
from client1_generator import TemperatureGenerator
from client2_processor import TemperatureProcessor
from client3_reporter import AlertReporter


def main() -> None:
    print("=" * 60)
    print("   Temperature Alert System — starting up")
    print("   Press Ctrl+C to stop")
    print("=" * 60)
    print()

    redis_client = make_redis_client()

    # Instantiate the three clients — all share the same Redis connection
    generator = TemperatureGenerator(redis_client)
    processor = TemperatureProcessor(redis_client)
    reporter  = AlertReporter(redis_client)

    # Start all three (each runs in its own daemon thread)
    reporter.start()    # start reporter first so it's ready for alerts
    processor.start()   # start processor before generator sends data
    generator.start()   # start generator last — it drives the pipeline

    try:
        # Keep the main thread alive; daemon threads run in the background
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[Main] Shutdown signal received — stopping all clients…")
        generator.stop()
        processor.stop()
        reporter.stop()

        # Brief pause to let threads print their final messages
        time.sleep(0.5)

        print("[Main] All clients stopped. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
