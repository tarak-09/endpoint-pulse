import argparse
import asyncio
import json
import sys
import sqlite3

from .config import load_config
from .worker import WorkerPool
from .db import init_db, save_metrics, get_history, print_history

def main():
    parser = argparse.ArgumentParser(description="Concurrent endpoint health monitor")
    parser.add_argument("-c", "--config", type=str, help="Path to the YAML configuration file")
    parser.add_argument("--db", type=str, help="SQLite database file where run metrics are recorded")
    
    subparsers = parser.add_subparsers(dest="command")
    hp = subparsers.add_parser("history", help="Show history of metrics")
    hp.add_argument("--db", type=str, default=argparse.SUPPRESS, help="SQLite database file where run metrics are recorded")
    
    args = parser.parse_args()

    if getattr(args, "command", None) == "history":
        if not args.db:
            print("Error: --db flag is required for history subcommand", file=sys.stderr)
            sys.exit(1)
        try:
            rows = get_history(args.db)
            print_history(rows)
        except sqlite3.Error as e:
            print(f"Database error: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    if not args.config:
        print("Error: -c/--config is required to run the monitor", file=sys.stderr)
        sys.exit(1)

    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    pool = WorkerPool(config)
    try:
        results = asyncio.run(pool.run())
        print(json.dumps(results, indent=2))
        
        if args.db:
            try:
                conn = init_db(args.db)
                save_metrics(conn, results)
                conn.close()
            except sqlite3.Error as e:
                print(f"Error saving to database: {e}", file=sys.stderr)
                
    except KeyboardInterrupt:
        print("\nMonitoring interrupted.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
