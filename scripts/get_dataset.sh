#!/bin/bash
export AWS_PROFILE="${AWS_PROFILE:-odin-cdk}"
pushd "$(git rev-parse --show-toplevel)" > /dev/null
python -m app.handler.handler_modules.download
popd > /dev/null
