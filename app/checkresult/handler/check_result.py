#!/usr/bin/env python3.8

import cdsapi


def lambda_handler(event, context):
    client = cdsapi.Client(progress=False, wait_until_complete=False)
    result = client.robust(client.session.post)
    result.raise_for_status()
    return result.json()
