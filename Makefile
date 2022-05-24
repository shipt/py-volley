PYTHON_VERSION=3.9.8
SOURCE_OBJECTS=example volley tests
INTRO_COMPOSE=example/intro/docker-compose.yml


format.black:
	poetry run black ${SOURCE_OBJECTS}
format.isort:
	poetry run isort --atomic ${SOURCE_OBJECTS}
format: format.black format.isort 

intro.start:
	docker-compose -f ${INTRO_COMPOSE} up -d kafka redis && sleep 10
	docker-compose -f ${INTRO_COMPOSE} up single_message
	docker-compose -f ${INTRO_COMPOSE} up app_0 app_1
intro.stop:
	docker-compose -f ${INTRO_COMPOSE} down

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
	poetry run pylint --rcfile pyproject.toml ${SOURCE_OBJECTS}
lints: lints.flake8 lints.format.check lints.mypy lints.pylint
lints.strict: lints.pylint lints.flake8.strict lints.mypy lints.format.check

setup: setup.python setup.sysdep.poetry setup.project
setup.uninstall: setup.python
	poetry env remove ${PYTHON_VERSION} || true
setup.ci: setup.ci.poetry setup.project
setup.ci.poetry:
	pip install poetry
setup.project:
	@poetry env use $$(python -c "import sys; print(sys.executable)")
	@echo "Active interpreter path: $$(poetry env info --path)/bin/python"
	poetry install -E all
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

test.clean:
	docker-compose down
	-docker images -a | grep ${PROJECT} | awk '{print $3}' | xargs docker rmi
	-docker image prune -f
test.integration: run.datastores run.components
	docker-compose up --exit-code-from int-tests --build int-tests
test.unit: setup
	poetry run coverage run -m pytest -s \
			--ignore=tests/integration_tests \
			--cov=./ \
			--cov-report=xml:coverage.xml \
			--cov-report term

run.components:
	docker-compose up --build -d input_worker middle_worker zmq_worker

run.example: run.datastores run.components run.externals
	docker compose up --build -d data_producer input_worker middle_worker data_consumer
run.externals:
	docker compose up --build -d data_producer data_consumer
run.datastores:
	docker-compose up -d redis kafka zookeeper postgres
run:
	docker compose up --build -d
stop.components:
	docker compose down
stop:
	docker compose down --remove-orphans

publish:
	poetry config repositories.shipt-deploy https://artifactory.shipt.com/artifactory/api/pypi/pypi-local
	poetry publish --repository shipt-deploy --build
poetry.pre.patch:
	poetry version prepatch
poetry.pre.minor:
	poetry version preminor
poetry.pre.major:
	poetry version premajor
publish.pre.patch: poetry.pre.patch publish
publish.pre.minor: poetry.pre.minor publish
publish.pre.major: poetry.pre.major publish