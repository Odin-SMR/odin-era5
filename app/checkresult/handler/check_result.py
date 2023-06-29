from os import environ
import boto3
import cdsapi


def lambda_handler(event, context):
    ssm = boto3.client("ssm", region_name="eu-north-1")

    # Get the parameter
    key = ssm.get_parameter(Name="/odin/cdsapi/key", WithDecryption=True)
    url = ssm.get_parameter(
        Name="/odin/cdsapi/url",
    )
    environ["CDSAPI_KEY"] = key["Parameter"]["Value"]
    environ["CDSAPI_URL"] = url["Parameter"]["Value"]
    client = cdsapi.Client(progress=False, wait_until_complete=False)
    result = client.robust(client.session.post)
    result.raise_for_status()
    return result.json()
