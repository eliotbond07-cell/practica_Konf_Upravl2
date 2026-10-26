#!/usr/bin/env bash
python3 ./src/main.py --config ./tests/config.toml

python3 ./src/main.py --config ./tests/missing.toml

python3 ./src/main.py --config ./tests/config_missing_parms.toml

python3 ./src/main.py --config ./tests/config_wrong_p_n.toml

python3 ./src/main.py --config ./tests/config_wrong_r_u.toml

python3 ./src/main.py --config ./tests/config_wrong_t_m.toml

python3 ./src/main.py --config ./tests/config_wrong_r_f_p.toml

python3 ./src/main.py --config ./tests/config_wrong_o_i.toml

python3 ./src/main.py --config ./tests/config_wrong_a_t.toml