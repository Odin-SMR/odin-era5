from aws_cdk import Duration, Stack
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks
from constructs import Construct

BUCKET = "odin-era5"


class Era5Stack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        era5_bucket = s3.Bucket.from_bucket_name(self, "Era5Bucket", BUCKET)

        download_era5 = _lambda.Function(
            self,
            "downloadERA5",
            timeout=Duration.minutes(15),
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
        )
        statement = aws_iam.PolicyStatement(
            actions=["ssm:GetParametersByPath"],
            resources=["arn:aws:ssm:eu-north-1:*:/odin/cdsapi/*"]
        )
        download_era5.add_to_role_policy(statement)        

        check_file = _lambda.Function(
            self,
            "checkFile",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("app/checkfile"),
            handler="handler.check_file.lambda_handler",
            timeout=Duration.seconds(10),
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
            self,
            "checkFileFail",
            comment="Something went wrong checking if file exists!",
        )
        check_file_success_state = sfn.Succeed(
            self, "fileSuccess", comment="File exist"
        )
        download_file_fail_state = sfn.Fail(
            self, "downloadFileFail", comment="Something went wrong while downloading!"
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
            errors=["CDSAPITooManyRequests"],
            max_attempts=3,
            backoff_rate=2,
            interval=Duration.minutes(15),
        )
        download_era5_task.add_retry(
            errors=["CDSAPINotAvailableYet"],
            max_attempts=3,
            backoff_rate=1,
            interval=Duration.days(1),
        )
        download_era5_task.add_retry(
            errors=["States.ALL"],
            max_attempts=3,
            backoff_rate=2,
            interval=Duration.minutes(30),
        )
        checkfile_exists_state = sfn.Choice(
            self,
            "checkFileExist",
        )
        check_file_task.next(checkfile_exists_state)
        checkfile_exists_state.when(
            sfn.Condition.number_equals("$.CheckFile.Payload.StatusCode", 200),
            check_file_success_state,
        )
        checkfile_exists_state.when(
            sfn.Condition.number_equals("$.CheckFile.Payload.StatusCode", 404),
            download_era5_task,
        )
        checkfile_exists_state.otherwise(check_file_fail_state)
        download_era5_ok_state = sfn.Choice(self, "downloadOKState")
        download_era5_task.next(download_era5_ok_state)
        download_era5_ok_state.when(
            sfn.Condition.string_equals("$.DownloadERA5.Payload.state", "completed"),
            download_file_succes_state,
        )
        download_era5_ok_state.otherwise(download_file_fail_state)

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
