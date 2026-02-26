#!/usr/bin/env python3
"""
Revenue Forecast Sync Application
Fetches revenue forecast data from MySQL bi_data database and sends to Revenue Forecast API.

Requirements:
    pip install mysql-connector-python requests

Setup:
    1. Create a .env file with your MySQL and API configuration (see .env.example)
    2. Run: python sync_app.py
    3. Schedule with Kubernetes CronJob for automated syncing

Usage:
    python sync_app.py              # Incremental sync (since last run)
    python sync_app.py --full       # Full refresh (all records)
    python sync_app.py --dry-run    # Print rows without sending
"""

import os
import sys
import json
import time
import logging
import argparse
import decimal
from datetime import datetime, date
from dotenv import load_dotenv

# ─── CONFIG ──────────────────────────────────────────────────────────────────

MYSQL_CONFIG = {
    "host":     "your-internal-mysql-host",   # e.g. 192.168.1.50 or localhost
    "user":     "your_db_user",
    "password": "your_db_password",
    "database": "bi_data",                    # The database containing bi_data.jobs
    "port":     3306,
    "connect_timeout": 10,
}

# Your deployed OptiQo URL
APP_URL = "https://optiqo.straker.co"

# API key — reads from environment variable BOOKINGS_SYNC_API_KEY, or set directly here
API_KEY = os.environ.get("BOOKINGS_SYNC_API_KEY", "8f2b3e91-7a4c-4d5e-bc81-2a9f3b6d5e1a")

BATCH_SIZE = 200       # Rows per POST request
RETRY_ATTEMPTS = 3     # Number of retries per batch
FETCH_BATCH_SIZE = 1000  # MySQL fetch batch size (memory optimization)

# Use environment variable for last sync file path (supports Kubernetes persistent volumes)
LAST_SYNC_FILE = os.environ.get("LAST_SYNC_FILE", os.path.join(os.path.dirname(__file__), "last_sync.txt"))

# ─────────────────────────────────────────────────────────────────────────────


def load_config():
    """Load configuration from .env file if it exists"""
    env_file = ".env"
    if os.path.exists(env_file):
        load_dotenv(env_file)
        log.info("Environment variables loaded from %s", env_file)
    else:
        # Try to load from Docker/Kubernetes mounted location
        env_file = "/app/.env"
        if os.path.exists(env_file):
            load_dotenv(env_file)
            log.info("Environment variables loaded from %s", env_file)
    
    # Update MySQL config from environment variables
    MYSQL_CONFIG.update({
        'host': os.getenv('MYSQL_HOST', MYSQL_CONFIG['host']),
        'user': os.getenv('MYSQL_USER', MYSQL_CONFIG['user']),
        'password': os.getenv('MYSQL_PASSWORD', MYSQL_CONFIG['password']),
        'database': os.getenv('MYSQL_DATABASE', MYSQL_CONFIG['database']),
        'port': int(os.getenv('MYSQL_PORT', MYSQL_CONFIG['port']))
    })
    
    # Update API config from environment variables
    global APP_URL, API_KEY
    APP_URL = os.getenv('APP_URL', APP_URL)
    API_KEY = os.getenv('BOOKINGS_SYNC_API_KEY', API_KEY)
    
    log.info("Configuration loaded from environment variables")


# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("revenue-forecast-sync")


QUERY = """
SELECT
    c.client_name                                    AS `Customer`,
    g.group_name                                     AS `Group`,
    sg.straker_group_name                            AS `Entity`,
    CONCAT('TJ', j.job_id)                           AS `TJ`,
    j.job_created                                    AS `Date`,
    j.quote                                          AS `TJAmount (in Sales Order currency)`,
    j.quote_nett                                     AS `TJAmount nett (in Sales Order currency)`,
    j.quote_currency                                 AS `Currency`,
    j.due_date                                       AS `Expected Due Date`,
    j.job_status                                     AS `Status`,
    j.completed_date                                 AS `Completed Date`,
    j.wip_completed_pct                              AS `WIP`,
    j.gross_margin                                   AS `Gross Margin`
FROM bi_data.jobs j
LEFT OUTER JOIN bi_data.clients c
    ON c.client_uuid = j.client_uuid
LEFT OUTER JOIN `groups` g
    ON g.group_uuid = j.group_uuid
LEFT OUTER JOIN straker_groups sg
    ON sg.straker_group_uuid = g.entity_uuid
{where_clause}
ORDER BY j.job_created DESC
"""


def serialize(obj):
    """Make MySQL date/datetime objects and decimals JSON-serialisable."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serialisable")


def read_last_sync():
    """Read the last sync timestamp from persistent storage"""
    try:
        # Ensure the directory exists (for Kubernetes persistent volume)
        os.makedirs(os.path.dirname(LAST_SYNC_FILE), exist_ok=True)
        with open(LAST_SYNC_FILE) as f:
            ts = f.read().strip()
            return ts if ts else None
    except FileNotFoundError:
        return None


def write_last_sync(ts: str):
    """Write the last sync timestamp to persistent storage"""
    # Ensure the directory exists (for Kubernetes persistent volume)
    os.makedirs(os.path.dirname(LAST_SYNC_FILE), exist_ok=True)
    with open(LAST_SYNC_FILE, "w") as f:
        f.write(ts)


def send_batch(rows: list, dry_run: bool) -> dict:
    """Send a batch of rows to the OptiQo webhook. Returns response dict."""
    if dry_run:
        log.info("[DRY RUN] Would send %d rows", len(rows))
        return {"inserted": 0, "updated": 0, "total": len(rows)}

    import requests

    # Use the correct webhook endpoint
    url = f"{APP_URL.rstrip('/')}/webhook"
    # Send rows directly as JSON array (API expects JSON, not wrapped in {"data": ...})
    payload = rows

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            resp = requests.post(
                url,
                json=payload,
                headers={
                    "X-Api-Key": API_KEY,
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            if resp.status_code == 401:
                log.error("Authentication failed — check BOOKINGS_SYNC_API_KEY matches the server environment variable")
                sys.exit(1)
            if resp.status_code == 503:
                log.error("Server says BOOKINGS_SYNC_API_KEY is not configured on the server")
                sys.exit(1)
            resp.raise_for_status()
            
            log.info(f"API Response Status: {resp.status_code}")
            log.info(f"API Response Headers: {dict(resp.headers)}")
            log.info(f"API Response (first 200 chars): {resp.text[:200]}")
            
            # Check if response is JSON
            if resp.headers.get('content-type', '').startswith('application/json'):
                return resp.json()
            else:
                # Non-JSON response - log warning but continue processing
                log.warning("Expected JSON response but received: %s", resp.headers.get('content-type', 'unknown'))
                log.warning("Response body (first 200 chars): %s", resp.text[:200])
                # Return default response structure to continue processing
                return {"inserted": 0, "updated": 0, "total": len(rows), "message": "Non-JSON response received"}
        except requests.exceptions.ConnectionError:
            log.warning("Attempt %d/%d: Connection error. Is the OptiQo server running?", attempt, RETRY_ATTEMPTS)
        except requests.exceptions.Timeout:
            log.warning("Attempt %d/%d: Request timed out", attempt, RETRY_ATTEMPTS)
        except requests.exceptions.HTTPError as e:
            log.warning("Attempt %d/%d: HTTP %s — %s", attempt, RETRY_ATTEMPTS, e.response.status_code, e.response.text[:200])

        if attempt < RETRY_ATTEMPTS:
            wait = 2 ** attempt
            log.info("Retrying in %ds…", wait)
            time.sleep(wait)

    raise RuntimeError(f"Failed to send batch after {RETRY_ATTEMPTS} attempts")


def run(full_refresh: bool = False, dry_run: bool = False):
    log.info("=== Revenue Forecast Sync ===")
    if dry_run:
        log.info("DRY RUN mode — no data will be sent")

    # Load configuration from file if it exists
    load_config()

    last_sync = None if full_refresh else read_last_sync()
    sync_start = datetime.utcnow().isoformat()

    if last_sync:
        where_clause = f"WHERE j.job_created >= '2025-04-01' AND (j.job_created >= '{last_sync}' OR j.completed_date >= '{last_sync}')"
        log.info("Incremental sync: fetching records from 2025-04-01 onwards, modified since %s", last_sync)
    else:
        where_clause = "WHERE j.job_created >= '2025-04-01'"
        log.info("Full refresh: fetching all records from 2025-04-01 onwards")

    try:
        import mysql.connector
    except ImportError:
        log.error("mysql-connector-python is not installed. Run: pip install mysql-connector-python requests")
        sys.exit(1)

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True, buffered=False)  # Use unbuffered cursor
        log.info("Connected to MySQL at %s/%s", MYSQL_CONFIG["host"], MYSQL_CONFIG["database"])
    except Exception as e:
        log.error("Failed to connect to MySQL: %s", e)
        sys.exit(1)

    try:
        # Use streaming query for memory efficiency
        sql = QUERY.format(where_clause=where_clause)
        cursor.execute(sql)
        
        # Process data in streaming batches to avoid OOM
        total_processed = 0
        total_inserted = 0
        total_updated = 0
        batch_buffer = []
        
        log.info("STREAMING MODE: Processing data in batches of %d records", FETCH_BATCH_SIZE)
        
        while True:
            # Fetch records in chunks
            chunk = cursor.fetchmany(FETCH_BATCH_SIZE)
            if not chunk:
                break
                
            total_processed += len(chunk)
            log.info("Processing chunk: %d-%d records (total: %d)", 
                    total_processed - len(chunk) + 1, total_processed, total_processed)
            
            # Convert chunk to serializable format
            serializable_chunk = json.loads(json.dumps(chunk, default=serialize))
            
            # Add to batch buffer
            batch_buffer.extend(serializable_chunk)
            
            # Send batches when buffer reaches BATCH_SIZE
            while len(batch_buffer) >= BATCH_SIZE:
                batch = batch_buffer[:BATCH_SIZE]
                batch_buffer = batch_buffer[BATCH_SIZE:]
                
                batch_num = (total_processed // BATCH_SIZE) + 1
                log.info("Batch %d (%d rows)…", batch_num, len(batch))
                
                if not dry_run:
                    result = send_batch(batch, dry_run)
                    total_inserted += result.get("inserted", 0)
                    total_updated += result.get("updated", 0)
                    log.info("  → inserted: %d, updated: %d", result.get("inserted", 0), result.get("updated", 0))
        
        # Send remaining records in buffer
        if batch_buffer:
            batch_num = (total_processed // BATCH_SIZE) + 1
            log.info("Final batch %d (%d rows)…", batch_num, len(batch_buffer))
            
            if not dry_run:
                result = send_batch(batch_buffer, dry_run)
                total_inserted += result.get("inserted", 0)
                total_updated += result.get("updated", 0)
                log.info("  → inserted: %d, updated: %d", result.get("inserted", 0), result.get("updated", 0))
        
        log.info("Processed %d total records from MySQL", total_processed)
        
    except Exception as e:
        log.error("Query failed: %s", e)
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

    if total_processed == 0:
        log.info("No rows to sync. Done.")
        if not full_refresh:
            write_last_sync(sync_start)
        return

    log.info("Sync complete. Total: %d inserted, %d updated", total_inserted, total_updated)

    if not dry_run:
        write_last_sync(sync_start)
        log.info("Last sync timestamp saved: %s", sync_start)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Revenue Forecast Sync")
    parser.add_argument("--full", action="store_true", help="Full refresh — ignore last sync timestamp")
    parser.add_argument("--dry-run", action="store_true", help="Fetch rows but do not send them")
    args = parser.parse_args()
    run(full_refresh=args.full, dry_run=args.dry_run)
