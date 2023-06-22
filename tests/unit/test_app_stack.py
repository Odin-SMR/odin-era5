import aws_cdk as core
import aws_cdk.assertions as assertions

from app.app_stack import Era5Stack


def test_lambda_created():
    app = core.App()
    stack = Era5Stack(app, "app")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::Lambda::Function", {"Timeout": 60})
