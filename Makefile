MAKEFLAGS += --warn-undefined-variables

.POSIX:
SHELL := /bin/sh

.DEFAULT_GOAL := menu

archive := $(CURDIR)/dist/gcsutils-*
pypi_repository := testpypi
pypi_repository_username := $(PYPI_REPOSITORY_USERNAME)
pypi_repository_password ?= $(PYPI_REPOSITORY_PASSWORD)
prerelease ?= b$(shell git rev-list --count HEAD ^develop)

%:
	@:

.PHONY: menu
menu:
	@ grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-35s\033[0m %s\n", $$1, $$2}'

.PHONY: test
test:  $(shell find $(CURDIR)/gcsutils -type f) ## Run the unit and integration tests
	@ pipenv run pytest -c tests/pytest.ini

.PHONY: build
build:  $(archive) ## Build the Python archive
	@ :

$(archive): setup.py $(shell find gcsutils -type f)
	@ pipenv run python setup.py egg_info --tag-build=$(prerelease) sdist bdist_wheel

.PHONY: publish
publish:  $(archive) ## Publish the Python archive to the PyPi repository
	@ pipenv run python -m twine upload \
		--repository $(pypi_repository) \
		--username $(pypi_repository_username) \
		--password $(pypi_repository_password) \
		--disable-progress-bar \
		$(archive)
