import aws_cdk as core
import aws_cdk.assertions as assertions

from odin_test.odin_test_stack import OdinTestStack

# example tests. To run these tests, uncomment this file along with the example
# resource in odin_test/odin_test_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = OdinTestStack(app, "odin-test")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
