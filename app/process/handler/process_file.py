import datetime
import json

import boto3

import hashlib
import time


def create_short_hash():
    input_data = str(time.time()).encode("utf-8")
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
    current_date = datetime.date.today()
    six_days_ago = current_date - datetime.timedelta(days=6)
    date = event.get("date", six_days_ago.isoformat())

    state_machine_arn = find_arn()

    hours = [
        "00",
        "06",
        "12",
        "18",
    ]

    sfn = boto3.client("stepfunctions")

    for hour in hours:
        input_data = {"date": date, "hour": hour}

        sfn.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps(input_data),
            name=f"{date}T{hour}-{create_short_hash()}",
        )

    return {
        "statusCode": 200,
    }
