# generate_feedback_function.py
import json
import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeSerializer

# ───── Config ──────────────────────────────────────────────────────────
TABLE_NAME   = os.environ.get("TABLE_NAME", "InterviewSession")
MODEL_ID     = os.environ.get(
    "MODEL_ID",
    "anthropic.claude-3-sonnet-20240229-v1:0"
)
REGION       = os.environ.get("AWS_REGION", "us-east-1")

bedrock = boto3.client("bedrock-runtime", region_name=REGION)
dynamo  = boto3.client("dynamodb",         region_name=REGION)
ser     = TypeSerializer()

# ───── Lambda entrypoint ───────────────────────────────────────────────
def lambda_handler(event, context):
    try:
        raw_body = event.get("body") or "{}"
        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body

        session_id = body["sessionId"]
        timestamp  = int(body["ts"])
        messages   = body["messages"]  # [{role:"user"|... , content:"..."}]

        # 1️⃣  Build transcript string
        transcript = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in messages
        )[:8000]  # Claude token safety

        # 2️⃣  Build prompt
        prompt = f"""
You are an AI interview coach.

Analyze the following interview transcript and return JSON (no markdown) formatted exactly:
{{
  "summary": "...3 lines...",
  "ratings": {{
    "technical": 0-10,
    "communication": 0-10,
    "confidence": 0-10,
    "overall": 0-10
  }},
  "strengths": ["...", "...", "..."],
  "weaknesses": ["...", "...", "..."],
  "suggestions": ["...", "...", "..."]
}}

Transcript:
\"\"\"{transcript}\"\"\"
"""

        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "temperature": 0.4
        }

        # 3️⃣  Invoke Claude
        resp = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json"
        )
        text = json.loads(resp["body"].read())["content"][0]["text"].strip()
        feedback = json.loads(text)  # May raise JSONDecodeError

        # 4️⃣  Persist to DynamoDB
        dynamo.update_item(
            TableName=TABLE_NAME,
            Key={
                "sessionId": {"S": session_id},
                "ts": {"N": str(timestamp)}  # 🧠 REQUIRED sort key
            },
            UpdateExpression="SET feedback = :f, feedbackTimestamp = :fts",
            ExpressionAttributeValues={
                ":f": ser.serialize(feedback),
                ":fts": {"N": str(int(datetime.utcnow().timestamp()))}
            }
        )


        return _resp(200, {"success": True, "feedback": feedback})

    except (KeyError, json.JSONDecodeError) as err:
        return _resp(400, {"error": f"Invalid input: {str(err)}"})

    except ClientError as err:
        print("AWS error:", err)
        return _resp(500, {"error": str(err)})

    except Exception as e:
        print("ERROR:", e)
        print("TRACEBACK:", traceback.format_exc())  # This line adds real debug info
        return {
            "statusCode": 500,
            "body": json.dumps({ "error": str(e) })
        }

# ───── Helper ──────────────────────────────────────────────────────────
def _resp(code, body):
    return {
        "statusCode": code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }
