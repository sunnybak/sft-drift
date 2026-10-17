"""Freeze hand-reviewed diagnostic content, without choosing on model scores."""
import json
from pathlib import Path

from belief_transfer.analysis.jsonl_md import write_md
from belief_transfer.config import load_job, write_resolved_config
from belief_transfer.evals.pilot import build_banks, fingerprint, validate_wordings
from belief_transfer.schemas import PilotWording

job = load_job(['+run=conviction_generalization_v1'])
spec = job.pilot_bench
directory = Path(__file__).resolve().parents[1] / 'data/generated/ethical_pilot' / spec.bank_run_id
if directory.exists():
    raise FileExistsError('diagnostic content is immutable')
wordings = []
for target in spec.targets:
    d = target.definition
    for i, statement in enumerate([d.stance.statement, *d.stance.paraphrases]):
        negation = d.stance.negation if i == 0 else 'It is not the case that ' + statement[0].lower() + statement[1:]
        wordings.append(PilotWording(belief_id=d.id, wording_id=f'w{i}', statement=statement, negation=negation, scope=d.scope))
validate_wordings(spec, wordings)
binary, categorical = build_banks(spec, wordings)
directory.mkdir(parents=True)
write_resolved_config(job, directory)
for name, rows in [('belief_wordings', [w.model_dump() for w in wordings]), ('binary_bank', binary), ('categorical_bank', categorical)]:
    path = directory / (name + '.jsonl')
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows));write_md(path)
manifest = {'targets_sha': fingerprint([t.model_dump() for t in spec.targets]),
    'wordings_sha': fingerprint([w.model_dump() for w in wordings]), 'binary_sha': fingerprint(binary),
    'categorical_sha': fingerprint(categorical), 'meta_eval': {'label_status': 'agent_authored_diagnostic',
        'review': 'Fixed before new-topic model calls. Same propositions/scope and logical complements reviewed by agent. Limited template paraphrases; no human gold or population representativeness.'}}
(directory/'bank_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Frozen five new diagnostic topics / thirty wordings; no model calls.')
