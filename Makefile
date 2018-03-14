.PHONY: clean clean-test clean-pyc clean-build docs help

lint: ## check style with flake8
	pipenv run flake8 bikram tests

pipenv:
	pip install pipenv
	pipenv install --dev

test: ## run tests quickly with the default Python
	pipenv run python setup.py test

coverage: ## check code coverage quickly with the default Python
	pipenv run coverage run --source bikram setup.py test

report:
	pipenv run coverage report -m

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -f .coverage
	rm -fr htmlcov/

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/bikram.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ bikram
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

release: clean ## package and upload a release
	python setup.py sdist
	twine upload dist/*

sdist: clean ## package
	python setup.py sdist
	ls -l dist
