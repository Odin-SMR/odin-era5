from aws_cdk import Duration
from aws_cdk.aws_lambda import Architecture, DockerImageCode, DockerImageFunction
from aws_cdk.aws_s3 import IBucket
from aws_cdk.aws_stepfunctions import JsonPath, TaskInput
from aws_cdk.aws_stepfunctions_tasks import LambdaInvoke
from constructs import Construct


class DownloadERA5(DockerImageFunction):
    def __init__(self, scope: Construct, cds_key: str, cds_url: str):
        super().__init__(
            scope,
            self.__class__.__name__,
            timeout=Duration.minutes(15),
            code=DockerImageCode.from_image_asset(
                "./app/download",
            ),
            memory_size=4096,
            architecture=Architecture.X86_64,
            environment={"CDSAPI_KEY": cds_key, "CDSAPI_URL": cds_url},
            function_name=self.__class__.__name__,
        )


class DownloadERA5Task(LambdaInvoke):
    def __init__(self, scope: Construct, bucket: IBucket, cds_key: str, cds_url: str):
        self.download_era5 = DownloadERA5(scope, cds_key, cds_url)
        bucket.grant_read_write(self.download_era5)
        super().__init__(
            scope,
            self.__class__.__name__,
            lambda_function=self.download_era5,  # type: ignore
            result_path="$.DownloadERA5",
            retry_on_service_exceptions=True,
            payload=TaskInput.from_object(
                {
                    "zarr_store": JsonPath.string_at("$.zarr_store"),
                    "reply": JsonPath.object_at("$.CheckResult.Payload"),
                }
            ),
        )
