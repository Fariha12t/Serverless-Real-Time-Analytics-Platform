"""
Processor Lambda — consumes Kinesis records, aggregates KPIs, writes to DynamoDB.
Triggered by: Kinesis Data Stream (batch size 100, bisect on error)
"""
import base64
import json
import os
import time
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["DYNAMODB_TABLE"]
table = dynamodb.Table(TABLE_NAME)

# KPIs expire after 90 days (TTL)
TTL_SECONDS = 90 * 24 * 3600


def lambda_handler(event: dict, context: Any) -> None:
    records = event.get("Records", [])
    logger.info("Processing %d Kinesis records", len(records))

    # Aggregate before writing to reduce DynamoDB write units
    aggregates: dict[tuple, dict] = defaultdict(lambda: {
        "count": 0,
        "sum_duration": 0,
        "unique_users": set(),
    })

    parse_errors = 0
    for record in records:
        try:
            payload = decode_record(record)
            bucket = make_bucket_key(payload)
            aggregates[bucket]["count"] += 1
            aggregates[bucket]["sum_duration"] += int(
                payload.get("properties", {}).get("duration_ms", 0)
            )
            aggregates[bucket]["unique_users"].add(payload.get("user_id", ""))
        except Exception as exc:  # noqa: BLE001
            parse_errors += 1
            logger.warning("Failed to parse record: %s", exc)

    # Write aggregated KPIs
    write_errors = 0
    for (event_type, hour_key), agg in aggregates.items():
        try:
            upsert_kpi(event_type, hour_key, agg)
        except Exception as exc:  # noqa: BLE001
            write_errors += 1
            logger.error("DynamoDB write failed for %s/%s: %s", event_type, hour_key, exc)

    logger.info(
        "Aggregated %d buckets | parse_errors=%d write_errors=%d",
        len(aggregates), parse_errors, write_errors,
    )

    if write_errors:
        raise RuntimeError(f"{write_errors} DynamoDB write(s) failed — triggering retry")


def decode_record(record: dict) -> dict:
    raw = base64.b64decode(record["kinesis"]["data"]).decode()
    return json.loads(raw)


def make_bucket_key(payload: dict) -> tuple[str, str]:
    event_type = payload.get("event_type", "unknown")
    # Bucket by hour
    ts_ms = payload.get("ingested_at", time.time() * 1000)
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    hour_key = dt.strftime("%Y-%m-%dT%H")
    return event_type, hour_key


def upsert_kpi(event_type: str, hour_key: str, agg: dict) -> None:
    pk = f"EVENT_TYPE#{event_type}"
    sk = f"HOUR#{hour_key}"
    expires_at = int(time.time()) + TTL_SECONDS

    # Atomic increment — safe for concurrent Lambda executions
    table.update_item(
        Key={"pk": pk, "sk": sk},
        UpdateExpression=(
            "ADD #count :cnt, sum_duration :dur, unique_users :users "
            "SET updated_at = :ts, expires_at = :ttl, event_type = :et"
        ),
        ExpressionAttributeNames={"#count": "count"},
        ExpressionAttributeValues={
            ":cnt": agg["count"],
            ":dur": agg["sum_duration"],
            ":users": agg["unique_users"],  # DynamoDB Number/String Set
            ":ts": datetime.now(tz=timezone.utc).isoformat(),
            ":ttl": expires_at,
            ":et": event_type,
        },
    )
