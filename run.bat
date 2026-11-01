@echo off
python .\src\main.py --config .\tests\config\config.toml

python .\src\main.py --config .\tests\config\config_openssh.toml

python .\src\main.py --config .\tests\config\config_linear.toml

python .\src\main.py --config .\tests\config\config_cyclic.toml

python .\src\main.py --config .\tests\config\config_branches.toml

python .\src\main.py --config .\tests\config\config_error_test_repo.toml

python .\src\main.py --config .\tests\config\config_hard.toml