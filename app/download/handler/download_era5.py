import datetime
import cdsapi
import tempfile
import boto3

BUCKET = "odin-era5"


def lambda_handler(event, context):
    s3_client = boto3.client("s3")
    client = cdsapi.Client(progress=False, wait_until_complete=False)
    result = cdsapi.Result(client, event["reply"])
    with tempfile.NamedTemporaryFile() as f:
        downloaded_target = result.download(target=f.name)
        date = event["date"]
        hour = event["hour"]
        dt = datetime.date.fromisoformat(date)

        target_dir = f"{dt.year}/{dt.month:02}/"
        target_file = f"ea_pl_{date}-{hour}.nc"
        s3_client.upload_fileobj(f, BUCKET, target_dir + target_file)

    return downloaded_target
