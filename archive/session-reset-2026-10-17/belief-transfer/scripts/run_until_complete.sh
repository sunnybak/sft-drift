#!/usr/bin/env bash
# Re-launch a run until it finishes, for jobs long enough to meet a rate limit.
#
#   scripts/run_until_complete.sh +run=multiformat_v1
#
# Safe because of the LLM cache, not because of anything this script does: prompts in
# this codebase are deterministic functions of an item index, so a killed run re-issues
# the same prompts, hits the cache for everything it already completed, and only pays
# for the remainder (AGENTS.md, Caching). Each attempt therefore starts further along
# than the last, and a run that dies at 90% costs one attempt's worth of retrying.
#
# This is a launcher, not a pipeline stage: it makes no decisions and touches no
# artifacts. If a run is failing for a reason that is not a rate limit, this will loop
# on it MAX_ATTEMPTS times and then stop -- read the log rather than raising the cap.
set -uo pipefail

MAX_ATTEMPTS="${MAX_ATTEMPTS:-12}"
LOG="${LOG:-/tmp/run_until_complete.log}"
PYTHON="${PYTHON:-.venv/bin/python}"

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
    echo "=== attempt $attempt/$MAX_ATTEMPTS: $* ===" | tee -a "$LOG"
    if "$PYTHON" run.py "$@" >>"$LOG" 2>&1; then
        echo "=== completed on attempt $attempt ===" | tee -a "$LOG"
        exit 0
    fi
    echo "=== attempt $attempt failed; cached calls will be skipped on retry ===" | tee -a "$LOG"
    sleep 30
done

echo "=== gave up after $MAX_ATTEMPTS attempts; see $LOG ===" | tee -a "$LOG"
exit 1
