from typing import Any, Dict

import arrow
from pandas import date_range, to_datetime

from .newdonalettyERANC import Donaletty

from .era5_dataset import get_dataset
from .geoloc_tools import getscangeoloc
from .geos import gmh
from .mjd import mjd2datetime
from .scanid import ScanInfo
from .ssm_parameters import get_parameters
from .scan_data_descriptions import parameter_desc


def lambda_handler(event: Dict[str, Any], context: Dict[str, Any]):
    interval_start = arrow.get(f"{event['start_date']}")
    interval_end = arrow.get(f"{event['end_date']}")

    pg_credentials = get_parameters(
        ["/odin/psql/user", "/odin/psql/db", "/odin/psql/host", "/odin/psql/password"]
    )

    l1_connect_string = (
        f"postgresql+psycopg://{pg_credentials.user}:{pg_credentials.password}@"
        f"{pg_credentials.host}/{pg_credentials.db}?sslmode=verify-ca"
    )

    level1db = ScanInfo(l1_connect_string)
    scan_data = level1db.get_scan_info(interval_start.datetime, interval_end.datetime)
    scan_data["mjd_mid"] = (scan_data["mjd"] + scan_data["end_mjd"]) / 2
    scan_data["mid_date"] = scan_data["mjd_mid"].apply(
        lambda x: mjd2datetime(x).replace(tzinfo=None)
    )
    scan_data["mid_latitude"], scan_data["mid_longitude"] = getscangeoloc(
        scan_data["latitude"],
        scan_data["longitude"],
        scan_data["end_latitude"],
        scan_data["end_longitude"],
    )
    scans = scan_data.set_index("scanid").to_xarray()
    scans.scanid.attrs = parameter_desc["scanid"]
    scans.mid_date.attrs = parameter_desc["mid_date"]
    scans.backend.attrs = parameter_desc["backend"]
    scans.latitude.attrs = parameter_desc["latitude"]
    scans.longitude.attrs = parameter_desc["longitude"]
    scans.mjd.attrs = parameter_desc["mjd"]
    scans.mid_latitude.attrs = parameter_desc["mid_latitude"]
    scans.mid_longitude.attrs = parameter_desc["mid_longitude"]
    scans.mjd_mid.attrs = parameter_desc["mjd_mid"]
    scans.end_latitude.attrs = parameter_desc["end_latitude"]
    scans.end_longitude.attrs = parameter_desc["end_longitude"]
    scans.end_mjd.attrs = parameter_desc["end_mjd"]

    era5_timesteps = date_range(
        to_datetime(interval_start.datetime).floor(freq="6H"),
        to_datetime(interval_end.datetime).ceil(freq="6H"),
        freq="6H",
    )
    era5_data = get_dataset(era5_timesteps)

    era5_data["longitude"] = era5_data.longitude - 180
    scans["era5_level"] = era5_data.level
    scans["era5_z"] = (
        ["scanid", "level"],
        era5_data.z.sel(
            latitude=scans["mid_latitude"],
            longitude=scans["mid_longitude"],
            time=scans["mid_date"],
            method="nearest",
        ).data,
    )
    scans.era5_z.attrs = era5_data.z.attrs
    scans["era5_t"] = (
        ["scanid", "level"],
        era5_data.t.sel(
            latitude=scans["mid_latitude"],
            longitude=scans["mid_longitude"],
            time=scans["mid_date"],
            method="nearest",
        ).data,
    )
    scans.era5_t.attrs = era5_data.t.attrs
    scans["era5_gmh"] = gmh(scans.mid_latitude, scans.era5_z)
    scans.era5_gmh.attrs = {"long_name": "geometric height", "units": "km"}
    scans["theta"] = scans["era5_t"] * (1e3 / scans["level"]) ** 0.286 # pressure in mb
    scans.theta.attrs = {"long_name": "Potential temperature", "units": "K"}

    # donaletty = Donaletty()
    # return donaletty.makeprofile(scandata)
    return scans

