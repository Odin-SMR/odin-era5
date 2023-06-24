#!/usr/bin/env python3.8

import tempfile
import datetime
from typing import Any, Dict
import cdsapi  # type: ignore
import boto3

BUCKET = "odin-era5"

# command for retrieving parameters on pressure levels
# Parameter id reference: http://apps.ecmwf.int/codes/grib/param-db
# 60.128   : Potential vorticity
# 129.128  : Geopotential
# 130.128  : Temperature
# 133.128  : Specific humidity
# 138.128  : Vorticity (relative)
# 203.128  : Ozone mass mixing ratio
# 246.128  : Specific cloud liquid water content
PL = {
    "class": "ea",
    "grid": "0.75/0.75",
    "levelist": "1/2/3/5/7/10/20/30/50/70/100/125/150/175/200/225/250/300/350/400/450/500/550/600/650/700/750/775/800/825/850/875/900/925/950/975/1000",  # noqa
    "levtype": "pl",
    "param": "60.128/129.128/130.128/133.128/138.128/203.128/246.128",
    "product_type": "reanalysis",
    "format": "netcdf",
}


# command for retrieving parameters on surface level
# Parameter id reference: http://apps.ecmwf.int/codes/grib/param-db
# 134 : Surface pressure
# 165 : 10 metre U wind component
# 166 : 10 metre V wind component
# 235 : Skin temperature
SFC = {
    "class": "ea",
    "grid": "0.75/0.75",
    "levtype": "sfc",
    "param": "134.128/165.128/166.128/235.128",
    "product_type": "reanalysis",
    "format": "netcdf",
}


def get_dataset_and_settings(levtype: str, date: str, hour: str):
    dt = datetime.date.fromisoformat(date)
    settings = {
        "year": dt.strftime("%Y"),
        "month": dt.strftime("%m"),
        "day": dt.strftime("%d"),
        "time": f"{hour}:00",
    }
    if levtype == "pl":
        settings.update(PL)
        dataset = "reanalysis-era5-pressure-levels"
    else:
        settings.update(SFC)
        dataset = "reanalysis-era5-complete"
    return dataset, settings


def download_data(date: str, levtype: str, hour: str, time_out: int) -> Dict[str, Any]:
    s3_client = boto3.client("s3")

    dataset, settings = get_dataset_and_settings(levtype, date, hour)
    target_file = "{}_{}_{}-{}.nc".format(
        settings["class"],
        settings["levtype"],
        date,
        hour,
    )
    dt = datetime.date.fromisoformat(date)
    target_dir = f"{dt.year}/{dt.month:02}/"
    with tempfile.NamedTemporaryFile() as f:
        server = cdsapi.Client(progress=False, timeout=time_out)
        request = server.retrieve(
            dataset,
            settings,
            f.name,
        )
        s3_client.upload_fileobj(f, BUCKET, target_dir + target_file)
    return request.reply
