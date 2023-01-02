# Makefile for python code
# 
# > make help
#
# The following commands can be used.
#
# init:  sets up environment and installs requirements
# install:  Installs development requirments
# format:  Formats the code with autopep8
# lint:  Runs flake8 on src, exit if critical rules are broken
# clean:  Remove build and cache files
# env:  Source venv and environment files for testing
# leave:  Cleanup and deactivate venv
# test:  Run pytest
# run:  Executes the logic

init:
				pip3 install -r requirements.txt

run: ## run celerey workers
run:
				python3 -m celery -A BrowserStackAutomation worker -n worker1 -l DEBUG

clean:
				rm -rf __pycache__
