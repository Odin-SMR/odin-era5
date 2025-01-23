import tempfile
from typing import Any, Mapping, TypedDict

import cdsapi  # type: ignore
import xarray

BUCKET = "odin-era5"


class DownloadEvent(TypedDict):
    zarr_store: str
    reply: Mapping[str, Any]


def lambda_handler(event: DownloadEvent, context):
    zarr_store = event["zarr_store"]
    client = cdsapi.Client(progress=False, wait_until_complete=False)
    result = client.client.get_remote(event["reply"]["request_id"])  # type: ignore
    with tempfile.NamedTemporaryFile() as f:
        result.download(target=f.name)
        ds = xarray.open_dataset(f.name)
        ds_rename = ds.rename({"pressure_level": "level", "valid_time": "time"})
        ds_rename.to_zarr(store=zarr_store, mode="w")
        f.close()
    result.delete()
    return {"StatusCode": 200}
