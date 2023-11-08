from datetime import datetime
from pytest import raises

from app.sendrequest.handler.send_request import (
    CDSAPINotAvailableYet,
    CDSAPITooManyRequests,
    SendRequestEvent,
    lambda_handler,
)
from app.sendrequest.handler.settings import settings


def test_lambda_handler_cdsapi_not_available_yet(mocker):
    event = SendRequestEvent(date="2022-01-01", time_list=["00", "06", "12", "18"])
    send_request_mock = mocker.patch(
        "app.sendrequest.handler.send_request.send_request"
    )
    send_request_mock.side_effect = Exception("not yet available")
    with raises(CDSAPINotAvailableYet):
        lambda_handler(event, None)


def test_lambda_handler_cdsapi_too_many_requests(mocker):
    event = SendRequestEvent(date="2022-01-01", time_list=["00", "06", "12", "18"])
    send_request_mock = mocker.patch(
        "app.sendrequest.handler.send_request.send_request"
    )
    send_request_mock.side_effect = Exception("too many")
    with raises(CDSAPITooManyRequests):
        lambda_handler(event, None)


def test_lambda_handler_returns_some_data(mocker):
    event = SendRequestEvent(date="2022-01-01", time_list=["00", "06", "12", "18"])
    send_request_mock = mocker.patch(
        "app.sendrequest.handler.send_request.send_request"
    )
    send_request_mock.return_value = {}
    assert lambda_handler(event, None) == {}


def test_sendrequest_settings():
    config = settings([datetime(2023, 11, 8, 00, 00), datetime(2023, 11, 8, 12, 00)])
    assert "date" in config
    assert config["date"] == ["2023-11-08"]
    assert "time" in config
    assert config["time"] == ["00:00", "12:00"]
