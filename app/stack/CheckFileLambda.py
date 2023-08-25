from aws_cdk import Duration
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_ecr_assets import DockerImageAsset
from constructs import Construct
from aws_cdk.aws_stepfunctions.tasks import TaskInput
from aws_cdk.aws_lambda import Function


class CheckFileFunction(Function):
    def __init__(
        self, scope: Construct, id: str, cds_key: str, cds_url: str, payload: TaskInput
    ):
        super().__init__(
            scope,
            id,
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
