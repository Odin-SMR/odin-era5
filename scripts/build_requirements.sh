#!/bin/bash
pushd $(git rev-parse --show-toplevel) > /dev/null
pip install -q -U pip-tools
# build cdk runtime requirements
pip-compile -q -U \
    requirements.in \
    --resolver=backtracking
# build lambda handler runtime requirements
pip-compile -q -U \
    requirements-stack.in \
    -o app/download/requirements.txt \
    --resolver=backtracking
# build zpt requirements
pip-compile -q -U \
    requirements-zpt.in \
    -o app/zpt/requirements.txt \
    --resolver=backtracking
# build development requirements
pip-compile -q -U \
    requirements-dev.in \
    requirements.txt \
    app/download/requirements.txt \
    app/zpt/requirements.txt \
    -o requirements-dev.txt \
    --resolver=backtracking
popd > /dev/null
