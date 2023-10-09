from datetime import datetime, date, time, timedelta
import json
from typing import List

import boto3

import hashlib

BUCKET = "odin-era5"


def create_short_hash():
    input_data = str(time()).encode("utf-8")
    hash_object = hashlib.sha256(input_data)
    short_hash = hash_object.hexdigest()[-20:]
    return short_hash


def find_arn():
    client = boto3.client("stepfunctions")
    results = client.list_state_machines()
    state_machine = next(
        (sm for sm in results["stateMachines"] if sm["name"] == "Era5StateMachine"),
        None,
    )
    return state_machine["stateMachineArn"] if state_machine else "None"


def lambda_handler(event, context):
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
