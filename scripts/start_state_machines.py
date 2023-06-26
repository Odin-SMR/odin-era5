#!/bin/env python3
import datetime
import json

import boto3


def find_arn() -> str:
    client = boto3.client("stepfunctions")
    results = client.list_state_machines()
    for i in results["stateMachines"]:
        if i["name"] == "Era5StateMachine":
            return i["stateMachineArn"]
    return "None"


if __name__ == "__main__":
    current_date = datetime.date(2023, 1, 1)
    end_date = datetime.date.today() - datetime.timedelta(days=4)

    state_machine_arn = find_arn()

    # Create four different times
    hours = [
        "00",
        "06",
        "12",
        "18",
    ]

    sfn = boto3.client("stepfunctions")
    while current_date <= end_date:
        for hour in hours:
            input_data = json.dumps({"date": current_date.isoformat(), "hour": hour})

            response = sfn.start_execution(
                stateMachineArn=state_machine_arn,
                input=input_data,
                name=f"{current_date}T{hour}-V3",
            )
        current_date = current_date + datetime.timedelta(days=1)
