from datetime import datetime, date, timedelta
import json
import random
import string
from typing import Any

import boto3


BUCKET = "odin-era5"


def create_short_hash():
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(8))


def find_arn():
    client = boto3.client("stepfunctions")
    results = client.list_state_machines()
    state_machine = next(
        (sm for sm in results["stateMachines"] if sm["name"] == "Era5StateMachine"),
        None,
    )
    return state_machine["stateMachineArn"] if state_machine else "None"


def lambda_handler(event: dict[str, Any], context: dict[str, Any] | None):
    event_date: datetime = datetime.strptime(
        event.get("date", (date.today() - timedelta(days=6)).isoformat()), "%Y-%m-%d"
    )

    state_machine_arn = find_arn()

    sfn = boto3.client("stepfunctions")

    zarr_store = (
        f"s3://{BUCKET}/{event_date.year:02}/{event_date.month:02}/"
        f"ea_pl_{event_date.year}-{event_date.month:02}-{event_date.day:02}.zarr"
    )

    sfn.start_execution(
        stateMachineArn=state_machine_arn,
        input=json.dumps(
            {
                "date": event_date.date().isoformat(),
                "zarr_store": zarr_store,
                "time_list": ["00", "06", "12", "18"],
            }
        ),
        name=f"{event_date.date()}-{create_short_hash()}",
    )

    return {"statusCode": 200}
