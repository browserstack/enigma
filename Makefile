## make all : Run service, test and linter
.PHONY: all
all: build test lint

## make dev : Build and start docker containers - (web/test/db)
.PHONY: dev
dev:
	@export DJANGO_SETTINGS_MODULE=BrowserStackAutomation.settings && python3 scripts/make_config_and_env_and_readme.py && python3 scripts/clone_access_modules.py && python3 scripts/github_test.py && python3 scripts/merge_requirements.py && python3 scripts/merge_config.py && docker-compose build && docker-compose up -d

## make build : Build and start docker containers - (web and db)
.PHONY: build
build:
	@docker-compose up --build web -d

.PHONY: down
down:
	@docker-compose -f docker-compose.yml down

## View docker logs for containers started in `make dev`
.PHONY: logs
logs:
	@docker-compose logs -ft

## Run tests with coverage
.PHONY: test
test:
	@if [ $$(docker ps -a -f name=dev | wc -l) -eq 2 ]; then \
		docker exec dev python -m pytest --version; \
	else \
		echo "No containers running.. Starting Django runserver:"; \
		make build; \
		echo "Running Tests"; \
	fi

	@docker exec dev python -m pytest -v --cov --disable-warnings;\
	echo "Tests finished."

## Create lint issues file
.PHONY: lint_issues
lint_issues:
	@touch $@

## Lint code using pylama skipping files in env (if pyenv created)
.PHONY: lint
lint: lint_issues
	@python3 -m pylama --version
	@pylama --skip "env/*" -r lint_issues || echo "Linter run returned errors. Check lint_issues file for details." && false

schema_validate:
	@echo $(shell python3 scripts/clone_access_modules.py && python3 scripts/validator.py)

run_semgrep:
	$(shell semgrep --error --config "p/cwe-top-25" --config "p/owasp-top-ten" --config "p/r2c-security-audit")
