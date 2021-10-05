# ML Bundle Engine
The ML bundle engine is an event driven series of processes & queues. 
The engine intakes a Kafka message from the bundle request topic, makes a prediction with an ML model, runs an optimizer and outputs to a Kafka topic.

![Engine Architecture](./docs/assets/ml-bundling-architecture.png)

## Maintainer(s)
 - @Jason
 - @AdamH

## Requirements
Python 3.8+

## Installation
Install the required packages in your local environment (ideally virtualenv, conda, etc.).
```bash
pip install -r requirements
``` 

## Setup
There is a Makefile provided to _make_ your life easier. Simply run ```make setup```

## Local Engine testing

Launch the engine locally via `docker compose up run-engine -d`

- [ ] TODO: Add script to pub a Kafka message to dummy topic (simulate intake)
   
- [ ] TODO: Add script to sub to a Kafka message to dummy topic (simulate outbound)

## Engine Project Structure

 - [ ] TODO: Run ```tree`` and elaborate after component diag/dir finalized

### Testing

#### Unit testing

All unit tests are in the tests directory. They can be run locally with `make test` or in docker using `docker compose up unit-tests`.


### Environments

Set the environment variable `APP_ENV` to one of the following names (all lower case).

| Name        | Description       |
|-------------|-------------------|
| development | Local development |
| testing     | Unit testing      |
| staging     | Pre-prod          |
| production  | Production        |

### Updating an Existing Repo

- Update `.drone.yml` based on template
- Add `Makefile` based on template
- Run `poetry init` to create `pyproject.toml`, or copy existing file from the template and change the project and version name
- Add needed dependencies to `pyproject.toml` under `[tool.poetry.dependencies]`
	- run pipreqs --print to see the deps needed, copy just the names
	- for the dep names copied, cross reference an existing `requirements.txt` file to get the correct versions
- copy everything from the template from `[tool.poetry.dev-dependencies]` down and add it into the pyproject toml file
- copy `setup.cfg` file from the template
- remove anything from `[tool.poetry.dependencies]` that exists already in `[tool.poetry.dependencies]`
- run `poetry lock` to create the lock file
- the `pyproject.toml` should use semantic versioning (semvar) for easy upgrading, e.g. `"pytest" = "^6.2.1"`
- run `make setup`
- If any of the dependencies fail on `poetry install`, add the needed dependency in the `pyproject.toml` file, remove the existing `poetry.lock` file and run `make setup.uninstall` then `make setup` again
- run `make format` to take care of any linting
- run `make deploy.requirements` to create/update `requirements.txt` and `requirements-dev.txt`
- push the PR!
