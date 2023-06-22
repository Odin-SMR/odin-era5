import datetime

import boto3

BUCKET = "odin-era5"


def lambda_handler(event, context):
    s3 = boto3.client("s3")
    date = datetime.date.fromisoformat(event["date"])
    hour = event["hour"]
    file_name = f"{date.year}/{date.month:02}/ea_pl_{date.isoformat()}-{hour}.nc"

    try:
        s3.head_object(Bucket=BUCKET, Key=file_name)
        exists = True
    except:
        exists = False

    data = {"exists": exists, "date": event["date"], "hour": event["hour"]}

    return {
        "statusCode": 200,
        "body": data,
        "headers": {
            "Content-Type": "application/json",
        },
    }
