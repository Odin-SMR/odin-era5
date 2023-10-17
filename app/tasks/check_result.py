from aws_cdk import Duration
from aws_cdk.aws_lambda import Code, Function, Runtime
from aws_cdk.aws_stepfunctions import TaskInput
from aws_cdk.aws_stepfunctions_tasks import LambdaInvoke
from constructs import Construct


class CheckResult(Function):
    def __init__(self, scope: Construct, cds_key: str, cds_url: str):
        super().__init__(
            scope,
            "checkResult",
            runtime=Runtime.PYTHON_3_10,
            code=Code.from_asset(
                "app/checkresult",
                bundling={
                    "image": Runtime.PYTHON_3_10.bundling_image,
                    "command": [
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                },
            ),
            handler="handler.check_result.lambda_handler",
            environment={
                "CDSAPI_KEY": cds_key,
                "CDSAPI_URL": cds_url,
            },
            timeout=Duration.seconds(10),
        )


class CheckResultTask(LambdaInvoke):
    def __init__(self, scope: Construct, cds_key: str, cds_url: str):
        self.check_result = CheckResult(scope, cds_key, cds_url)
        super().__init__(
            scope,
            "checkResultTask",
            lambda_function=self.check_result,  # type: ignore
            payload=TaskInput.from_json_path_at("$.SendRequest.Payload"),
            result_path="$.CheckResult",
        )
        self.add_retry(
            errors=["States.ALL"],
            max_attempts=3,
            backoff_rate=2,
            interval=Duration.minutes(3),
        )
