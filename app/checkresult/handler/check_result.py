from cdsapi.api import Result, Client


def lambda_handler(event, context):
    client = Client(progress=False, wait_until_complete=False)
    result = Result(client, event)
    result.update()
    return result.reply
