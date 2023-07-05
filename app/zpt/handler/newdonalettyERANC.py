import os
from datetime import datetime

import nrlmsise00 as M90  # type:ignore
import numpy as np
import xarray
from scipy.integrate import odeint  # type:ignore
from scipy.interpolate import BSpline, splrep  # type:ignore

from .geos import intermbar

AVOGADRO = 6.02282e23  # [mol^-1] aovogadros number
Ro = 8.3143  # [J * mol^-1 * K^-1] ideal gas constant


class Donaletty:
    """
    Create ZPT2 file using the new NetCDF ECMWF files
    Created
        Donal Murtagh July 2011.

    """

    def donaletty(self, g5zpt, scan_datetime, newz, lat, lon):
        """Inputs :
                g5zpt : heights (km) Pressure (hPa) and temperature profile
                        should extend to at least 60 km
                scan_datetime : datetime object
                lat : latitude of observation
        Output : ZPT array [3, 0-120]
        """

        def intatm(z, T, newz, normz, normrho, lat):
            """Integrates the temperature profile to yield a new model
            atmosphere in hydrostatic equilibrium including the effect of
            g(z) and M(z).
            newT, p, rho, nodens, n2, o2, o = intatm(z, T, newz, normz,normrho)
            NOTE z in km and returns pressure in pa
            """
            wn2 = 0.78084  # mixing ratio N2
            wo2 = 0.209476  # mixing ratio O2
            k = 1.38054e-23  # jK-1 Boltzmans constant
            m0 = 28.9644

            def func(_, z, bspl_eval):
                return bspl_eval(z)

            def spline(xk, yk, xnew):
                t_i, c_i, k_i = splrep(xk, yk, k=3)
                bspl_eval = BSpline(t_i, c_i, k_i)
                return bspl_eval(xnew)

            newT = spline(z, T, newz)
            mbar_over_m0 = intermbar(newz) / m0
            t_i, c_i, k_i = splrep(newz, g(newz, lat) / newT * mbar_over_m0, k=3)
            bspl_eval = BSpline(t_i, c_i, k_i)

            integral = odeint(func, 0, newz, args=(bspl_eval,))
            integral = 3.483 * np.squeeze(integral.transpose())
            integral = newT[1] / newT * mbar_over_m0 * np.exp(-integral)

            normfactor = normrho / spline(newz, integral, normz)
            rho = normfactor * integral
            nodens = rho / intermbar(newz) * AVOGADRO / 1e3
            n2 = wn2 * mbar_over_m0 * nodens
            o2 = nodens * (mbar_over_m0 * (1 + wo2) - 1)
            o = 2 * (1 - mbar_over_m0) * nodens
            o[o < 0] = 0
            p = nodens * 1e6 * k * newT
            return newT, p, rho, nodens, n2, o2, o

        # fix Msis from 70-150 km with solar effects
        msis = M90.Msis90(solardatafile=self.solardatafile)
        # to ensure an ok stratopause Donal wants to add a 50 km point
        # from msis
        msisz = np.r_[49.0, 50.0, 51, np.arange(75, 151, 1)]
        msisT = msis.extractPTZprofilevarsolar(scan_datetime, lat, lon, msisz)[1]
        z = np.r_[g5zpt[g5zpt[:, 0] < 60, 0], msisz]
        temp = np.r_[g5zpt[g5zpt[:, 0] < 60, 2], msisT]
        normrho = (
            np.interp([20], g5zpt[:, 0], g5zpt[:, 1])
            * 28.9644
            / 1000
            / Ro
            / np.interp([20], g5zpt[:, 0], g5zpt[:, 2])
        )
        newT, newp, _, _, _, _, _ = intatm(z, temp, newz, 20, normrho[0], lat)
        zpt = np.vstack((newz, newp, newT)).transpose()
        return zpt

    def get_filepath(self, date, hour):
        # ERA-Interim (ei) data is used before 2019-09-01,
        # and ERA5 (ea) data afterwards
        prefix = "ei" if date < datetime(2019, 9, 1).date() else "ea"
        return os.path.join(
            self.ecmwfpath,
            date.strftime("%Y/%m"),
            "{prefix}_pl_{date}-{hour}.nc".format(
                prefix=prefix, date=date.strftime("%Y-%m-%d"), hour=hour
            ),
        )

    def makeprofile(self, scans: xarray.Dataset):
        ecmz = np.arange(45) * 1000  # needs to be in metres
        newz = np.arange(151)

        T1 = self.ecm[0].extractprofile_on_z("t", latpt, lonpt, ecmz, 0)
        P1 = (
            self.ecm[0].extractprofile_on_z("p", latpt, lonpt, ecmz, 0) / 100.0
        )  # to hPa
        T2 = self.ecm[1].extractprofile_on_z("t", latpt, lonpt, ecmz, 0)
        P2 = (
            self.ecm[1].extractprofile_on_z("p", latpt, lonpt, ecmz, 0) / 100.0
        )  # to hPa
        T = (T1 * ((ibelow + 1) * 6.0 - hour) + T2 * (hour - ibelow * 6.0)) / 6.0
        P = (P1 * ((ibelow + 1) * 6.0 - hour) + P2 * (hour - ibelow * 6.0)) / 6.0
        # tempory fix in case ECMWF make temperatures below the surface nans,
        # P shouldn't matter
        T[np.isnan(T)] = 273.0
        zpt = self.donaletty(
            np.c_[ecmz / 1000, P, T], scan_datetime, newz, midlat, midlon
        )
        datadict = {
            "ScanID": scanid,
            "Z": zpt[:, 0],
            "P": zpt[:, 1],
            "T": zpt[:, 2],
            "latitude": midlat,
            "longitude": midlon,
            "datetime": scan_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        return datadict


def run_donaletty(scan_data):
    # create file
    donaletty = Donaletty()
    zpt = donaletty.makeprofile(midlat, midlon, date, scanid)
    save_zptfile(filepath, zpt)
    return zpt

    latest_file = sorted(os.listdir(os.path.join(basedir, latest_year, latest_month)))[
        -1
    ]
    return latest_file
