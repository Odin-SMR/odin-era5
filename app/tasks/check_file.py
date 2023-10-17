from aws_cdk import Duration
from aws_cdk.aws_lambda import Code, Function, Runtime
from aws_cdk.aws_s3 import IBucket
from aws_cdk.aws_stepfunctions import JsonPath, TaskInput
from aws_cdk.aws_stepfunctions_tasks import LambdaInvoke
from constructs import Construct

from app.checkfile.handler.check_file import CheckFileEvent


class CheckFile(Function):
    def __init__(self, scope: Construct, cds_key: str, cds_url: str):
        super().__init__(
            scope,
            "CheckFile",
            runtime=Runtime.PYTHON_3_10,
            code=Code.from_asset(
                "app/checkfile",
                bundling={
                    "image": Runtime.PYTHON_3_10.bundling_image,
                    "command": [
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                },
            ),
            handler="handler.check_file.lambda_handler",
            environment={
                "CDSAPI_KEY": cds_key,
                "CDSAPI_URL": cds_url,
            },
            timeout=Duration.seconds(10),
        )


class CheckFileTask(LambdaInvoke):
    def __init__(self, scope: Construct, bucket: IBucket, cds_key: str, cds_url: str):
        self.check_file = CheckFile(scope, cds_key, cds_url)
        bucket.grant_read(self.check_file)
        super().__init__(
            scope,
            "Era5StackCheckFile",
            lambda_function=self.check_file,  # type: ignore
            payload=TaskInput.from_object(
                CheckFileEvent(zarr_store=JsonPath.string_at("$.zarr_store"))
            ),
            result_path="$.CheckFile",
            retry_on_service_exceptions=True,
        )
