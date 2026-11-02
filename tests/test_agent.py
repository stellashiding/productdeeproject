import json
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from deeproject.engine import evaluate, compare, validate_specification, write_result
from deeproject.agent import validate_events
ROOT=Path(__file__).resolve().parents[1]
class AgentTests(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads((ROOT/'dist/data/agent-spec.json').read_text())
        self.log=json.loads((ROOT/'dist/data/agent-violation.json').read_text())
    def test_js_python_evaluation_parity(self):
        for variant in ['violation','reference']:
            log=json.loads((ROOT/'dist/data'/('agent-'+variant+'.json')).read_text())
            result=evaluate(log,self.spec)
            self.assertEqual(result['events'],log['events'])
            self.assertEqual(result['issues'],log['issues'])
            self.assertEqual(result['summary'],log['summary'])
            self.assertEqual(result['source_run_id'],log['id'])
    def test_future_evidence_becomes_error_and_source_is_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,'agent_judge.py').write_text('def judge(events, criterion):\n return {"status":"pass","explanation":"Claim", "evidence":[{"event_id":"complete", "quote":"future"}]}\n')
            sys.path.insert(0,tmp)
            try:
                s=deepcopy(self.spec);s['criteria']=s['criteria'][:1];s['criteria'][0]['evaluator']={'type':'python','callable':'agent_judge:judge','version':'1'}
                result=evaluate(self.log,s)
                self.assertEqual(result['events'][0]['evaluations'][0]['status'],'error')
                self.assertEqual(result['events'][0]['text'],self.log['events'][0]['text'])
            finally:
                sys.path.remove(tmp);sys.modules.pop('agent_judge',None)
    def test_no_verification_is_unknown_and_new_action_invalidates_success(self):
        log={'events':[{'id':'done','sequence':1,'type':'completion','text':'Done','data':{}}]}
        result=evaluate(log,self.spec)
        self.assertEqual(result['events'][0]['evaluations'][-1]['status'],'unknown')
        self.log['events'].append({'id':'edit-again','sequence':21,'type':'action','text':'Artifact changed again','data':{'tool':'update_artifact','scope':'workspace','goal_id':'repair-v2','arguments':{'interface':'v2'}}})
        result=evaluate(self.log,self.spec)
        self.assertEqual(next(i for i in result['issues'] if i['criterion_id']=='artifact-check')['status'],'unknown')
    def test_comparison_checks_external_protocol_and_result_report_roundtrip(self):
        baseline=evaluate(json.loads((ROOT/'dist/data/agent-reference.json').read_text()),self.spec)
        candidate=evaluate(self.log,self.spec)
        self.assertTrue(compare(baseline,candidate)['comparable'])
        candidate['protocol']['environment']='different'
        self.assertFalse(compare(baseline,candidate)['comparable'])
        with tempfile.TemporaryDirectory() as tmp:
            write_result(candidate,tmp)
            text=Path(tmp,'report.md').read_text()
            self.assertIn('Critical',text.title());self.assertIn('revoke',text);self.assertEqual(json.loads(Path(tmp,'result.json').read_text())['events'],candidate['events'])
    def test_invalid_order_and_unbound_custom_dimensions(self):
        s=deepcopy(self.spec);s['dimensions'].append({'id':'my_dimension','name':'My dimension','definition':'Defined by the author'})
        s['criteria'][0]['dimension']='my_dimension'
        self.assertEqual(validate_specification(s,True),[])
        s['criteria'][0]['evaluator']={'type':'unbound','version':'1'}
        self.assertTrue(validate_specification(s,True))
        self.log['events'][1]['sequence']=1
        with self.assertRaises(ValueError):validate_events(self.log)
if __name__=='__main__':unittest.main()
