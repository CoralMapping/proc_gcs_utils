MAKEFLAGS += --warn-undefined-variables

.POSIX:
SHELL := /bin/sh

.DEFAULT_GOAL := menu

%:
	@:

.PHONY: menu
menu:
	@ grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-35s\033[0m %s\n", $$1, $$2}'

.PHONY: test
test:  $(shell find $(CURDIR)/src -type f) ## Run the unit and integration tests
	pipenv run pytest -c proc_gcs_utils/tests/pytest.ini
