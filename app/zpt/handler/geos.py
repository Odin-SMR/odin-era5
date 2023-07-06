import numpy as np


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


def gmh(lats, z):
    # Calculate gmh
    G0 = 9.80665  # ms**-2
    Re = geoid_radius(lats) * 1000  # to m
    glat = g(z / G0 / 1000, lats)
    hr = z / G0
    return hr * Re / (glat * Re / G0 - hr) / 1000 # back to km


