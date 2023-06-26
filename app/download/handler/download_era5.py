from .download import download_data


class CDSAPINotAvailableYet(RuntimeError):
    pass


class CDSAPITooManyRequests(RuntimeError):
    pass


def lambda_handler(event, context):
    try:
        result = download_data(event["date"], "pl", event["hour"])
        return result
    except Exception as err:
        if "too many" in str(err):
            raise CDSAPITooManyRequests()
        if "yet" in str(err):
            raise CDSAPINotAvailableYet()
        raise err
