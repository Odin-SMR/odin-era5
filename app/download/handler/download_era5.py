import datetime
import tempfile

import boto3
from cdsapi.api import Client, Result

BUCKET = "odin-era5"


def lambda_handler(event, context):
    s3_client = boto3.client("s3")
    client = Client(progress=False, wait_until_complete=False)
    result = Result(client, event["reply"])
    with tempfile.NamedTemporaryFile() as f:
        result.download(target=f.name)
        date = event["date"]
        hour = event["hour"]
        dt = datetime.date.fromisoformat(date)

        target_dir = f"{dt.year}/{dt.month:02}/"
        target_file = f"ea_pl_{date}-{hour}.nc"
        s3_client.upload_fileobj(f, BUCKET, target_dir + target_file)

    return {"StatusCode": 200}
