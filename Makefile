schema_validate:
	@echo $(shell python3 clone_access_modules.py && python3 validator.py)
