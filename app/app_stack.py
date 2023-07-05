from aws_cdk import Duration, Stack
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ssm
from aws_cdk import aws_iam as iam
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks
from constructs import Construct

BUCKET = "odin-era5"


class Era5Stack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        era5_bucket = s3.Bucket.from_bucket_name(self, "Era5Bucket", BUCKET)
        role = iam.Role(self, "LambdaProcessRole", assumed_by=iam.ServicePrincipal)
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "states:ListStateMachines",
                    "states:DescribeStateMachine",
                    "states:StartExecution",
                ],
                resources=["*"],
            ),
        )
        cds_key = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "cdsKey",
            string_parameter_name="/odin/cdsapi/key2",
        )
        cds_url = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "cdsUrl",
            string_parameter_name="/odin/cdsapi/url",
        )

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
            memory_size=512,
            handler="handler.download_era5.lambda_handler",
            environment={
                "CDSAPI_KEY": cds_key.string_value,
                "CDSAPI_URL": cds_url.string_value,
            },
        )

        check_file = _lambda.Function(
            self,
            "checkFile",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("app/checkfile"),
            handler="handler.check_file.lambda_handler",
            environment={
                "CDSAPI_KEY": cds_key.string_value,
                "CDSAPI_URL": cds_url.string_value,
            },
            timeout=Duration.seconds(10),
        )
        send_request = _lambda.Function(
            self,
            "sendRequest",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset(
                "app/sendrequest",
                bundling={
                    "image": _lambda.Runtime.PYTHON_3_10.bundling_image,
                    "command": [
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                },
            ),
            handler="handler.send_request.lambda_handler",
            environment={
                "CDSAPI_KEY": cds_key.string_value,
                "CDSAPI_URL": cds_url.string_value,
            },
            timeout=Duration.seconds(10),
        )
        check_result = _lambda.Function(
            self,
            "checkResult",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset(
                "app/checkresult",
                bundling={
                    "image": _lambda.Runtime.PYTHON_3_10.bundling_image,
                    "command": [
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                },
            ),
            handler="handler.check_result.lambda_handler",
            environment={
                "CDSAPI_KEY": cds_key.string_value,
                "CDSAPI_URL": cds_url.string_value,
            },
            timeout=Duration.seconds(10),
        )
        process_file = _lambda.Function(
            self,
            "processFile",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("app/process"),
            handler="handler.process_file.lambda_handler",
            environment={
                "CDSAPI_KEY": cds_key.string_value,
                "CDSAPI_URL": cds_url.string_value,
            },
            role=role,
        )

        # SFN

        send_request_task = tasks.LambdaInvoke(
            self,
            "sendRequestTask",
            lambda_function=send_request,
            payload=sfn.TaskInput.from_object(
                {
                    "date": sfn.JsonPath.string_at("$.date"),
                    "hour": sfn.JsonPath.string_at("$.hour"),
                }
            ),
            result_path="$.SendRequest",
        )
        check_result_task = tasks.LambdaInvoke(
            self,
            "checkResultTask",
            lambda_function=check_result,
            payload=sfn.TaskInput.from_json_path_at("$.SendRequest.Payload"),
            result_path="$.CheckResult",
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
                    "reply": sfn.JsonPath.object_at("$.CheckResult.Payload"),
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

        # Logic flow & State
        check_file_fail_state = sfn.Fail(
            self,
            "checkFileFail",
            comment="Something went wrong checking if file exists!",
        )
        check_file_success_state = sfn.Succeed(
            self, "fileSuccess", comment="File exist"
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
            send_request_task,
        )
        checkfile_exists_state.otherwise(check_file_fail_state)

        wait_state = sfn.Wait(
            self, "Wait", time=sfn.WaitTime.duration(Duration.seconds(30))
        )

        send_request_task.next(wait_state)
        wait_state.next(check_result_task)

        check_result_choice_state = sfn.Choice(self, "checkResultChoiceState")
        check_result_task.next(check_result_choice_state)
        check_result_choice_state.when(
            sfn.Condition.string_equals("$.CheckResult.Payload.state", "queued"),
            wait_state,
        )
        check_result_choice_state.when(
            sfn.Condition.string_equals("$.CheckResult.Payload.state", "completed"),
            download_era5_task,
        )
        check_result_choice_state.when(
            sfn.Condition.string_equals("$.CheckResult.Payload.state", "running"),
            wait_state,
        )
        download_file_fail_state = sfn.Fail(
            self, "downloadFileFail", comment="Something went wrong while downloading!"
        )
        check_result_choice_state.otherwise(download_file_fail_state)

        download_file_succes_state = sfn.Succeed(
            self, "downloadSuccess", comment="Download success"
        )

        download_era5_ok_state = sfn.Choice(self, "downloadOKState")
        download_era5_task.next(download_era5_ok_state)
        download_era5_ok_state.when(
            sfn.Condition.number_equals("$.DownloadERA5.Payload.StatusCode", 200),
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
