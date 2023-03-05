help:     ## Show this help.
	@egrep -h '(\s##\s|^##\s)' $(MAKEFILE_LIST) | egrep -v '^--' | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[32m  %-35s\033[0m %s\n", $$1, $$2}'

tests: ## Run tests
	python -m unittest discover src/

pytests: ## Run detailed tests
	pytest -v

coverage: ## Check tests coverage
	ruby misc/check_block_coverage.rb

clean: ## Remove pyc and pycache
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

#package, doc, upload
