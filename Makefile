APP_UID := $(shell id -u)

setup_mounts:
	@mkdir -p mounts/db
	@mkdir -p mounts/mysql_db
	@mkdir -p mounts/logs
	@mkdir -p mounts/modules
	@mkdir -p Access/access_modules
	@chown $(APP_UID) mounts/db
	@chown $(APP_UID) mounts/mysql_db
	@chown $(APP_UID) mounts/logs
	@chown $(APP_UID) mounts/modules
	@chown $(APP_UID) Access/access_modules

## make all : Run service, test and linter
.PHONY: all
all: build test lint

## make dev : Build and start docker containers - (web/test/db)
.PHONY: dev
dev: export APPUID = $(APP_UID)
dev: setup_mounts
	@docker-compose up --build -d web celery

## make build : Build and start docker containers - (web and db)
.PHONY: build
build: export APPUID = $(APP_UID)
build:
	@docker-compose up --build -d web

## make build_only : Only build the web container
.PHONY: build_only
build_only: export APPUID = $(APP_UID)
build_only:
	@docker-compose build web

.PHONY: down
down: export APPUID = $(APP_UID)
down:
	@docker-compose -f docker-compose.yml down

## View docker logs for containers started in `make dev`
.PHONY: logs
logs:
	@docker-compose logs -ft

ensure_web_container_for_test:
	@if [ $$(docker ps -a -f name=dev | wc -l) -eq 2 ]; then \
		docker exec dev python -m pytest --version; \
	else \
		echo "No containers running.. Starting Django runserver:"; \
		make build; \
	fi

## Run tests with coverage
.PHONY: test
test: export APPUID = $(APP_UID)
test: setup_mounts ensure_web_container_for_test
	@if [ "$(TESTS)" = "" ]; then \
		echo "No arguments passed to make test. Running all tests.."; \
		docker exec dev python -m pytest -v --cov --disable-warnings; \
		echo "Tests finished."; \
	else \
		echo "Running tests with filter $(TESTS)"; \
		docker exec dev python -m pytest -v --cov --disable-warnings -k '$(TESTS)'; \
	fi

## Lint code using pylama skipping files in env (if pyenv created)
.PHONY: lint
lint: export APPUID = $(APP_UID)
lint: setup_mounts ensure_web_container_for_test
	@docker exec dev python -m pylama --version
	@docker exec dev python -m pylama Access/accessrequest_helper.py scripts
	@if [ "$$?" -ne 0 ]; then \
		echo "Linter checks failed"; \
		exit 1; \
	else \
	  echo "Linter checks passed"; \
	fi

.PHONY: schema_validate
schema_validate: export APPUID = $(APP_UID)
schema_validate: setup_mounts ensure_web_container_for_test
	@echo "Validating Schema"
	@docker exec dev python scripts/validator.py
	@if [ "$$?" -ne 0 ]; then \
		echo "Schema validation failed"; \
		exit 1; \
	else \
	  echo "Schema validation passed"; \
	fi

run_semgrep:
	$(shell semgrep --error --config "p/cwe-top-25" --config "p/r2c-security-audit")
