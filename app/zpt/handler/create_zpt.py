from datetime import datetime, timedelta
from typing import Any, Dict
from pandas import read_sql
from psycopg import connect
import s3fs 
import xarray

MJD_START_DATE = datetime(1858, 11, 17)
DAYS_PER_SECOND = 1.0 / 60 / 60 / 24


def datetime2mjd(dt: datetime) -> float:
    return (dt - MJD_START_DATE).total_seconds() * DAYS_PER_SECOND


def mjd2datetime(mjd: float) -> datetime:
    return MJD_START_DATE + timedelta(days=mjd)

def lambda_handler(event: Dict[str, Any], contex: Dict[str, Any]) -> Dict[str, Any]:
    date = str(event.get("date"))
    hour = int(event.get("hour",-1))
    dt = datetime.fromisoformat(date) + timedelta(hours=hour)
    interval_start:datetime = dt
    interval_end: datetime = dt + timedelta(hours=6)

    return {
        "statusCode": 200,
    }

def read_dataset():
    s3 = s3fs.S3FileSystem(profile='odin-cdk')
    stores = [
        s3fs.S3Map(root='s3://odin-era5/output-21-18.zarr', check=False, s3=s3),
        s3fs.S3Map(root='s3://odin-era5/output-22-12.zarr', check=False, s3=s3),
        s3fs.S3Map(root='s3://odin-era5/output-22-00.zarr', check=False, s3=s3),
        s3fs.S3Map(root='s3://odin-era5/output-22-06.zarr', check=False, s3=s3),
    ]
    datasets = [xarray.open_zarr(store) for store in stores]
    combined = xarray.concat(datasets, dim='time')
    combined.sortby('time')


def save_dataset():
    ds = xarray.open_dataset('ea_pl_2023-06-21-18.nc')
    s3 = s3fs.S3FileSystem(profile='odin-cdk')
    output_url = 's3://odin-era5/output-21-18.zarr'
    store = s3fs.S3Map(root=output_url, s3=s3, check=False)
    ds.to_zarr(store=store)