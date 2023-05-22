SOURCE_OBJECTS=example volley tests
INTRO_COMPOSE=example/intro/docker-compose.yml


format.black:
	poetry run black ${SOURCE_OBJECTS}
format.isort:
	poetry run isort --atomic ${SOURCE_OBJECTS}
format: format.black format.isort

intro.start:
	docker compose -f ${INTRO_COMPOSE} up -d kafka redis && sleep 10
	docker compose -f ${INTRO_COMPOSE} up single_message
	docker compose -f ${INTRO_COMPOSE} up app_0 app_1
intro.stop:
	docker compose -f ${INTRO_COMPOSE} down

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

setup: setup.sysdeps setup.python setup.project
setup.project:
	poetry install -E all
setup.python:
	@echo "Active Python version: $$(python --version)"
	@echo "Base Interpreter path: $$(python -c 'import sys; print(sys.executable)')"
	@export _python_version=$$(cat .tool-versions | grep -i python | cut -d' ' -f2) \
      && test "$$(python --version | cut -d' ' -f2)" = "$$_python_version" \
      || (echo "Please activate python version: $$_python_version" && exit 1)
	@poetry env use $$(python -c "import sys; print(sys.executable)")
	@echo "Active interpreter path: $$(poetry env info --path)/bin/python"
setup.sysdeps:
	@-asdf plugin-add python; asdf install python
	@asdf plugin update --all \
      && for p in $$(cut -d" " -f1 .tool-versions | sort | tr '\n' ' '); do \
           asdf plugin add $$p || true; \
         done \
      && asdf install || echo "WARNING: Failed to install sysdeps. Environment may disagree with .tool-versions"

test.clean:
	-docker compose down
	-docker images -a | grep ${PROJECT} | awk '{print $3}' | xargs docker rmi
	-docker image prune -f
test.integration: run.datastores run.components
	docker-compose up --exit-code-from int-tests --build int-tests
test.unit: setup
	poetry run pytest -s \
			--ignore=tests/integration_tests \
			--cov=./ \
			--cov-report=xml:coverage.xml \
			--cov-report term

run.components:
	docker compose up --build -d input_worker middle_worker zmq-worker

run.example: run.datastores run.components run.externals
	docker compose up --build -d data_producer input_worker middle_worker data_consumer
run.externals:
	docker compose up --build -d data_producer data_consumer
run.datastores:
	docker compose up -d redis kafka zookeeper postgres
run:
	docker compose up --build -d
stop.components:
	docker compose down
stop:
	docker compose down --remove-orphans

publish:
	poetry publish
publish.docs: setup.project
	cd docs && poetry run mkdocs gh-deploy --force
