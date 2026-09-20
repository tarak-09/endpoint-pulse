import sqlite3
import sys
from typing import List, Dict, Any

def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS run_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            url TEXT,
            total_requests INTEGER,
            successes INTEGER,
            failures INTEGER,
            p50_ms REAL,
            p95_ms REAL,
            p99_ms REAL
        )
    ''')
    conn.commit()
    return conn

def save_metrics(conn: sqlite3.Connection, results: List[Dict[str, Any]]):
    c = conn.cursor()
    for res in results:
        c.execute('''
            INSERT INTO run_metrics (url, total_requests, successes, failures, p50_ms, p95_ms, p99_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            res["url"],
            res["total_requests"],
            res["successes"],
            res["failures"],
            res["latencies"]["p50_ms"],
            res["latencies"]["p95_ms"],
            res["latencies"]["p99_ms"]
        ))
    conn.commit()

def get_history(db_path: str):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT timestamp, url, total_requests, failures, p50_ms, p95_ms, p99_ms
        FROM run_metrics
        ORDER BY url, timestamp
    ''')
    rows = c.fetchall()
    conn.close()
    return rows

def print_history(rows):
    if not rows:
        print("No history found in database.")
        return

    print(f"{'Timestamp':<22} | {'URL':<30} | {'Reqs':<5} | {'Fail %':<7} | {'p50(ms)':<8} | {'p95(ms)':<8} | {'p99(ms)':<8}")
    print("-" * 105)
    for row in rows:
        timestamp, url, total_requests, failures, p50, p95, p99 = row
        fail_rate = (failures / total_requests * 100) if total_requests else 0
        fail_str = f"{fail_rate:.1f}%"
        print(f"{timestamp:<22} | {url:<30} | {total_requests:<5} | {fail_str:<7} | {p50:<8.2f} | {p95:<8.2f} | {p99:<8.2f}")
