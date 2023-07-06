import datetime
import tempfile

import s3fs  # type: ignore
import xarray
from cdsapi.api import Client, Result  # type: ignore

BUCKET = "odin-era5"


def lambda_handler(event, context):
    date = event["date"]
    hour = event["hour"]
    dt = datetime.date.fromisoformat(date)
    zarr_url = (
        f"s3://${BUCKET}/{dt.year}/{dt.month:02}/"
        f"ea_pl_{dt.year}-{dt.month:02}-{dt.day:02}-{hour}.zarr"
    )
    client = Client(progress=False, wait_until_complete=False)
    result = Result(client, event["reply"])
    s3 = s3fs.S3FileSystem()
    store = s3fs.S3Map(root=zarr_url, s3=s3, check=False)
    with tempfile.NamedTemporaryFile() as f:
        result.download(target=f.name)
        ds = xarray.open_dataset(f.name)
        ds.to_zarr(store=store)
    return {"StatusCode": 200}
