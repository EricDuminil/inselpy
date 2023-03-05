help:     ## Show this help.
	@egrep -h '(\s##\s|^##\s)' $(MAKEFILE_LIST) | egrep -v '^--' | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[32m  %-35s\033[0m %s\n", $$1, $$2}'

tests: ## Run tests
	python3 -m unittest discover src/

pytests: ## Run detailed tests
	pytest -v

coverage: ## Check tests coverage
	ruby misc/check_block_coverage.rb

clean: ## Remove pyc and pycache
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	rm dist/*.tar.gz
	rm dist/*.whl

build_package: clean pytests ## Build PyPI package
	python3 -m pip install --upgrade build
	python3 -m build

_check_upload:
	@echo -n "Are you sure you want to upload the package to PyPI? [y/N] " && read ans && [ $${ans:-N} = y ]

upload_package: _check_upload build_package ## Upload PyPI package
	python3 -m twine upload --repository testpypi dist/* --verbose
