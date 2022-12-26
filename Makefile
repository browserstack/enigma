validate:
	$(shell git clone https://github.com/browserstack/enigma-public-access-modules.git ../enigma-public-access-modules)
	@echo $(shell python3 validator.py $(config_file))