# fmt: off
# mypy: ignore-errors
from datetime import datetime, timedelta


MJD_ODIN_REBOOT = 59247
MJD_START_DATE = datetime(1858, 11, 17)


def datetime2mjd(dt: datetime) -> float:
    return (
        (dt - MJD_START_DATE).total_seconds()
        * datetime2mjd.days_per_second
    )


datetime2mjd.days_per_second = 1. / 60 / 60 / 24


def datetime2stw(dt: datetime) -> int:
    return mjd2stw(datetime2mjd(dt))


def mjd2stw(mjd: float) -> int:
    """
    Convert from mjd (modified julian date) to stw (satellite time word
    or the internal time of Odin). The conversion is not exact so the
    function should only be used when an exakt stw is not needed. It is
    a close to linear relationship between mjd and stw, except that a big
    jump is found around the Odin reboot date in February 2021.
    """
    if mjd >= MJD_ODIN_REBOOT:
        a = -6.89789762 * 1e10
        b = 1.38121393 * 1e6
        c = 1.12346880 * 1e-2
        d = 0.
    else:
        a = - 7.18192098 * 1e10
        b = 1.38161488 * 1e6
        c = 1.59079812 * 1e-2
        d = - 9.05026091 * 1e-8
    return int(a + b * mjd + c * mjd ** 2 + d * mjd ** 3)


def stw2mjd(stw: int) -> float:
    """
    Convert from stw to mjd in an approximate manner.
    """
    if stw >= mjd2stw(MJD_ODIN_REBOOT):
        # if stw later than odin reboot
        a = 4.99205631 * 1e4
        b = 7.23413455 * 1e-7
        c = -4.25743315 * 1e-21
        d = 0.
    else:
        a = 5.19601792 * 1e4
        b = 7.23308989 * 1e-7
        c = -6.81289563 * 1e-22
        d = 2.47714080 * 1e-32
    return (a + b * stw + c * stw ** 2 + d * stw ** 3)


def mjd2datetime(mjd: float) -> datetime:
    return MJD_START_DATE + timedelta(days=mjd)


def stw2datetime(stw: int) -> datetime:
    return mjd2datetime(stw2mjd(stw))
