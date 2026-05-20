"""
Query API Lambda — returns KPI data from DynamoDB for the dashboard.
Triggered by: API Gateway GET /kpis?event_type=page_view&hours=24
"""
import json
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["DYNAMODB_TABLE"]
table = dynamodb.Table(TABLE_NAME)

DEFAULT_HOURS = 24
MAX_HOURS = 168  # 7 days


def lambda_handler(event: dict, context: Any) -> dict:
    params = event.get("queryStringParameters") or {}
    event_type = params.get("event_type", "page_view")
    try:
        hours = min(int(params.get("hours", DEFAULT_HOURS)), MAX_HOURS)
    except ValueError:
        return response(400, {"error": "hours must be an integer"})

    now = datetime.now(tz=timezone.utc)
    hour_keys = [
        (now - timedelta(hours=i)).strftime("%Y-%m-%dT%H")
        for i in range(hours - 1, -1, -1)
    ]

    pk = f"EVENT_TYPE#{event_type}"
    start_sk = f"HOUR#{hour_keys[0]}"
    end_sk = f"HOUR#{hour_keys[-1]}"

    result = table.query(
        KeyConditionExpression=Key("pk").eq(pk) & Key("sk").between(start_sk, end_sk),
        ScanIndexForward=True,
    )

    items = result.get("Items", [])
    # Fill gaps with zeros
    item_map = {item["sk"].replace("HOUR#", ""): item for item in items}

    series = []
    totals = {"count": 0, "sum_duration": 0, "unique_users": 0}
    for hk in hour_keys:
        item = item_map.get(hk, {})
        cnt = int(item.get("count", 0))
        dur = int(item.get("sum_duration", 0))
        users = len(item.get("unique_users", set()))
        series.append({
            "hour": hk,
            "count": cnt,
            "avg_duration_ms": round(dur / cnt, 1) if cnt else 0,
            "unique_users": users,
        })
        totals["count"] += cnt
        totals["sum_duration"] += dur
        totals["unique_users"] += users

    payload = {
        "event_type": event_type,
        "window_hours": hours,
        "totals": totals,
        "series": series,
    }

    logger.info("KPI query: event_type=%s hours=%d items=%d", event_type, hours, len(items))
    return response(200, payload)


def response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }
