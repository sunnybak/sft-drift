"""Is the hop ladder actually separated?

Each rung's config carries a discriminator the rung below is supposed to FAIL. That is a
design claim until someone measures it, so this judges every bank's items against every
rung's discriminator and prints the matrix. A ladder whose rungs all pass each other's
checks is three banks with different labels, not three distances.
"""
import asyncio, sys
from pathlib import Path
sys.path.insert(0, "src")

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf
from belief_transfer.schemas import JobConfig
from belief_transfer.evals import gate, suite as suite_mod
from belief_transfer.generation.context import RunContext

ROOT = Path("/root/sft-drift/belief-transfer")
DISCRIMINATORS = {
    "0": ["action_belief_is_the_decision"],
    "05": ["action_not_belief_restated"],
    "1": ["action_requires_further_premise", "action_options_omit_subject"],
}
TOPICS = {"ff": "factory_farming_stmt", "mono": "monolith_architecture", "pata": "patagonia_fleeces"}


def job_for(run_id):
    with initialize_config_dir(config_dir=str(ROOT / "configs"), version_base=None):
        cfg = compose(config_name="config", overrides=[f"+run={run_id}"])
    return JobConfig.model_validate(OmegaConf.to_container(cfg, resolve=True))


async def main():
    ctx = RunContext()
    print(f"{'bank':18}{'judged by rung':>16}  {'check':38} pass rate")
    print("-" * 92)
    for tk, exp in TOPICS.items():
        for item_hop in ["0", "05", "1"]:
            items = suite_mod.load_rows(
                suite_mod.items_path(exp, f"hop{item_hop}_{tk}_suite", "action"))
            for judge_hop in ["0", "05", "1"]:
                wanted = DISCRIMINATORS[judge_hop]
                job = job_for(f"hop{judge_hop}_{tk}_suite")
                cfg = job.eval.evalgen
                scores = await gate.score_items(
                    items, job.experiment, cfg, throughput=8, force=False, context=ctx)
                for cid in wanted:
                    vals = [s[cid] for s in scores if cid in s]
                    if not vals:
                        continue
                    rate = sum(1 for v in vals if v.get("passed")) / len(vals)
                    flag = "  <- own rung" if judge_hop == item_hop else ""
                    print(f"hop{item_hop}_{tk:12}{judge_hop:>16}  {cid:38} {rate:5.0%}{flag}")
        print()

asyncio.run(main())
