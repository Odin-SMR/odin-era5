from app.zpt.handler.create_zpt import lambda_handler

if __name__ == "__main__":
    scan = lambda_handler(
        {"start_date": "2022-09-05T05:15Z", "end_date": "2022-09-05T07:32"}, {}
    )
