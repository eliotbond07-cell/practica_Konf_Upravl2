#!/usr/bin/env bash
python3 ./src/main.py --config ./tests/config/config.toml

python3 ./src/main.py --config ./tests/config/config_openssh.toml

python3 ./src/main.py --config ./tests/config/config_linear.toml

python3 ./src/main.py --config ./tests/config/config_cyclic.toml

python3 ./src/main.py --config ./tests/config/config_branches.toml

python3 ./src/main.py --config ./tests/config/config_error_test_repo.toml

python3 ./src/main.py --config ./tests/config/config_hard.toml