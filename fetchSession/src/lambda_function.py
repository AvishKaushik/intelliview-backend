import json
import boto3
import os
from decimal import Decimal
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])  # Should be InterviewSession

# Utility: Convert Decimal → float/int for JSON serialization
def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj) if '.' in str(obj) else int(obj)
    return obj

def lambda_handler(event, context):
    try:
        params = event.get("queryStringParameters") or {}
        session_id = params.get("sessionId")
        if not session_id:
            return _response(400, {"error": "sessionId query param required"})

        # Query all items by sessionId (using sort key ts if needed)
        resp = table.query(
            KeyConditionExpression=Key("sessionId").eq(session_id),
            ScanIndexForward=True  # oldest → newest
        )
        items = resp.get("Items", [])

        if not items:
            return _response(404, {"error": "Session not found"})

        # Clean decimals for frontend
        clean = convert_decimals(items)

        return _response(200, { "messages": clean })

    except Exception as e:
        print("ERROR:", e)
        return _response(500, {"error": str(e)})

def _response(code, body):
    return {
        "statusCode": code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "OPTIONS,GET"
        },
        "body": json.dumps(body)
    }
