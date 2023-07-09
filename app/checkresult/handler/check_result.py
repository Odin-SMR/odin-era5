from cdsapi.api import Result, Client  # type: ignore


def lambda_handler(event, context):
    client = Client(progress=False, wait_until_complete=False, delete=False)
    result = Result(client, event)
    result.update()
    return result.reply
