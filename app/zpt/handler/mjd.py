from datetime import datetime, timedelta

import arrow

MJD_START_DATE = arrow.get("1858-11-17T00Z").datetime
DAYS_PER_SECOND = 1.0 / 60 / 60 / 24


def datetime2mjd(dt: datetime) -> float:
    return (dt - MJD_START_DATE).total_seconds() * DAYS_PER_SECOND


def mjd2datetime(mjd: float) -> datetime:
    return MJD_START_DATE + timedelta(days=mjd)
