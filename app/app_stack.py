from aws_cdk import Duration, Stack
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ssm
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk.aws_stepfunctions import Condition
from constructs import Construct

from .lambdas.process_file import ProcessFile
from .tasks.check_file import CheckFileTask
from .tasks.check_result import CheckResultTask
from .tasks.download_era5 import DownloadERA5Task
from .tasks.send_request import SendRequestTask

BUCKET = "odin-era5"


class Era5Stack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        era5_bucket = s3.Bucket.from_bucket_name(self, "Era5Bucket", BUCKET)
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

        process_file = ProcessFile(self, cds_key.string_value, cds_url.string_value)
        rule = events.Rule(
            self,
            "Era5ScheduleRule",
            schedule=events.Schedule.cron(minute="00", hour="15"),
        )
        rule.add_target(targets.LambdaFunction(process_file))  # type: ignore

        # Taskdefinitions
        send_request_task = SendRequestTask(
            self, cds_key.string_value, cds_url.string_value
        )
        check_result_task = CheckResultTask(
            self, cds_key.string_value, cds_url.string_value
        )
        check_file_task = CheckFileTask(
            self, era5_bucket, cds_key.string_value, cds_url.string_value
        )
        download_era5_task = DownloadERA5Task(
            self, era5_bucket, cds_key.string_value, cds_url.string_value
        )

        # Logic flow & State
        check_file_success_state = sfn.Succeed(
            self, "fileSuccess", comment="File already exist"
        )
        file_ok: sfn.Choice = sfn.Choice(
            self,
            "checkFileExist",
        )
        check_file_task.next(file_ok)
        file_ok.when(
            Condition.number_equals("$.CheckFile.Payload.status_code", 200),
            check_file_success_state,
        )
        file_ok.when(
            sfn.Condition.number_equals("$.CheckFile.Payload.status_code", 404),
            send_request_task,
        )
        file_ok.otherwise(check_file_success_state)

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
        check_result_choice_state.when(
            sfn.Condition.string_equals("$.CheckResult.Payload.state", "accepted"),
            wait_state,
        )
        download_file_fail_state = sfn.Fail(
            self, "downloadFileFail", comment="Something went wrong while downloading!"
        )
        check_result_choice_state.otherwise(download_file_fail_state)

        download_file_succes_state = sfn.Succeed(
            self, "downloadSuccess", comment="Download success"
        )

        download_era5_ok_state: sfn.Choice = sfn.Choice(self, "downloadOKState")
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
