from collections import namedtuple
from typing import List

import boto3

ssm = boto3.client("ssm", region_name="eu-north-1")


def get_parameters(parameters: List[str]):
    keys: List[str] = []
    values: List[str] = []
    for param in parameters:
        keys.append(param.split("/")[-1])
        value: str = ssm.get_parameter(Name=param)["Parameter"]["Value"]
        values.append(value)
    SSMParameters = namedtuple("SSMParameters", keys)  # type: ignore
    return SSMParameters(*values)
