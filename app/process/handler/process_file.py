from datetime import datetime, date, time, timedelta
import json
from typing import List

import boto3

import hashlib

BUCKET = "odin-era5"


def create_short_hash():
    input_data = str(time()).encode("utf-8")
    hash_object = hashlib.sha256(input_data)
    short_hash = hash_object.hexdigest()[:8]
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

    hours = [
        0,
        6,
        12,
        18,
    ]

    sfn = boto3.client("stepfunctions")

    date_list = [
        datetime.combine(event_date, time(hour=hour)).isoformat() for hour in hours
    ]

    zarr_store = (
        f"s3://{BUCKET}/{event_date.year:02}/{event_date.month:02}/"
        f"ea_pl_{event_date.year}-{event_date.month:02}-{event_date.day:02}.zarr"
    )

    sfn.start_execution(
        stateMachineArn=state_machine_arn,
        input=json.dumps({"date_list": date_list, "zarr_store": zarr_store}),
        name=f"{event_date}-{hashlib.md5(str(datetime.now()).encode('utf-8')).hexdigest()}",
    )

    return {"statusCode": 200}
