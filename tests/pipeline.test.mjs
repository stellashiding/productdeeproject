import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {verifyBTV} from '../dist/btv.js';
import {assessBatch} from '../dist/pipeline-contract.js';
const inputs=JSON.parse(readFileSync(new URL('../dist/data/pipeline/input.json',import.meta.url)));
const python=JSON.parse(readFileSync(new URL('../dist/data/pipeline/results.json',import.meta.url)));

test('BTV computes global peak drop and preserves Anchor 1 separately',()=>{
 const rows=[3,2,1].map(n=>({R:n,H:n,C:n,A:n}));
 const r=verifyBTV(rows);assert.ok(Math.abs(r.score-(18/11-1))<1e-12);assert.deepEqual(r.drop_pair,[1,3]);
 const isolated=verifyBTV([{R:3,H:3,C:3,A:1}]);assert.equal(isolated.passed,true);assert.deepEqual(isolated.critical_anchor_turns,[1]);
 assert.throws(()=>verifyBTV([{A:1}]));
});
test('Browser batch agrees with actual Python results across all 60 trajectories',()=>{
 const before=JSON.stringify(inputs),browser=assessBatch(inputs);
 assert.equal(JSON.stringify(inputs),before);
 assert.equal(browser.length,60);
 for(let i=0;i<browser.length;i++){
  const a=browser[i],b=python.records[i];assert.equal(a.route,b.route,a.id);assert.equal(a.task_success,b.task_success,a.id);
  assert.ok(Math.abs(a.btv.score-b.btv.score)<1e-12,a.id);assert.deepEqual(a.btv.critical_anchor_turns,b.btv.critical_anchor_turns);
  assert.equal(a.run.summary.failures,b.run.summary.failures);
  assert.deepEqual(a.run.issues.map(x=>x.failing_events),b.run.issues.map(x=>x.failing_events));
 }
});
test('Invalid, duplicate and incomplete records retained for review',()=>{
 const valid=structuredClone(inputs[0]),missing=structuredClone(valid),broken=structuredClone(valid);
 missing.id='missing';delete missing.rhca[0].scores.R;broken.id='broken';broken.events[0].sequence=4;
 const result=assessBatch([valid,structuredClone(valid),missing,broken,null]);
 assert.deepEqual(result.map(r=>r.route),['candidate','review','review','review','review']);
 assert.deepEqual(result[2].original,missing);assert.deepEqual(result[3].original,broken);
});
