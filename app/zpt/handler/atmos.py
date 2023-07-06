import numpy as np
from scipy.integrate import odeint  # type: ignore
from scipy.interpolate import BSpline, splrep  # type: ignore

from .geos import g  # type:ignore

AVOGADRO = 6.02282e23  # [mol^-1] aovogadros number


def intermbar(z):
    mbars = np.r_[
        28.9644,
        28.9151,
        28.73,
        28.40,
        27.88,
        27.27,
        26.68,
        26.20,
        25.80,
        25.44,
        25.09,
        24.75,
        24.42,
        24.10,
    ]
    mbarz = np.arange(85, 151, 5)
    m = np.interp(z, mbarz, mbars)
    return m


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
