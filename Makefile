schema_validate:
	@echo $(shell python3 scripts/clone_access_modules.py && python3 scripts/validator.py)
