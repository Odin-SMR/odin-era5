#!/usr/bin/env python3

import aws_cdk as cdk

from app.app_stack import Era5Stack

app = cdk.App()
Era5Stack(app, "GetEra5Data")

app.synth()
