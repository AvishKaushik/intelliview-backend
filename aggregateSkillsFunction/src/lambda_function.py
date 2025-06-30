import boto3
import json
import os
from decimal import Decimal
from collections import Counter, defaultdict

dynamo = boto3.client("dynamodb")

TABLE       = os.environ["TABLE_NAME"]           # e.g. InterviewSession
INDEX_NAME  = "userId-ts-index"                  # your GSI (PK userId, SK ts)

def lambda_handler(event, context):
    # ─── 1.  Get userId from query param (hard‑coded for quick test) ────────────
    user_id = event["queryStringParameters"].get("userId")   # fallback for dev
    if not user_id:
        return _resp(400, {"error": "userId required"})

    # ─── 2.  Query all sessions for this user (paginate via LastEvaluatedKey) ──
    items, last = [], None
    while True:
        query_args = {
            "TableName": TABLE,
            "IndexName": INDEX_NAME,
            "KeyConditionExpression": "userId = :u",
            "ExpressionAttributeValues": {":u": {"S": user_id}},
            "ProjectionExpression": "feedback"
        }
        if last:
            query_args["ExclusiveStartKey"] = last

        resp = dynamo.query(**query_args)
        items.extend(resp.get("Items", []))
        last = resp.get("LastEvaluatedKey")
        if not last:
            break

    # ─── 3.  Aggregate ratings / strengths / weaknesses ───────────────────────
    rating_sum  = defaultdict(Decimal)
    rating_cnt  = defaultdict(int)
    strengths   = Counter()
    weaknesses  = Counter()

    for it in items:
        fb = it.get("feedback", {}).get("M")
        if not fb:
            continue

        # ratings
        for k, v in fb.get("ratings", {}).get("M", {}).items():
            rating_sum[k] += Decimal(v["N"])  # ← fix here
            rating_cnt[k] += 1

        # strengths / weaknesses
        for s in fb.get("strengths", {}).get("L", []):
            strengths[s["S"]]  += 1
        for w in fb.get("weaknesses", {}).get("L", []):
            weaknesses[w["S"]] += 1

    avg_ratings = {
        k: round(float(rating_sum[k] / rating_cnt[k]), 2)
        for k in rating_sum
    }

    body = {
        "sessionsAnalyzed": len(items),
        "avgRatings": avg_ratings,
        "topStrengths": strengths.most_common(5),
        "topWeaknesses": weaknesses.most_common(5),
    }
    return _resp(200, body)

# ───────────────────────────────────────────────────────────────────────────────
def _resp(code: int, body: dict):
    """
    API Gateway proxy integration response helper with CORS.
    """
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "OPTIONS,GET"
        },
        "body": json.dumps(body)
    }
