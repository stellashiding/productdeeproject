import copy
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch
from deeproject.engine import validate_specification, evaluate, run_suite, compare, http_target, write_result

ROOT=Path(__file__).resolve().parents[1]

def judge_with_future_evidence(turns,criterion):
    return {'score':3,'explanation':'bad evidence','evidence':[{'turn':len(turns)+1,'role':'assistant','quote':'future'}]}

class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads((ROOT/'dist/data/fixture-spec.json').read_text())
        self.suite=json.loads((ROOT/'dist/data/fixture-suite.json').read_text())

    def test_history_uses_actual_outputs_and_issues_are_evidence_linked(self):
        calls=[]
        def target(messages):
            calls.append(copy.deepcopy(messages))
            return ['Atlas one','missing','missing','Atlas corrected'][len(calls)-1]
        r=run_suite(self.suite,self.spec,target)
        self.assertEqual(calls[1][1],{'role':'assistant','content':'Atlas one'})
        self.assertEqual([t['evaluations'][0]['score'] for t in r['turns']],[3,1,1,3])
        self.assertEqual(r['issues'][0]['first_observed'],2)
        self.assertEqual(r['issues'][0]['correction_turns'],[4])
        self.assertIn('Not established',r['issues'][0]['recovery'])

    def test_late_unassessed_is_unknown_and_original_annotations_survive(self):
        self.spec['criteria'][0]['applicability']['to_turn']=2
        r=evaluate({'id':'source','turns':[{'user':'x','assistant':'missing','annotations':[{'score':3}]},{'user':'x','assistant':'missing'},{'user':'x','assistant':'Atlas'}]},self.spec)
        self.assertEqual(r['issues'][0]['status'],'unknown')
        self.assertEqual(r['turns'][0]['annotations'],[{'score':3}])

    def test_new_spec_cannot_be_compared_as_target_improvement(self):
        a=run_suite(self.suite,self.spec,lambda history:'missing')
        newer=copy.deepcopy(self.spec);newer['version']+=1
        b=run_suite(self.suite,newer,lambda history:'Atlas')
        self.assertFalse(compare(a,b)['comparable'])

    def test_future_evidence_becomes_error_not_pass(self):
        self.spec['criteria'][0]['evaluator']={'type':'python','callable':'test_harness:judge_with_future_evidence','version':'v1'}
        r=run_suite(self.suite,self.spec,lambda h:'Atlas')
        self.assertEqual(r['evaluation_errors'],4)
        self.assertIsNone(r['turns'][0]['evaluations'][0]['score'])

    def test_generation_failure_is_partial_and_not_retried(self):
        count=[]
        def target(messages):
            count.append(1)
            raise RuntimeError('secret-value-do-not-export')
        r=run_suite(self.suite,self.spec,target)
        self.assertEqual(len(count),1)
        self.assertEqual(r['execution_status'],'partial_failure')
        self.assertEqual(r['evaluation_errors'],0)  # target errors separately recorded
        self.assertNotIn('secret-value',json.dumps(r))
        self.assertIsNone(r['turns'][0]['evaluations'][0]['score'])

    def test_http_adapter_uses_full_history_and_keeps_token_out_of_results(self):
        observed=[]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                observed.append((data,self.headers.get('Authorization')))
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
                self.wfile.write(json.dumps({'assistant':'Atlas response'}).encode())
            def log_message(self,*args): pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with patch.dict(os.environ,{'DEEPROJECT_TARGET_TOKEN':'test-secret'}):
                r=run_suite(self.suite,self.spec,http_target('http://127.0.0.1:'+str(server.server_port)))
            self.assertEqual(len(observed[-1][0]['messages']),7)
            self.assertEqual(observed[0][1],'Bearer test-secret')
            self.assertNotIn('test-secret',json.dumps(r))
        finally: server.shutdown();server.server_close();thread.join()

    def test_missing_anchors_or_unbound_evaluator_cannot_execute(self):
        del self.spec['criteria'][0]['anchors']['2']
        self.assertTrue(validate_specification(self.spec))
        self.spec['criteria'][0]['anchors']['2']='Review'
        self.spec['criteria'][0]['evaluator']={'type':'unbound'}
        self.assertTrue(validate_specification(self.spec,executable=True))

    def test_result_and_report_roundtrip(self):
        r=run_suite(self.suite,self.spec,lambda h:'Atlas')
        with tempfile.TemporaryDirectory() as folder:
            write_result(r,folder)
            reread=json.loads((Path(folder)/'result.json').read_text())
            self.assertEqual(reread['specification'],self.spec)
            self.assertIn('Original conversation',(Path(folder)/'report.md').read_text())

if __name__=='__main__': unittest.main()
