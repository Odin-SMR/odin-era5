import datetime
import json

import boto3


def find_arn():
    client = boto3.client("stepfunctions")
    results = client.list_state_machines()
    for i in results["stateMachines"]:
        if i["name"] == "Era5StateMachine":
            return i["stateMachineArn"]
    return "None"


def lambda_handler(event, context):
    # Calculate the date of five days ago
    current_date = datetime.date.today()
    five_days_ago = current_date - datetime.timedelta(days=5)

    state_machine_arn = find_arn()

    # Create four different times
    hours = [
        "00",
        "06",
        "12",
        "18",
    ]

    sfn = boto3.client("stepfunctions")

    for hour in hours:
        input_data = {"date": five_days_ago.isoformat(), "hour": hour}

        response = sfn.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps(input_data),
        )

    return {
        "statusCode": 200,
    }
