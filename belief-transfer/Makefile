UV ?= uv

.PHONY: help setup test data-push data-pull bench simple-bench memorization-bench choice-bench chat efficacy

help:
	@echo "setup        install Python 3.12 deps with uv"
	@echo "test         run pytest"
	@echo "data-push    upload data/ (minus cache/) to the HF dataset repo"
	@echo "data-pull    download the HF dataset repo into data/"
	@echo "bench        calibrate batch size for this machine -> configs/hardware_profile.yaml"
	@echo "simple-bench run the simple correctness/throughput eval at the calibrated batch size"
	@echo "memorization-bench  verify SFT works on this box (AGENTS.md tiny-dataset memorization)"
	@echo "choice-bench MCQ ability + confidence of a checkpoint (belief evals depend on it)"
	@echo "chat         interactive CLI chat with a base model or a LoRA checkpoint"
	@echo "efficacy     train M+/M- and measure whether the corpus was absorbed (tune SFT on this)"

setup:
	$(UV) sync --dev

test:
	$(UV) run pytest

data-push:
	$(UV) run python -m belief_transfer.data_sync push

data-pull:
	$(UV) run python -m belief_transfer.data_sync pull

bench:
	$(UV) run python -m belief_transfer.inference.bench calibrate $(BENCH_ARGS)

simple-bench:
	$(UV) run python -m belief_transfer.inference.bench simple $(BENCH_ARGS)

memorization-bench:
	$(UV) run python -m belief_transfer.inference.bench memorize $(BENCH_ARGS)

choice-bench:
	$(UV) run python -m belief_transfer.benchmarks choice $(BENCH_ARGS)

chat:
	$(UV) run python -m belief_transfer.client $(CHAT_ARGS)

efficacy:
	$(UV) run python -m belief_transfer.evals $(EVAL_ARGS)
