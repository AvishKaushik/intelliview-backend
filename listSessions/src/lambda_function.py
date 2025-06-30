import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])  # InterviewSession

def decimal_to_float(obj):
    if isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

def lambda_handler(event, context):
    try:
        params = event.get("queryStringParameters") or {}
        user_id = params.get("userId")
        if not user_id:
            return _response(400, { "error": "Missing userId query param" })

        # Use GSI to query by userId
        result = table.query(
            IndexName="userId-ts-index",
            KeyConditionExpression=boto3.dynamodb.conditions.Key("userId").eq(user_id),
            ProjectionExpression="sessionId, category, difficulty, ts"
        )
        items = result.get("Items", [])

        return _response(200, decimal_to_float(items))
    except Exception as e:
        print("Error:", str(e))
        return _response(500, {"error": str(e)})

def _response(code, body):
    return {
        "statusCode": code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        },
        "body": json.dumps(body)
    }
