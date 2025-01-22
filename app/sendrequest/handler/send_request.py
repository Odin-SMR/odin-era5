from datetime import datetime
from typing import Any, Dict, List, TypedDict

import cdsapi  # type: ignore

from .settings import PRODUCT, settings

BUCKET = "odin-era5"


class SendRequestEvent(TypedDict):
    """
    date: date in iso-format
    time_list: list of times eg. ['00','12'].
    """

    date: str
    time_list: List[str]


class CDSAPINotAvailableYet(RuntimeError):
    pass


class CDSAPITooManyRequests(RuntimeError):
    pass


def send_request(date: datetime | List[datetime]) -> Dict[str, Any]:
    client = cdsapi.Client(progress=False, wait_until_complete=False, delete=False)
    result = client.retrieve(
        PRODUCT,
        settings(date),
    )
    return result.reply


def lambda_handler(event: SendRequestEvent, context):
    times: List[datetime] = []
    for time in event["time_list"]:
        dt = datetime.fromisoformat(f"{event['date']}T{time}")
        times.append(dt)

    try:
        result = send_request(times)
        return result
    except Exception as err:
        if "too many" in str(err):
            raise CDSAPITooManyRequests()
        if "yet" in str(err):
            raise CDSAPINotAvailableYet()
        raise err
