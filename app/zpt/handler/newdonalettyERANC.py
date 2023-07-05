# fmt: off
# mypy: ignore-errors
import os
import re
import datetime as DT
from datetime import datetime

from netCDF4 import Dataset
import numpy as np
from scipy.integrate import odeint
from scipy.interpolate import BSpline, splrep
from simpleflock import SimpleFlock

from . import msis90 as M90
from .NC4era import NCera
from .time_util import mjd2datetime, datetime2mjd

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
            wn2 = 0.78084    # mixing ratio N2
            wo2 = 0.209476   # mixing ratio O2
            k = 1.38054e-23  # jK-1 Boltzmans constant
            m0 = 28.9644

            def geoid_radius(latitude):
                """
                Function from GEOS5 class.
                GEOID_RADIUS calculates the radius of the geoid at the given
                latitude.
                [Re] = geoid_radius(latitude) calculates the radius of the
                geoid (km) at the given latitude (degrees).
                ---------------------------------------------------------------
                Craig Haley 11-06-04
                ---------------------------------------------------------------
                """
                EQRAD = 6378.14 * 1000
                FLAT = 1.0 / 298.257
                Rmax = EQRAD
                Rmin = Rmax * (1.0 - FLAT)
                Re = np.sqrt(1. / (
                    np.cos(np.radians(latitude)) ** 2 / Rmax ** 2
                    + np.sin(np.radians(latitude)) ** 2 / Rmin ** 2
                )) / 1000
                return Re

            def intermbar(z):
                mbars = np.r_[
                    28.9644, 28.9151, 28.73, 28.40, 27.88, 27.27, 26.68, 26.20,
                    25.80, 25.44, 25.09, 24.75, 24.42, 24.10]
                mbarz = np.arange(85, 151, 5)
                m = np.interp(z, mbarz, mbars)
                return m

            def g(z, lat):
                # reference: The Earth's Atmosphere: Its Physics and Dynamics
                # (Eq. 1.2.4)
                # e.g 9.80616 [ms^-2] acceleration (gravity) at mean sea level
                # at 45 degree
                return 9.80616 * (
                    1 - 0.0026373 * np.cos(2 * np.radians(lat)) +
                    0.0000059 * np.cos(2 * np.radians(lat)) ** 2
                ) * (1 - 2. * z / geoid_radius(lat))

            def func(_, z, bspl_eval):
                return bspl_eval(z)

            def spline(xk, yk, xnew):
                t_i, c_i, k_i = splrep(xk, yk, k=3)
                bspl_eval = BSpline(t_i, c_i, k_i)
                return bspl_eval(xnew)

            newT = spline(z, T, newz)
            mbar_over_m0 = intermbar(newz) / m0
            t_i, c_i, k_i = splrep(
                newz, g(newz, lat) / newT * mbar_over_m0, k=3)
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
        msisz = np.r_[49., 50., 51, np.arange(75, 151, 1)]
        msisT = msis.extractPTZprofilevarsolar(
            scan_datetime, lat, lon, msisz)[1]
        z = np.r_[g5zpt[g5zpt[:, 0] < 60, 0], msisz]
        temp = np.r_[g5zpt[g5zpt[:, 0] < 60, 2], msisT]
        normrho = (
            np.interp([20], g5zpt[:, 0], g5zpt[:, 1]) * 28.9644 / 1000 / Ro
            / np.interp([20], g5zpt[:, 0], g5zpt[:, 2])
        )
        newT, newp, _, _, _, _, _ = intatm(
            z, temp, newz, 20, normrho[0], lat)
        zpt = np.vstack((newz, newp, newT)).transpose()
        return zpt

    def loadecmwfdata(self):

        # load all ecmwffiles for the day
        hourlist = ['00', '06', '12', '18', '24']
        hour = self.datetime.hour
        ibelow = hour // 6
        self.ecm = []
        for ind in range(ibelow, ibelow+2):
            hourstr = hourlist[ind]
            if hourstr == '24':
                # we need to read data from one day later : time 00
                date = self.datetime.date() + DT.timedelta(days=1)
                hourstr = '00'
            else:
                date = self.datetime.date()
            ecmwffilename = self.get_filepath(date, hourstr)
            # TODO: Opening more than one netcdf file at the same time
            #       can result in segfault.
            self.ecm.append(NCera(ecmwffilename, 0))

        self.minlat = self.ecm[0]['lats'][0]
        self.latstep = np.mean(np.diff(self.ecm[0]['lats']))
        self.minlon = self.ecm[0]['lons'][0]
        self.lonstep = np.mean(np.diff(self.ecm[0]['lons']))

    def get_filepath(self, date, hour):
        # ERA-Interim (ei) data is used before 2019-09-01,
        # and ERA5 (ea) data afterwards
        prefix = "ei" if date < datetime(2019, 9, 1).date() else "ea"
        return os.path.join(
            self.ecmwfpath,
            date.strftime('%Y/%m'),
            '{prefix}_pl_{date}-{hour}.nc'.format(
                prefix=prefix,
                date=date.strftime('%Y-%m-%d'),
                hour=hour
            )
        )

    def makeprofile(self, midlat, midlon, scan_datetime, scanid):

        ecmz = np.arange(45) * 1000  # needs to be in metres
        newz = np.arange(151)
        # extract T and P for the mid lat and long of each scan
        if midlon > 180:
            midlon = midlon - 360
        latpt = int(np.floor((midlat - self.minlat) / self.latstep))
        lonpt = int(np.floor((midlon - self.minlon) / self.lonstep))
        if midlon < 0:
            midlon = midlon + 360
        hour = scan_datetime.hour
        ibelow = hour // 6  # index in file w.r.t time
        # iabove = ibelow + 1 #not needed, files only contain one time index
        # if iabove==4:
        #     iabove = 0
        T1 = self.ecm[0].extractprofile_on_z('t', latpt, lonpt, ecmz, 0)
        P1 = self.ecm[0].extractprofile_on_z(
            'p', latpt, lonpt, ecmz, 0) / 100.  # to hPa
        T2 = self.ecm[1].extractprofile_on_z('t', latpt, lonpt, ecmz, 0)
        P2 = self.ecm[1].extractprofile_on_z(
            'p', latpt, lonpt, ecmz, 0) / 100.  # to hPa
        T = (T1 * ((ibelow + 1) * 6. - hour) + T2 * (hour - ibelow * 6.)) / 6.
        P = (P1 * ((ibelow + 1) * 6. - hour) + P2 * (hour - ibelow * 6.)) / 6.
        # tempory fix in case ECMWF make temperatures below the surface nans,
        # P shouldn't matter
        T[np.isnan(T)] = 273.0
        zpt = self.donaletty(
            np.c_[ecmz / 1000, P, T], scan_datetime, newz, midlat, midlon)
        datadict = {
            'ScanID': scanid,
            'Z': zpt[:, 0],
            'P': zpt[:, 1],
            'T': zpt[:, 2],
            'latitude': midlat,
            'longitude': midlon,
            'datetime': scan_datetime.strftime('%Y-%m-%dT%H:%M:%S')}
        return datadict

    def __init__(self, scan_datetime, solardatafile, ecmwfpath):
        self.datetime = scan_datetime
        self.solardatafile = solardatafile
        self.ecmwfpath = ecmwfpath
        self.ecm = []
        self.minlat = None
        self.latstep = None
        self.minlon = None
        self.lonstep = None


def save_zptfile(filename, zpt):
    with Dataset(filename, 'w', format='NETCDF4') as rootgrp:
        datagrp = rootgrp.createGroup('Data')
        datagrp.createDimension('level', 151)

        altitude = datagrp.createVariable('Z', 'f4', ('level',))
        altitude.units = 'Km'
        altitude[:] = zpt['Z']
        pressure = datagrp.createVariable('P', 'f4', ('level',))
        pressure.units = 'hPa'
        pressure[:] = zpt['P']

        temperature = datagrp.createVariable('T', 'f4', ('level',))
        temperature.units = 'K'
        temperature[:] = zpt['T']

        latitude = datagrp.createVariable('latitude', 'f4')
        latitude.units = 'degrees north'
        latitude[:] = zpt['latitude']

        longitude = datagrp.createVariable('longitude', 'f4')
        longitude.units = 'degrees east'
        longitude[:] = zpt['longitude']

        rootgrp.description = (
            'PTZ data for odin-smr level2-processing data source is '
            'ECMWF and NRLMSIS91')
        rootgrp.history = 'Created ' + str(DT.datetime.now())
        rootgrp.geoloc_latitude = "{0} degrees north".format(zpt['latitude'])
        rootgrp.geoloc_longitude = "{0} degrees east".format(zpt['longitude'])
        rootgrp.geoloc_datetime = "{0}".format(zpt['datetime'])


def load_zptfile(filepath, scanid):
    with Dataset(filepath, mode='r') as dataset:
        data = dataset.groups['Data']
        zpt = {
            'ScanID': scanid,
            'Z': data.variables['Z'][:],
            'P': data.variables['P'][:],
            'T': data.variables['T'][:],
            'latitude': float(data.variables['latitude'][:]),
            'longitude': float(data.variables['longitude'][:]),
            'datetime': dataset.geoloc_datetime}
    return zpt


def get_filename(basedir, date, scanid):
    return os.path.join(
        basedir,
        date.strftime('%Y/%m/'),
        "ZPT_{0}.nc".format(scanid)
    )


def run_donaletty(
        mjd, midlat, midlon, scanid,
        ecmwfpath='/var/lib/odindata/ECMWF',
        solardatafile='/var/lib/odindata/Solardata2.db',
        zptpath='/var/lib/odindata/ZPT'):

    date = mjd2datetime(mjd)
    filepath = get_filename(zptpath, date, scanid)

    if not os.path.exists(os.path.dirname(filepath)):
        os.makedirs(os.path.dirname(filepath))

    with SimpleFlock(filepath + '.lock', timeout=600):
        try:
            zpt = load_zptfile(filepath, scanid)
        except (IOError, KeyError, FileNotFoundError):
            # create file
            donaletty = Donaletty(date, solardatafile, ecmwfpath)
            donaletty.loadecmwfdata()
            zpt = donaletty.makeprofile(midlat, midlon, date, scanid)
            save_zptfile(filepath, zpt)

    zpt['datetime'] = datetime2mjd(
        datetime.strptime(zpt['datetime'], '%Y-%m-%dT%H:%M:%S'))
    return zpt


def get_latest_ecmf_file():
    """Return the file name of the latest ecmf file"""
    basedir = '/var/lib/odindata/ECMWF'

    def is_digit_dir(name):
        if not os.path.isdir(os.path.join(basedir, name)):
            return False
        if not name.isdigit():
            return False
        return True

    latest_year = list(filter(is_digit_dir, sorted(os.listdir(basedir))))
    if not latest_year:
        return None
    latest_year = latest_year[-1]
    latest_month = sorted(
        os.listdir(os.path.join(basedir, latest_year)))[-1]
    latest_file = sorted(
        os.listdir(os.path.join(basedir, latest_year, latest_month)))[-1]
    return latest_file


def get_latest_ecmf_date():
    return get_ecmf_file_date(get_latest_ecmf_file())


def get_ecmf_file_date(file_name):
    if not file_name:
        return
    ecmf_pattern = r'\w+_\w+_(?P<date>\d\d\d\d-\d\d-\d\d)-\d\d.nc$'
    match = re.match(ecmf_pattern, file_name)
    if not match:
        raise ValueError('Could not recognize ecmf file: %r' % file_name)
    return match.group('date')
