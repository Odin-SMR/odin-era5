import numpy as np
import xarray
from pandas import to_datetime

from .atmos import intatm
from .msis90 import Msis90 as M90

Ro = 8.3143  # [J * mol^-1 * K^-1] ideal gas constant


class Donaletty:
    """
    Create ZPT2 file using the new NetCDF ECMWF files
    Created
        Donal Murtagh July 2011.

    """

    def donaletty(self, scan_data, newz):
        """Inputs :
                g5zpt : heights (km) Pressure (hPa) and temperature profile
                        should extend to at least 60 km
                scan_datetime : datetime object
                lat : latitude of observation
        Output : ZPT array [3, 0-120]
        """

        # fix Msis from 70-150 km with solar effects
        msis = M90()
        # to ensure an ok stratopause Donal wants to add a 50 km point
        # from msis
        msisz = np.r_[49.0, 50.0, 51, np.arange(75, 151, 1)]
        scan_datetime = to_datetime(scan_data.mid_date.data).to_pydatetime()
        msisT = msis.extractPTZprofilevarsolar(
            scan_datetime, scan_data.latitude, scan_data.longitude, msisz
        )[1]
        z = np.r_[scan_data.era5_gmh.data, msisz]
        temp = np.r_[scan_data.era5_t, msisT]
        normrho = (
            np.interp([20], scan_data.era5_gmh, scan_data.era5_level)
            * 28.9644
            / 1000
            / Ro
            / np.interp([20], scan_data.era5_gmh, scan_data.era5_t)
        )
        newT, newp, _, _, _, _, _ = intatm(
            z, temp, newz, 20, normrho[0], scan_data.latitude
        )
        zpt = xarray.Dataset(
            data_vars=dict(
                scanid=(["id"], scan_data.scanid),
                p=(["z"], newp),
                t=(["z"], newT),
            ),
            coords=dict(
                gmh=(["z"], newz),
                scanid=(["id"], scan_data.scanid),
            ),
        )
        return zpt

    def makeprofile(self, scans: xarray.Dataset):
        ecmz = np.arange(45)
        newz = np.arange(151)
        scan_on_interp_gmh = scans.groupby("scanid").map(
            lambda ds: ds.swap_dims(level="era5_gmh").interp(era5_gmh=ecmz)
        )
        zpt_donaletty = scan_on_interp_gmh.groupby("scanid").map(
            self.donaletty, args=(newz,)
        )
        return zpt_donaletty
