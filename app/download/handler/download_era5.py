from .download import download_data


def lambda_handler(event, context):
    time_out = context.get_remaining_time_in_millis() / 1000 - 20
    result = download_data(event["date"], "pl", event["hour"], time_out)
    return result
