"""
Ingest Lambda — validates incoming events and puts them onto Kinesis.
Triggered by: API Gateway POST /events
"""
import json
import os
import uuid
import time
import logging
import boto3
from typing import Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

kinesis = boto3.client("kinesis")
STREAM_NAME = os.environ["KINESIS_STREAM_NAME"]

REQUIRED_FIELDS = {"event_type", "user_id"}
MAX_BATCH = 500  # Kinesis PutRecords limit


def lambda_handler(event: dict, context: Any) -> dict:
    """API Gateway HTTP API proxy integration handler."""
    try:
        body = parse_body(event)
    except ValueError as exc:
        return response(400, {"error": str(exc)})

    # Accept single event or array
    events = body if isinstance(body, list) else [body]

    if len(events) > MAX_BATCH:
        return response(400, {"error": f"Batch size exceeds limit of {MAX_BATCH}"})

    enriched, errors = [], []
    for idx, evt in enumerate(events):
        try:
            enriched.append(enrich(evt))
        except ValueError as exc:
            errors.append({"index": idx, "error": str(exc)})

    if errors and not enriched:
        return response(400, {"errors": errors})

    # Put records onto Kinesis
    records = [
        {"Data": json.dumps(e).encode(), "PartitionKey": e["user_id"]}
        for e in enriched
    ]

    result = kinesis.put_records(StreamName=STREAM_NAME, Records=records)
    failed = result.get("FailedRecordCount", 0)

    logger.info(
        "Ingested %d events, %d failed, stream=%s",
        len(records), failed, STREAM_NAME
    )

    return response(200, {
        "accepted": len(enriched),
        "failed_kinesis": failed,
        "validation_errors": errors,
    })


def parse_body(event: dict) -> Any:
    raw = event.get("body", "{}")
    if event.get("isBase64Encoded"):
        import base64
        raw = base64.b64decode(raw).decode()
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON body: {exc}") from exc


def enrich(evt: dict) -> dict:
    missing = REQUIRED_FIELDS - set(evt.keys())
    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")
    return {
        **evt,
        "event_id": str(uuid.uuid4()),
        "ingested_at": int(time.time() * 1000),  # epoch ms
    }


def response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
