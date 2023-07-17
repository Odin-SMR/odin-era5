import datetime
import tempfile
from typing import Any, Mapping, TypedDict

import s3fs  # type: ignore
import xarray
from cdsapi.api import Client, Result  # type: ignore

BUCKET = "odin-era5"

class DownloadEvent(TypedDict):
    zarr_store: str
    reply: Mapping[str, Any]


def lambda_handler(event: DownloadEvent, context):

    zarr_store = event["zarr_store"]
    client = Client(progress=False, wait_until_complete=False)
    result = Result(client, event["reply"])
    s3 = s3fs.S3FileSystem()
    store = s3fs.S3Map(root=zarr_store, s3=s3, check=False)
    with tempfile.NamedTemporaryFile() as f:
        result.download(target=f.name)
        ds = xarray.open_dataset(f.name)
        ds.to_zarr(store=store)
        f.close()
    return {"StatusCode": 200}
