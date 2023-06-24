import datetime

import boto3
import json

BUCKET = "odin-era5"

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

def lambda_handler(event, context):
    s3 = boto3.client("s3")
    date = datetime.date.fromisoformat(event["date"])
    hour = event["hour"]
    file_name = f"{date.year}/{date.month:02}/ea_pl_{date.isoformat()}-{hour}.nc"
    request = s3.head_object(Bucket=BUCKET, Key=file_name)
    return json.loads(json.dumps(request, cls=DateTimeEncoder))

