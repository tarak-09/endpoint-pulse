import argparse
import asyncio
import json
import sys

from .config import load_config
from .worker import WorkerPool

def main():
    parser = argparse.ArgumentParser(description="Concurrent endpoint health monitor")
    parser.add_argument(
        "-c", "--config", 
        type=str, 
        required=True, 
        help="Path to the YAML configuration file"
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    pool = WorkerPool(config)
    try:
        results = asyncio.run(pool.run())
        print(json.dumps(results, indent=2))
    except KeyboardInterrupt:
        print("\nMonitoring interrupted.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
