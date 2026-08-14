UV ?= uv

.PHONY: help setup test data-push data-pull download-models calibrate memorization-bench perf-bench choice-bench chat efficacy

help:
	@echo "setup        install Python 3.12 deps with uv"
	@echo "test         run pytest"
	@echo "data-push    upload data/ (minus cache/) to the HF dataset repo"
	@echo "data-pull    download the HF dataset repo into data/"
	@echo "download-models  fetch configs/models.yaml's models into the local HF cache"
	@echo "calibrate    discover batch size for this machine -> configs/hardware_profile.yaml"
	@echo "memorization-bench  verify SFT works on this box (AGENTS.md tiny-dataset memorization)"
	@echo "perf-bench   correctness + throughput check at the calibrated batch size"
	@echo "choice-bench MCQ ability + confidence of a checkpoint (belief evals depend on it)"
	@echo "chat         interactive CLI chat with a base model or a LoRA checkpoint"
	@echo "efficacy     train M+/M- and measure whether the corpus was absorbed (tune SFT on this)"
	@echo ""
	@echo "Run download-models, then calibrate, before perf-bench/choice-bench/efficacy."

setup:
	$(UV) sync --dev

test:
	$(UV) run pytest

data-push:
	$(UV) run python -m belief_transfer.data_sync push

data-pull:
	$(UV) run python -m belief_transfer.data_sync pull

download-models:
	$(UV) run python -m belief_transfer.inference.calibrate download $(BENCH_ARGS)

calibrate:
	$(UV) run python -m belief_transfer.inference.calibrate calibrate $(BENCH_ARGS)

memorization-bench:
	$(UV) run python -m belief_transfer.inference.calibrate memorize $(BENCH_ARGS)

perf-bench:
	$(UV) run python -m belief_transfer.benchmarks perf $(BENCH_ARGS)

choice-bench:
	$(UV) run python -m belief_transfer.benchmarks choice $(BENCH_ARGS)

chat:
	$(UV) run python -m belief_transfer.client $(CHAT_ARGS)

efficacy:
	$(UV) run python -m belief_transfer.evals $(EVAL_ARGS)
