PYTHON  := python
MAIN    := ./src/main.py
CONFIG  := ./tests/config

.PHONY: run run-openssh run-alpine-sdk run-linear run-cyclic run-branches run-error-test-repo run-hard clean

run:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config.toml

run-openssh:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config_openssh.toml

run-alpine-sdk:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config_alpine_sdk.toml

run-linear:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config_linear.toml

run-cyclic:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config_cyclic.toml

run-branches:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config_branches.toml

run-error-test-repo:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config_error_test_repo.toml

run-hard:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config_hard.toml

clean:
	rm -rf ../src/__pycache__ ./__pycache__