run_semgrep:
		$(shell semgrep --error --config "p/cwe-top-25" --config "p/owasp-top-ten" --config "p/r2c-security-audit")
