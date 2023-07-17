from datetime import datetime

from pytest import raises

from app.sendrequest.handler.send_request import (
    CDSAPINotAvailableYet,
    CDSAPITooManyRequests,
    SendRequestEvent,
    lambda_handler
)
from app.sendrequest.handler.settings import settings


def test_cds_api_single_date_settings():
    dt = datetime(2001, 1, 1, 0, 0)
    single_date = settings(dt)
    assert single_date["date"] == "2001-01-01"
    assert single_date["time"] == "00:00"


def test_cds_api_multiple_date_settings():
    dt = datetime(2001, 1, 1, 0, 0), datetime(2001, 1, 1, 12, 0)
    multiple_date = settings(dt)
    assert multiple_date["date"] == ["2001-01-01"]
    assert multiple_date["time"] == ["00:00", "12:00"]


def test_lambda_handler_cdsapi_not_available_yet(mocker):
    event = SendRequestEvent(time_list=["2022-01-01T12:00:00"])
    send_request_mock = mocker.patch(
        "app.sendrequest.handler.send_request.send_request"
    )
    send_request_mock.side_effect = Exception("not yet available")
    with raises(CDSAPINotAvailableYet):
        lambda_handler(event, None)


def test_lambda_handler_cdsapi_too_many_requests(mocker):
    event = SendRequestEvent(time_list=["2022-01-01T12:00:00"])
    send_request_mock = mocker.patch(
        "app.sendrequest.handler.send_request.send_request"
    )
    send_request_mock.side_effect = Exception("too many")
    with raises(CDSAPITooManyRequests):
        lambda_handler(event, None)


def test_lambda_handler_returns_some_data(mocker):
    event = SendRequestEvent(time_list=["2022-01-01T12:00:00"])
    send_request_mock = mocker.patch(
        "app.sendrequest.handler.send_request.send_request"
    )
    send_request_mock.return_value = {}
    assert lambda_handler(event, None) == {}
