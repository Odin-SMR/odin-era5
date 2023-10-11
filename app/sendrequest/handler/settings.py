from datetime import datetime
from typing import Any, Dict, Iterable, List

PRODUCT = "reanalysis-era5-pressure-levels"

SETTINGS = {
    "product_type": "reanalysis",
    "format": "netcdf",
    "grid": [0.75, 0.75],
    "pressure_level": [
        "1",
        "2",
        "3",
        "5",
        "7",
        "10",
        "20",
        "30",
        "50",
        "70",
        "100",
        "125",
        "150",
        "175",
        "200",
        "225",
        "250",
        "300",
        "350",
        "400",
        "450",
        "500",
        "550",
        "600",
        "650",
        "700",
        "750",
        "775",
        "800",
        "825",
        "850",
        "875",
        "900",
        "925",
        "950",
        "975",
        "1000",
    ],
    "variable": ["temperature", "geopotential"],
}


def settings(dt: datetime | Iterable[datetime]) -> Dict[str, Any]:
    if isinstance(dt, Iterable):
        date: List[str] = []
        time: List[str] = []
        for d in dt:
            date.append(d.date().isoformat())
            time.append(d.time().strftime("%H:%M"))
        settings = SETTINGS.copy()
        settings.update(date=sorted(set(date)), time=sorted(set(time)))
        return settings

    else:
        settings = SETTINGS.copy()
        settings.update(date=dt.date().isoformat(), time=dt.time().strftime("%H:%M"))
        return settings
