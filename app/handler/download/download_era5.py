from download import download_data, PL


def lambda_handler(event, context):
    status = ""
    error = ""
    try:
        download_data(event["date"], PL, event["hour"])
        status = "success"
    except Exception as err:
        status = "failed"
        error = str(err)

    data = {
        "status": status,
        "date": event["date"],
        "hour": event["hour"],
        "error": error,
    }

    return {
        "statusCode": 200,
        "body": data,
        "headers": {
            "Content-Type": "application/json",
        },
    }
