import cdsapi  # type: ignore


def lambda_handler(event, context):
    client = cdsapi.Client(progress=False, wait_until_complete=False, delete=False)
    result = client.client.get_remote(event["request_id"])  # type: ignore
    return result.reply
