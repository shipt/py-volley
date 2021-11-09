PROJECT=ml_bundle_engine
PYTHON_VERSION=3.9.4

SOURCE_OBJECTS=components engine tests

# remove extra-index-urls - they break when auth is required
deploy.requirements:
	poetry export --without-hashes -f requirements.txt -o requirements.txt
	poetry export --without-hashes --dev -f requirements.txt -o requirements-dev.txt
	sed -i.bak -e '/^--extra-index-url/d' -e '/^$$/d' requirements.txt && rm requirements.txt.bak
	sed -i.bak -e '/^--extra-index-url/d' -e '/^$$/d' requirements-dev.txt && rm requirements-dev.txt.bak

deploy:
	poetry build

format.black:
	poetry run black ${SOURCE_OBJECTS}
format.isort:
	poetry run isort --atomic ${SOURCE_OBJECTS}
format: format.black format.isort 

lints.format.check:
	poetry run black --check ${SOURCE_OBJECTS}
	poetry run isort --check-only ${SOURCE_OBJECTS}
lints.flake8:
	poetry run flake8 --ignore=DAR,E203,W503 ${SOURCE_OBJECTS}
lints.flake8.strict:
	poetry run flake8 ${SOURCE_OBJECTS}
lints.mypy:
	poetry run mypy ${SOURCE_OBJECTS}
lints.pylint:
	poetry run pylint --rcfile pyproject.toml  ${SOURCE_OBJECTS}
lints: lints.flake8 lints.format.check lints.mypy 
lints.strict: lints.pylint lints.flake8.strict lints.mypy lints.format.check

notebook:
	poetry run jupyter notebook

setup: setup.python setup.sysdep.poetry setup.project
setup.uninstall: setup.python
	poetry env remove ${PYTHON_VERSION} || true
setup.ci: setup.ci.poetry setup.project
setup.ci.poetry:
	pip install poetry
setup.project:
	@poetry env use $$(python -c "import sys; print(sys.executable)")
	@echo "Active interpreter path: $$(poetry env info --path)/bin/python"
	poetry install
setup.python.activation:
	@pyenv local ${PYTHON_VERSION} >/dev/null 2>&1 || true
	@asdf local python ${PYTHON_VERSION} >/dev/null 2>&1 || true

setup.python: setup.python.activation
	@echo "Active Python version: $$(python --version)"
	@echo "Base Interpreter path: $$(python -c 'import sys; print(sys.executable)')"
	@test "$$(python --version | cut -d' ' -f2)" = "${PYTHON_VERSION}" \
        || (echo "Please activate python ${PYTHON_VERSION}" && exit 1)
setup.sysdep.poetry:
	@command -v poetry \&> /dev/null \
        || (echo "Poetry not found. \n  Installation instructions: https://python-poetry.org/docs/" \
            && exit 1)

test:
	docker-compose up unit-tests
test.clean:
	docker-compose down
	-docker images -a | grep ${PROJECT} | awk '{print $3}' | xargs docker rmi
	-docker image prune -f
test.integration: run.datastores run.components
	docker-compose exec -T features pytest tests/integration_tests/test_integration.py
	docker-compose down
test.shell:
	docker compose run unit-tests /bin/bash
test.shell.debug:
	docker compose run --entrypoint /bin/bash unit-tests
test.unit: setup
	poetry run coverage run -m pytest -s \
			--ignore=tests/integration_tests \
            --cov=./ \
            --cov-report=xml:cov.xml \
            --cov-report term

run.dummy.components:
	docker compose up -d dummy_events dummy_consumer

run.components:
	docker-compose up -d features triage optimizer fallback collector publisher

run.datastores:
	docker-compose up -d postgres redis kafka zookeeper

run:
	docker compose up --build -d

stop.components:
	docker compose down

stop:
	docker compose down --remove-orphans