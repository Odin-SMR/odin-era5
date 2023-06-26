#!/bin/env python3
import datetime
import boto3
import json


def find_arn() -> str:
    client = boto3.client("stepfunctions")
    results = client.list_state_machines()
    print(results)
    for i in results["stateMachines"]:
        if i["name"] == "Era5StateMachine":
            print("test: ", i["stateMachineArn"])
            return i["stateMachineArn"]
    return "None"


if __name__ == "__main__":
    state_machine_arn = find_arn()

    sfn = boto3.client("stepfunctions")
    state_machines = sfn.list_executions(
        stateMachineArn=state_machine_arn,  # statusFilter="RUNNING"
    )
    while True:
        for i in state_machines["executions"]:
            print(i["name"])
            sfn.delete_state_machine(stateMachineArn=i["executionArn"])
        if state_machines.get("nextToken"):
            state_machines = sfn.list_executions(
                stateMachineArn=state_machine_arn,
                nextToken=state_machines["nextToken"],
                statusFilter="RUNNING",
            )
        else:
            break
