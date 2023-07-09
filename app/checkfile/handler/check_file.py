import datetime
import json

import boto3
from botocore.exceptions import ClientError

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
    file_name = f"{date.year}/{date.month:02}/ea_pl_{date.isoformat()}-{hour}.zarr"
    # Reverse: if fail do nu'in else download
    try:
        request = s3.head_object(Bucket=BUCKET, Key=file_name)
        return {
            "LastModified": request["LastModified"].isoformat(),
            "ContentLength": request["ContentLength"],
            "ContentType": request["ContentType"],
            "StatusCode": request["ResponseMetadata"]["HTTPStatusCode"],
            "FileName": file_name,
        }
    except ClientError as err:
        error = err.response.get("Error")
        if error:
            code = error.get("Code")
            msg = error.get("Message")
            if code == "404":
                return {
                    "StatusCode": int(code),
                    "Message": msg,
                    "FileName": file_name,
                }
        raise err
