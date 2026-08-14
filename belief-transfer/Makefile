UV ?= uv

.PHONY: help setup test data-push data-pull

help:
	@echo "setup      install Python 3.12 deps with uv"
	@echo "test       run pytest"
	@echo "data-push  upload data/ (minus cache/) to the HF dataset repo"
	@echo "data-pull  download the HF dataset repo into data/"

setup:
	$(UV) sync --dev

test:
	$(UV) run pytest

data-push:
	$(UV) run python -m belief_transfer.data_sync push

data-pull:
	$(UV) run python -m belief_transfer.data_sync pull
