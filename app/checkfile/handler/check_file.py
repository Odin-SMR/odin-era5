from typing import Hashable, List, Mapping, TypedDict

import xarray as xr
import s3fs  # type: ignore

BUCKET = "odin-era5"


class CheckFileEvent(TypedDict):
    zarr_store: str


class CheckFileResult(TypedDict):
    zarr_store: str
    dimensions: Mapping[Hashable, int] | None
    times: List[int] | None
    status_code: int


def lambda_handler(event: CheckFileEvent, context):
    zarr_store = event["zarr_store"]
    s3 = s3fs.S3FileSystem(anon=True)
    store = s3fs.S3Map(root=zarr_store, s3=s3)

    try:
        ds = xr.open_zarr(store, consolidated=True)
    except ValueError as e:
        return CheckFileResult(
            zarr_store=zarr_store, status_code=404, dimensions=None, times=None
        )
    return CheckFileResult(
        zarr_store=zarr_store,
        dimensions=ds.dims.mapping,
        times=ds.time.values.tolist(),
        status_code=200,
    )
