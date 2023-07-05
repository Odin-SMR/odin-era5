## Manage python dependencies:
##
## make help   -- Display this message
## make all    -- Recompute the .txt requirements files, keeping the
##                pinned package versions.  Use this after adding or
##                removing packages from the .in files.
## make update -- Recompute the .txt requirements files files from
##                scratch, updating all packages unless pinned in the
##                .in files.

help:
	@sed -rn 's/^## ?//;T;p' $(MAKEFILE_LIST)

PIP_COMPILE := pip-compile -q --no-header --resolver=backtracking
MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
CURRENT_DIR := $(patsubst %/,%,$(dir $(MKFILE_PATH)))

SOURCES := $(shell find . -name '*.in' -not -path '*/cdk.out/*')
CONSTRAINT_FILE := $(CURRENT_DIR)/constraints.txt
constraints.txt: $(SOURCES)
	CONSTRAINTS=/dev/null $(PIP_COMPILE) --strip-extras -o $@ $^

%.txt: %.in constraints.txt
	CONSTRAINTS=$(CONSTRAINT_FILE) $(PIP_COMPILE) --no-annotate -o $@ $<

all: constraints.txt $(addsuffix .txt, $(basename $(SOURCES)))

clean:
	rm -rf constraints.txt $(addsuffix .txt, $(basename $(SOURCES)))

update: clean all

.PHONY: help all clean update