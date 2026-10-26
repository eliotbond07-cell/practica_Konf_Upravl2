@echo off
python .\src\main.py --config .\tests\config.toml

python .\src\main.py --config .\tests\missing.toml

python .\src\main.py --config .\tests\config_missing_parms.toml

python .\src\main.py --config .\tests\config_wrong_p_n.toml

python .\src\main.py --config .\tests\config_wrong_r_u.toml

python .\src\main.py --config .\tests\config_wrong_t_m.toml

python .\src\main.py --config .\tests\config_wrong_r_f_p.toml

python .\src\main.py --config .\tests\config_wrong_o_i.toml

python .\src\main.py --config .\tests\config_wrong_a_t.toml