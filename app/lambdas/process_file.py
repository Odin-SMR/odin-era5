from aws_cdk.aws_lambda import Function, Code, Runtime
from aws_cdk import aws_iam
from constructs import Construct


class ProcessFile(Function):
    def __init__(self, scope: Construct, cds_key: str, cds_url: str):
        super().__init__(
            scope,
            self.__class__.__name__,
            runtime=Runtime.PYTHON_3_10,
            code=Code.from_asset("app/process"),
            handler="handler.process_file.lambda_handler",
            environment={
                "CDSAPI_KEY": cds_key,
                "CDSAPI_URL": cds_url,
            },
            function_name=self.__class__.__name__,
        )
        self.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=[
                    "states:ListStateMachines",
                    "states:StartExecution",
                ],
                resources=["*"],
            ),
        )
