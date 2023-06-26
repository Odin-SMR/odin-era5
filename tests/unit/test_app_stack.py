import aws_cdk
import aws_cdk.assertions as assertions

from app.app_stack import Era5Stack


def test_lambda_created():
    app = aws_cdk.App()
    stack = Era5Stack(app, "GetEra5Data")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::Lambda::Function", {"Timeout": 900})
