UV ?= uv

.PHONY: help setup test status restore save verify data-pull data-push
help:
	@echo "setup / test: locked environment and weight-free tests"
	@echo "status / restore / save / verify: current private experiment handoff"
	@echo "Commit and push source before save. See ../SETUP.md."

setup:
	$(UV) sync --locked --dev

test:
	$(UV) run --no-sync pytest

status:
	$(UV) run --no-sync python scripts/handoff.py status

restore:
	$(UV) run --no-sync python scripts/handoff.py restore

save:
	$(UV) run --no-sync python scripts/handoff.py save

verify:
	$(UV) run --no-sync python scripts/handoff.py verify

# Compatibility spellings now use only the current scoped snapshot.
data-pull: restore

data-push: save
