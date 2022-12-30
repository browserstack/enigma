schema_validate:
	@echo $(shell python3 scripts/clone_access_modules.py && python3 scripts/validator.py)

run_semgrep:
	$(shell semgrep --error --config "p/cwe-top-25" --config "p/owasp-top-ten" --config "p/r2c-security-audit")
