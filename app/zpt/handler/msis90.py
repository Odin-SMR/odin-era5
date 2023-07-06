# mypy: ignore-errors
#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
#
#  msis90.py
#
#  Copyright 2015 Donal Murtagh <donal@chalmers.se>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

# fmt: off
import numpy as np
import nrlmsise00
import sqlite3 as sqlite
kB = 1.3806488E-23  # m2 kg s-2 K-1


class Msis90:
    '''class for access to MSIS90e model'''

    def __init__(
        self, solardatafile='/home/donal/Dropbox/solar/Solardata2.db',
    ):
        nrlmsis.meters(1)  # turn on SI units
        self.solardatafile = solardatafile

    def extractPTZprofilevarsolar(self, datetime, lat, lng, altitudes):
        db = sqlite.connect(self.solardatafile)
        cur = db.cursor()
        selectstr = (
            'select APAvg, ObsF10_7, ObsCtr81 from solardata where id ='
            + str(datetime.year * 10000 + datetime.month * 100 + datetime.day)
        )
        apavg, f107, f107a = cur.execute(selectstr).fetchall()[0]
        ap = apavg * np.ones(7, 'f')
        db.close()
        mass = 48
        iydd = datetime.timetuple().tm_yday
        ut = datetime.hour * 3600 + datetime.minute * 60 + datetime.second
        P = np.zeros(altitudes.shape)
        T = np.zeros(altitudes.shape)
        Z = altitudes
        for i, alt in enumerate(altitudes):
            d = np.zeros(9, 'f')
            t = np.zeros(2, 'f')
            nrlmsis.gtd7(
                iydd, ut, alt, lat, lng, ut / 3600 - lng / 15, f107a, f107, ap,
                mass, d, t,
            )
            T[i] = t[1]
            P[i] = (d.sum() - d[5]) * kB * t[1] / 100.

        return P, T, Z

    def extractPTZprofilefixedsolar(self, datetime, lat, lng, altitudes):
        f107a = 100
        f107 = 100
        ap = 4 * np.ones(7)
        mass = 48
        iydd = datetime.timetuple().tm_yday
        ut = datetime.hour * 3600 + datetime.minute * 60 + datetime.second
        P = np.zeros(altitudes.shape)
        T = np.zeros(altitudes.shape)
        Z = altitudes
        for i, alt in enumerate(altitudes):
            d, t = nrlmsis.gtd7(
                iydd, ut, alt, lat, lng, ut / 3600 - lng / 15, f107a, f107, ap,
                mass,
            )
            T[i] = t[1]
            P[i] = (d.sum() - d[5]) * kB * t[1] / 100.
        return P, T, Z
