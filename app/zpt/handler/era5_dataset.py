from datetime import datetime
from tempfile import NamedTemporaryFile

import boto3
import s3fs  # type: ignore
import xarray
from pandas import DatetimeIndex

s3 = s3fs.S3FileSystem()

s3_client = boto3.client("s3")


def get_dataset(range: DatetimeIndex):
    stores = [
        s3fs.S3Map(
            root=(
                f"s3://odin-era5/{i.year}/{i.month:02}/"
                f"ea_pl_{i.year:02}-{i.month:02}-{i.day:02}-{i.hour:02}.zarr"
            ),
            check=False,
            s3=s3,
        )
        for i in range
    ]
    datasets = [xarray.open_zarr(store) for store in stores]
    combined = xarray.concat(datasets, dim="time")
    combined.sortby("time")
    return combined


def convert_dataset(date: datetime):
    zarr_url = (
        f"s3://odin-era5/{date.year}/{date.month:02}/"
        f"ea_pl_{date.year}-{date.month:02}-{date.day:02}-{date.hour:02}.zarr"
    )
    nc_path = (
        f"{date.year}/{date.month:02}/"
        f"ea_pl_{date.year}-{date.month:02}-{date.day:02}-{date.hour:02}.nc"
    )
    with NamedTemporaryFile() as f:
        s3_client.download_fileobj("odin-era5", nc_path, f)
        ds = xarray.open_dataset(f.name)
        store = s3fs.S3Map(root=zarr_url, s3=s3, check=False)
        ds.to_zarr(store=store)
