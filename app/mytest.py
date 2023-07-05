from .zpt.handler.create_zpt import lambda_handler
from os import environ
if __name__ == "__main__":
    environ['AWS_PROFILE']="odin-cdk"
    era5, scan = lambda_handler(
        {"start_date": "2022-09-05T05:15Z", "end_date": "2022-09-05T15:32"}, {}
    )
