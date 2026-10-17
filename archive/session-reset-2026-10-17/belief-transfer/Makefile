UV ?= uv

# Bootstrap and hygiene only. Every *job* -- datagen, sft, efficacy, benchmarks, data sync,
# chat -- goes through the one entrypoint instead of getting a target here:
#
#   python run.py +run=factory_farming_v1
#   python run.py +run=factory_farming_v1 stage=sft
#   python run.py +run=adhoc stage=data_pull
#   python run.py --help                      # lists every config group and option
#
# A target per stage was a second way to launch the same thing, with its own flags to keep
# in step, which is exactly what the config migration removed.

.PHONY: help setup tectonic test data-pull data-push cache-pull cache-push clean clean-llm-cache

help:
	@echo "Bootstrap:"
	@echo "  setup            install deps with uv (pinned torch/transformers/trl/peft) + tectonic"
	@echo "  tectonic         install the LaTeX engine \`bt pdf\` needs (part of setup)"
	@echo "  test             run pytest (GPU-free; add --run-gpu for weight-loading tests)"
	@echo "  data-pull        download the HF dataset repo into data/"
	@echo "  data-push        upload data/ (minus cache/) to the HF dataset repo"
	@echo "  cache-pull       download the LLM call cache (opt-in; saves real money)"
	@echo "  cache-push       upload the LLM call cache"
	@echo ""
	@echo "Hygiene:"
	@echo "  clean            remove __pycache__, .pytest_cache, and HF download bookkeeping"
	@echo "  clean-llm-cache  remove data/cache/ -- NOT part of clean; costs ~\$$2.90/corpus to refill"
	@echo ""
	@echo "Everything else is a job: python run.py --help"

setup: tectonic
	$(UV) sync --dev --verbose 2>&1 | while IFS= read -r line; do echo "[$$(date +%H:%M:%S)] $$line"; done

# `bt pdf` compiles a note or paper with tectonic, and every insight note gets a PDF in the
# same pass as its note.md (.claude/skills/write-insight, section 8) -- so this belongs in
# bootstrap rather than being installed by hand the first time a PDF is wanted. Single static
# binary, no TeX distribution: it fetches what a document needs on first compile. Idempotent
# and non-fatal, since a box that cannot reach the installer can still run every other target.
TECTONIC_BIN ?= /usr/local/bin/tectonic

tectonic:
	@if command -v tectonic >/dev/null 2>&1; then \
		echo "tectonic already installed: $$(command -v tectonic) ($$(tectonic --version))"; \
	else \
		echo "installing tectonic -> $(TECTONIC_BIN) ..."; \
		tmp=$$(mktemp -d) && \
		( cd "$$tmp" && curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh ) && \
		install -m 0755 "$$tmp/tectonic" "$(TECTONIC_BIN)" && rm -rf "$$tmp" && \
		echo "tectonic installed: $$(tectonic --version)" \
		|| echo "WARNING: tectonic install failed -- \`bt pdf\` will not work until it is installed"; \
	fi

test:
	$(UV) run pytest

data-pull:
	$(UV) run python run.py +run=adhoc stage=data_pull

data-push:
	$(UV) run python run.py +run=adhoc stage=data_push

cache-pull:
	$(UV) run python -c "from belief_transfer.data_sync import pull_cache; pull_cache()"

cache-push:
	$(UV) run python -c "from belief_transfer.data_sync import push_cache; push_cache()"

# Deliberately leaves data/ alone apart from `.cache/`, which is snapshot_download's own
# bookkeeping: without removing it, a pull-then-push round trip uploads that bookkeeping
# back to the dataset repo, where the next pull downloads it again.
clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache data/.cache
	@echo "cleaned. data/cache/ (LLM calls) left in place -- see clean-llm-cache"

# Separate target, never a dependency of `clean`: this cache is the difference between a
# ~\$1.75 re-run and a ~\$2.90 one per corpus (see configs/run/control_offtopic_v2.yaml),
# and it is not recoverable except by paying for the calls again.
clean-llm-cache:
	rm -rf data/cache
