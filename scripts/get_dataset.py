#!/bin/env python3
import datetime
import boto3
import json


def find_arn():
    client = boto3.client("stepfunctions")
    results = client.list_state_machines()
    print(results)
    for i in results["stateMachines"]:
        if i["name"] == "Era5StateMachine":
            print("test: " , i["stateMachineArn"])
            return i["stateMachineArn"]
    return None


if __name__ == "__main__":
    current_date = datetime.date(2022, 9, 25)
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
            )
        current_date = current_date + datetime.timedelta(days=1)
