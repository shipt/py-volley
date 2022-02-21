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
lints.mypy:
	poetry run mypy ${SOURCE_OBJECTS}
lints.pylint:
	poetry run pylint --rcfile pyproject.toml ${SOURCE_OBJECTS}
lints: lints.flake8 lints.format.check lints.mypy lints.pylint

test:
	docker-compose up unit-tests
test.integration: run.datastores run.components
	docker-compose up --exit-code-from int-tests --build int-tests
test.unit:
	poetry run coverage run -m pytest -s \
			--ignore=tests/integration_tests \
            --cov=./ \
            --cov-report=xml:coverage.xml \
            --cov-report term

run.components:
	docker-compose up --build -d input_worker middle_worker 

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
	poetry publish --repository=shipt --build
poetry.pre.patch:
	poetry version prepatch
poetry.pre.minor:
	poetry version preminor
poetry.pre.major:
	poetry version premajor
publish.pre.patch: poetry.pre.patch publish
publish.pre.minor: poetry.pre.minor publish
publish.pre.major: poetry.pre.major publish