#!/bin/bash
pushd $(git rev-parse --show-toplevel) > /dev/null
pip install -q -U pip-tools
# build cdk runtime requirements
pip-compile -q \
    requirements.in \
    --resolver=backtracking
# build lambda handler runtime requirements
pip-compile -q \
    requirements-stack.in \
    -o app/handler/requirements.txt \
    --resolver=backtracking
# build development requirements
pip-compile -q \
    requirements-dev.in \
    requirements.txt \
    app/handler/download/requirements.txt \
    -o requirements-dev.txt \
    --resolver=backtracking
popd > /dev/null
