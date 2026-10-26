PYTHON  := python
MAIN    := ./src/main.py
CONFIG  := ./tests

.PHONY: run run-missing run-missing-parms run-wrong-p-n run-wrong-r-u run-wrong-t-m run-wrong-r-f-p run-wrong-o-i run-wrong-a-t clean

run:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config.toml

run-missing:
	$(PYTHON) $(MAIN) --config $(CONFIG)/missing.toml

run-missing-parms:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config_missing_parms.toml

run-wrong-p-n:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config_wrong_p_n.toml

run-wrong-r-u:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config_wrong_r_u.toml

run-wrong-t-m:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config_wrong_t_m.toml

run-wrong-r-f-p:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config_wrong_r_f_p.toml

run-wrong-o-i:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config_wrong_o_i.toml

run-wrong-a-t:
	$(PYTHON) $(MAIN) --config $(CONFIG)/config_wrong_a_t.toml

clean:
	rm -rf ../src/__pycache__ ./__pycache__