"""A bounded controller snapshots completed work and never retries failed stages."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC=importlib.util.spec_from_file_location('corpus_supervisor',Path(__file__).parents[1]/'scripts/run_stance_corpus_generation.py')
supervisor=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(supervisor)


@pytest.mark.parametrize('failure', [None,'stage','snapshot','no_progress'])
def test_completed_boundaries_are_saved_and_failures_stop(tmp_path,monkeypatch,failure):
    run='ethics_sft_test_supervisor'
    root=tmp_path/'data/generated/ethical_stance_sft'/run
    output=tmp_path/'data/results/ethical_stance_sft'/run
    root.mkdir(parents=True);output.mkdir(parents=True)
    (root/'contract.json').write_text(json.dumps({'settings':{}}))
    (root/'schedule.jsonl').write_text('{}\n{}\n')
    stages=[];snapshots=[]
    monkeypatch.setattr(supervisor,'PROJECT',tmp_path)
    monkeypatch.setattr(supervisor.sys,'argv',['driver','--run-id',run,'--batches-per-invocation','1'])
    monkeypatch.setattr(supervisor.subprocess,'check_output',lambda command,**_: '' if 'status' in command else 'source-commit')

    class Child:
        pid=123
        def __init__(self,command,**_):
            stages.append(command)
            if 'run.py' in command and failure != 'no_progress':
                folder=root/'shards'/str(len(stages));folder.mkdir(parents=True)
                (folder/'manifest.json').write_text('{}')
        def wait(self): return 1 if failure=='stage' else 0
    def save(command,**_):
        snapshots.append(json.loads((output/'generation_job.json').read_text()))
        return SimpleNamespace(returncode=1 if failure=='snapshot' else 0)
    monkeypatch.setattr(supervisor.subprocess,'Popen',Child)
    monkeypatch.setattr(supervisor.subprocess,'run',save)
    result=supervisor.main()
    status=json.loads((output/'generation_job.json').read_text())
    assert status['child_pid'] is None
    if failure:
        assert result==(2 if failure=='no_progress' else 1) and len(stages)==len(snapshots)==1
        assert status['phase']==('snapshot_failed' if failure=='snapshot' else 'failed')
        assert status['completed_shards']==(0 if failure=='no_progress' else 1)
    else:
        assert result==0 and status['phase']=='completed'
        assert status['completed_shards']==2
        assert len(stages)==len(snapshots)==3
        assert all('stance_corpus.resume=true' in c for c in stages[:2])
        assert snapshots[-1]['phase']=='completed'
