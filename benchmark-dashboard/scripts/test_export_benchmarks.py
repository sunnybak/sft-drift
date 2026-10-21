import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from export_benchmarks import build

class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.project=Path(self.tmp.name)
    def save(self,run,data):
        p=self.project/'data/results/ethical_pilot'/run/'summary.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data));return p
    def test_missing_is_not_zero(self):
        s=build(self.project)
        self.assertEqual(s['observations'],[]);self.assertTrue(s['missing_sources']);self.assertEqual(len(s['models']),8)
    def test_zero_scores_and_source_hash_preserved(self):
        a={'lookup':{'n_correct':0,'n':20},'controls':{'n_correct':32,'n_expected':32,'strict_format_rate':1,'null_eligible':16,'null_expected':16,'null_flip_rate':0}}
        p=self.save('ethics_gpu_registry_untagged_validation_v2',{'arms':{'base':a,'adapter':a},'training_run_id':'example'})
        s=build(self.project);o=next(o for o in s['observations'] if o['model']=='untagged' and o['metric']=='strict-lookup')
        self.assertEqual((o['numerator'],o['denominator'],o['value']),(0,20,0));self.assertEqual(o['source_sha256'],hashlib.sha256(p.read_bytes()).hexdigest())
    def test_retention_cohorts_do_not_get_pooled(self):
        def mode(k,n,known):return {'known':{'semantic_correct':known,'strict_format':n,'response_boundaries_valid':n,'normal_stop':n},'known_n':n,'full':{'semantic_correct':k},'full_n':64}
        self.save('ethics_gpu_registry_untagged_retention_v2',{'by_mode':{'True':mode(64,64,64),'False':mode(59,44,44)}})
        obs={o['metric']:o for o in build(self.project)['observations']}
        self.assertEqual(obs['retain-nonthinking']['denominator'],44)
        self.assertEqual(obs['retain-full-nonthinking']['denominator'],64)
        self.assertEqual(obs['retain-full-nonthinking']['numerator'],59)
        self.assertEqual(obs['retain-stops-nonthinking']['numerator'],44)
    def test_semantic_match_keeps_length_stops(self):
        arm={name:{'n':n,'unambiguous_numeric_match':k,'length_stops':cap} for name,n,k,cap in [('original_long',20,17,2),('natural_registry',20,17,0),('direct_math',8,8,0)]}
        self.save('ethics_gpu_registry_untagged_transfer_v2',{'by_arm':{'ethics_sft_registry_untagged_replay_v2':arm}})
        o=next(o for o in build(self.project)['observations'] if o['metric']=='recall-original')
        self.assertEqual(o['length_stops'],2);self.assertEqual(o['value'],.85)
    def test_invalid_counts_rejected(self):
        arm={n:{'n':20,'unambiguous_numeric_match':21,'length_stops':0} for n in ['original_long','natural_registry','direct_math']}
        self.save('ethics_gpu_registry_untagged_transfer_v2',{'by_arm':{'ethics_sft_registry_untagged_replay_v2':arm}})
        with self.assertRaisesRegex(ValueError,'Invalid benchmark counts'):build(self.project)
if __name__=='__main__':unittest.main()
