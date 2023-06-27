from os import environ

import boto3

from .download import download_data


class CDSAPINotAvailableYet(RuntimeError):
    pass


class CDSAPITooManyRequests(RuntimeError):
    pass


def lambda_handler(event, context):
    ssm = boto3.client("ssm", region_name="eu-north-1")

    # Get the parameter
    key = ssm.get_parameter(Name="/odin/cdsapi/key", WithDecryption=True)
    url = ssm.get_parameter(
        Name="/odin/cdsapi/url",
    )
    environ["CDSAPI_KEY"] = key["Parameter"]["Value"]
    environ["CDSAPI_URL"] = url["Parameter"]["Value"]
    try:
        result = download_data(event["date"], "pl", event["hour"])
        return result
    except Exception as err:
        if "too many" in str(err):
            raise CDSAPITooManyRequests()
        if "yet" in str(err):
            raise CDSAPINotAvailableYet()
        raise err
