from datetime import datetime, date, time, timedelta
import json
from typing import List

import boto3

import hashlib


def create_short_hash():
    input_data = str(time()).encode("utf-8")
    hash_object = hashlib.sha256(input_data)
    short_hash = hash_object.hexdigest()[:8]
    return short_hash


def find_arn():
    client = boto3.client("stepfunctions")
    results = client.list_state_machines()
    for i in results["stateMachines"]:
        if i["name"] == "Era5StateMachine":
            return i["stateMachineArn"]
    return "None"


def lambda_handler(event, context):
    current_date = date.today()
    six_days_ago = current_date - timedelta(days=6)
    event_date = event.get("date", six_days_ago.isoformat())

    state_machine_arn = find_arn()

    hours = [
        0,
        6,
        12,
        18,
    ]

    sfn = boto3.client("stepfunctions")

    date_list: List[str] = []

    for hour in hours:
        datetime_string = datetime.combine(event_date, time(hour=hour)).isoformat()
        date_list.append(datetime_string)

    sfn.start_execution(
        stateMachineArn=state_machine_arn,
        input=json.dumps(date_list),
        name=f"{event_date}-{create_short_hash()}",
    )

    return {
        "statusCode": 200,
    }
