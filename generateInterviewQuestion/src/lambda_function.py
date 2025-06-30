import json, time, os, boto3
from decimal import Decimal

# ---------- AWS Clients ----------
REGION    = os.environ.get("REGION", "us-east-1")
TABLE     = os.environ["TABLE_NAME"]            # InterviewSession
MODEL_ID  = os.environ.get("MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

dynamodb  = boto3.resource("dynamodb", region_name=REGION)
table     = dynamodb.Table(TABLE)
bedrock   = boto3.client("bedrock-runtime", region_name=REGION)

# ---------- Helpers ----------
def _headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Methods": "OPTIONS,POST"
    }

def _resp(code, body):
    return { "statusCode": code, "headers": _headers(), "body": json.dumps(body) }

# ---------- Lambda Handler ----------
def lambda_handler(event, context):
    try:
        # Parse body safely (string from API Gateway or dict in tests)
        raw_body = event.get("body") or "{}"
        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body

        session_id  = body["sessionId"]
        user_id     = body["userId"]  
        ts          = body["ts"]                          # ⭐ new
        category    = body.get("category",   "Unknown")      # ⭐ summary field
        difficulty  = body.get("difficulty", "Unknown")      # ⭐ summary field
        messages    = body["messages"]                       # list[ {role,content} ]

        # Format for Claude / Bedrock
        claude_msgs = [
            {
                "role": m["role"],
                "content": [ { "type": "text", "text": m["content"] } ]
            } for m in messages
        ]
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": claude_msgs
        }

        # Call Claude
        result = bedrock.invoke_model(
            modelId   = MODEL_ID,
            contentType = "application/json",
            accept    = "application/json",
            body      = json.dumps(payload)
        )
        reply_text = json.loads(result["body"].read())["content"][0]["text"]

        # Persist to DynamoDB
        # epoch_ts = int(time.time())
        table.put_item(
            Item = {
                "sessionId":  session_id,
                "ts":         ts,
                "userId":     user_id,      # ⭐ so we can query by user
                "category":   category,
                "difficulty": difficulty,
                "messages":   messages + [{ "role": "assistant", "content": reply_text }],
            }
        )

        return _resp(200, { "message": reply_text })

    except Exception as e:
        print("ERROR:", e)
        return _resp(500, { "error": str(e) })
