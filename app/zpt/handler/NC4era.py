"""
Created on Mar 12, 2009
New version Oct 2014 - dicovered that geometric height was in the files
new version April 2015 - to use ERA interim or ERA5 files retreived
using the ECMWF API
@author: donal
"""
from itertools import product
from tempfile import NamedTemporaryFile
from netCDF4 import Dataset  # type: ignore
import numpy as np


class NCera:
    def __init__(self, filename, ind):
        """
        This routine will allow us to access
        """

        def readfield(fid, fieldname, lonsort, ind=0):
            np.disp("Reading field {}, index {}".format(fieldname, ind))
            field = np.array(fid.variables[fieldname])[ind, :, :, :]
            # field=np.r_[field]*field.scale_factor+field.add_offset
            field = np.ma.filled(field, np.nan)[:, :, lonsort]
            return field

        def geoid_radius(latitude):
            """
            Function from GEOS5 class.
            GEOID_RADIUS calculates the radius of the geoid at the given
            latitude
            [Re] = geoid_radius(latitude) calculates the radius of the geoid
            (km) at the given latitude (degrees).
            ----------------------------------------------------------------
                 Craig Haley 11-06-04
            ---------------------------------------------------------------
            """
            DEGREE = np.pi / 180.0
            EQRAD = 6378.14 * 1000
            FLAT = 1.0 / 298.257
            Rmax = EQRAD
            Rmin = Rmax * (1.0 - FLAT)
            Re = (
                np.sqrt(
                    1.0
                    / (
                        np.cos(latitude * DEGREE) ** 2 / Rmax**2
                        + np.sin(latitude * DEGREE) ** 2 / Rmin**2
                    )
                )
                / 1000
            )
            return Re

        def g(z, lat):
            # Re=6372;
            # g=9.81*(1-2.*z/Re)
            return (
                9.80616
                * (
                    1
                    - 0.0026373 * np.cos(2 * lat * np.pi / 180.0)
                    + 0.0000059 * np.cos(2 * lat * np.pi / 180.0) ** 2
                )
                * (1 - 2.0 * z / geoid_radius(lat))
            )

         ## read file from s3
        fid = Dataset(filename, "r")

        lats = fid.variables["latitude"]
        lats = np.r_[lats]
        lons = fid.variables["longitude"]
        # change longitudes from  0- 360 to -180 - 180
        lons = np.r_[lons]
        lons[lons > 180] = lons[lons > 180] - 360
        lonsort = lons.argsort()
        lons = lons[lonsort]
        pres = fid.variables["level"][:].astype(float) * 100  # millibar to Pa
        # make it 3d to match the old files
        # 480 longitudes
        # 241 latitudes
        # 37 levels
        pres = np.tile(pres, [480, 241, 1]).T
        z = readfield(fid, "z", lonsort, ind)
        gmh = np.zeros(z.shape)

        # Calculate gmh
        G0 = 9.80665  # ms**-2
        for ilat, lat in enumerate(lats):
            Re = geoid_radius(lat) * 1000  # to m
            for ip, pp in enumerate(pres):
                glat = g(z[ip, ilat, :] / G0 / 1000, lat)
                hr = z[ip, ilat, :] / G0
                # to km
                gmh[ip, ilat, :] = hr * Re / (glat * Re / G0 - hr) / 1000

        t = readfield(fid, "t", lonsort, ind)
        # Calculate  potential temperature
        theta = t * (1e5 / pres) ** 0.286
        cfn = "t"
        cf = t
        self.__keys = {
            "fid",
            "lats",
            "lons",
            "lonsort",
            "pres",
            "gmh",
            "theta",
            "CurrentFieldName",
            "CurrentField",
        }
        self.fid = fid
        self.lats = lats
        self.lons = lons
        self.lonsort = lonsort
        self.pres = pres
        self.gmh = gmh
        self.theta = theta
        self.CurrentFieldName = cfn
        self.CurrentField = cf

    def __getitem__(self, key):
        if key in self.__keys:
            return getattr(self, key)
        raise KeyError("{} not recognized key".format(key))

    def extractprofile_on_z(self, fieldname, latpt, longpt, newz, ind=0):
        z = self.gmh[:, latpt, longpt]
        if fieldname == "p":
            profile = np.interp(newz / 1e3, z[-1::-1], self.pres[-1::-1, latpt, longpt])
        else:
            field = self.readfield(fieldname, ind)
            profile = np.interp(newz / 1e3, z[-1::-1], field[-1::-1, latpt, longpt])
        return profile

    def readfield(self, fieldname, ind=0):
        np.disp("""Reading field {}, index {}""".format(fieldname, ind))
        field = np.array(self.fid.variables[fieldname])[ind, :, :, :]
        field = np.ma.filled(field, np.nan)[:, :, self.lonsort]
        self.CurrentField = field
        self.CurrentFieldName = fieldname
        return field

    def extractfield_on_p(self, fieldname, plevels):
        """
        This routine will extract a field on given pressure levels
        """
        # get the pressures on the model levels
        field = self.readfield(fieldname)
        logpres = np.log(self.pres)
        newfield = np.zeros((len(plevels), len(self.lats), len(self.lons)))
        for i, j in product(range(len(self.lats)), range(len(self.lons))):
            # f=interpolate.interp1d(
            # np.flipud(logpres[:,i,j]),np.flipud(field[:,i,j]))
            # newfield[:,i,j]=
            # np.interp(np.log(plevels),np.flipud(logpres[:,i,j]),
            # np.flipud(field[:,i,j]))
            newfield[:, i, j] = np.interp(
                np.log(plevels), logpres[:, i, j], field[:, i, j]
            )
        return newfield

    def extractfield_on_theta(self, fieldname, thlevels):
        """
        This routine will extract a field on given pressure levels
        """
        # get the pressures on the model levels
        field = self.readfield(fieldname)
        newfield = np.zeros((len(thlevels), len(self.lats), len(self.lons)))
        for i, j in product(range(len(self.lats)), range(len(self.lons))):
            # f=interpolate.interp1d(
            #    np.flipud(logpres[:,i,j]),np.flipud(field[:,i,j]))
            # newfield[:,i,j]=
            # np.interp(np.log(plevels),np.flipud(logpres[:,i,j]),
            # np.flipud(field[:,i,j]))
            newfield[:, i, j] = np.flipud(
                np.interp(
                    np.flipud(thlevels),
                    np.flipud(self.theta[:, i, j]),
                    np.flipud(field[:, i, j]),
                )
            )
        newfield = newfield[:, :, self.lonsort]  # sort longitudes
        return newfield

    def fileclose(self):
        self.fid.close()
