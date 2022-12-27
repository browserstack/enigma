## Install dependencies
.PHONY: setup
setup:
	pip install -r requirements.txt --no-cache-dir

## Build and start docker
.PHONY: docker
docker:
	docker-compose build && docker-compose up -d

## View docker logs
.PHONY: logs
logs:
	docker-compose logs -ft

## Run tests with coverage
.PHONY: test
test: setup
	python -m pytest --version
	python -m pytest -v --cov --disable-warnings

## Lint code using pylint
.PHONY: lint
lint:
	pip install pylint
	python -m pylint --version
	find . -type f -not -path "./env/*" -name "*.py" | xargs pylint --output-format=json:enigma-linter.json,colorized