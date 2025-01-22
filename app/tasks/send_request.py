from aws_cdk import Duration
from aws_cdk.aws_lambda import Code, Function, Runtime
from aws_cdk.aws_stepfunctions import JsonPath, TaskInput
from aws_cdk.aws_stepfunctions_tasks import LambdaInvoke
from constructs import Construct

from app.sendrequest.handler.send_request import SendRequestEvent


class SendRequest(Function):
    def __init__(self, scope: Construct, cds_key: str, cds_url: str) -> None:
        super().__init__(
            scope,
            self.__class__.__name__,
            runtime=Runtime.PYTHON_3_12,
            code=Code.from_asset(
                "app/sendrequest",
                bundling={
                    "image": Runtime.PYTHON_3_12.bundling_image,
                    "command": [
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                },
            ),
            handler="handler.send_request.lambda_handler",
            environment={
                "CDSAPI_KEY": cds_key,
                "CDSAPI_URL": cds_url,
            },
            timeout=Duration.seconds(30),
            function_name=self.__class__.__name__,
        )


class SendRequestTask(LambdaInvoke):
    def __init__(self, scope: Construct, cds_key: str, cds_url: str):
        self.send_request = SendRequest(scope, cds_key, cds_url)
        super().__init__(
            scope,
            self.__class__.__name__,
            lambda_function=self.send_request,  # type: ignore
            payload=TaskInput.from_object(
                SendRequestEvent(
                    date=JsonPath.string_at("$.date"),
                    time_list=JsonPath.list_at("$.time_list"),
                )
            ),
            result_path="$.SendRequest",
        )
        self.add_retry(
            errors=["CDSAPITooManyRequests"],
            max_attempts=3,
            backoff_rate=2,
            interval=Duration.minutes(15),
        )
        self.add_retry(
            errors=["CDSAPINotAvailableYet"],
            max_attempts=3,
            backoff_rate=1,
            interval=Duration.days(1),
        )
        self.add_retry(
            errors=["States.ALL"],
            max_attempts=3,
            backoff_rate=2,
            interval=Duration.minutes(30),
        )
