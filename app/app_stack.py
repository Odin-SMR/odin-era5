from aws_cdk import Duration, Stack
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ssm
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks
from constructs import Construct

BUCKET = "odin-era5"


class Era5Stack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        era5_bucket = s3.Bucket.from_bucket_name(self, "Era5Bucket", BUCKET)
        cds_key = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "cdsKey",
            string_parameter_name="/odin/cdsapi",
        )

        download_era5 = _lambda.Function(
            self,
            "downloadERA5",
            timeout=Duration.seconds(900),
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset(
                "app/download",
                bundling={
                    "image": _lambda.Runtime.PYTHON_3_10.bundling_image,
                    "command": [
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                },
            ),
            handler="handler.download_era5.lambda_handler",
            environment={
                "CDSAPI_KEY": cds_key.string_value,
                "CDSAPI_URL": "https://cds.climate.copernicus.eu/api/v2",
            },
        )

        check_file = _lambda.Function(
            self,
            "checkFile",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("app/checkfile"),
            handler="handler.check_file.lambda_handler",
        )
        process_file = _lambda.Function(
            self,
            "processFile",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("app/process"),
            handler="handler.process_file.lambda_handler",
        )

        # SFN
        check_file_fail_state = sfn.Fail(
            self, "checkFileFail", comment="Something went wrong checking if file exists!"
        )
        download_file_fail_state = sfn.Fail(
            self, "downloadFileFail", comment="Something went wrong while downloading!"
        )
        check_file_success_state = sfn.Succeed(
            self, "fileSuccess", comment="File exist"
        )
        download_file_succes_state = sfn.Succeed(
            self, "downloadSuccess", comment="Download success"
        )
        check_file_task = tasks.LambdaInvoke(
            self,
            "Era5StackCheckFile",
            lambda_function=check_file,
            payload=sfn.TaskInput.from_object(
                {
                    "date": sfn.JsonPath.string_at("$.date"),
                    "hour": sfn.JsonPath.string_at("$.hour"),
                }
            ),
            result_path="$.CheckFile",
            retry_on_service_exceptions=True,
        )

        download_era5_task = tasks.LambdaInvoke(
            self,
            "era5StackDownloadFile",
            lambda_function=download_era5,
            result_path="$.DownloadERA5",
            retry_on_service_exceptions=True,
            payload=sfn.TaskInput.from_object(
                {
                    "date": sfn.JsonPath.string_at("$.date"),
                    "hour": sfn.JsonPath.string_at("$.hour"),
                }
            ),
        )

        download_era5_task.add_retry(
            errors=["HTTPError", "Exception"],
            max_attempts=3,
            backoff_rate=5,
            interval=Duration.hours(1),
        )
        download_era5_task.add_catch(
            download_file_fail_state,
            errors=["HTTPError", "Exception"],
            result_path="$.DownloadEra5",
        )

        check_file_task.add_catch(
            download_era5_task,
            errors=["ClientError"],
            result_path="$.CheckFile",
        )
        check_file_task.add_catch(
            check_file_fail_state,
            errors=["ValueError"],
            result_path="$.CheckFile",
        )

        check_file_task.next(check_file_success_state)
        download_era5_task.next(download_file_succes_state)

        sfn.StateMachine(
            self,
            "Era5StateMachine",
            definition=check_file_task,
            state_machine_name="Era5StateMachine",
        )

        # Define the CloudWatch event rule
        rule = events.Rule(
            self,
            "Era5ScheduleRule",
            schedule=events.Schedule.cron(minute="00", hour="15"),
        )

        # Add the Lambda function as a target of the rule
        rule.add_target(targets.LambdaFunction(process_file))
        era5_bucket.grant_read_write(download_era5)
        era5_bucket.grant_read(check_file)
