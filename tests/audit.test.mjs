import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {auditRows,AUDIT_CHECKS} from '../dist/audit.js';
import {assessBatch} from '../dist/pipeline-contract.js';
const read=p=>JSON.parse(readFileSync(new URL(p,import.meta.url)));
const audit=read('../dist/data/public-audit/audit.json');
test('Published audit metadata reconciles with actual full-dataset structural checks',()=>{
 assert.equal(audit.records.length,20363);
 assert.equal(auditRows(audit.records).length,2226);
 assert.equal(auditRows(audit.records,{route:'structural_candidate'}).length,18137);
 for(const [flag,count] of Object.entries(audit.summary.flag_counts))assert.equal(audit.records.filter(r=>r.flags.includes(flag)).length,count,flag);
 assert.equal(auditRows(audit.records,{check:'duplicate'}).length,985);
 assert.ok(AUDIT_CHECKS.every(c=>c.flags.length));
 assert.equal(audit.summary.model_runs,0);assert.equal(audit.summary.btv_results,0);
});
test('Audit filtering uses source rows and supports empty results',()=>{
 const sample=audit.records.find(r=>r.flags.includes('missing_reference_answer'));
 assert.ok(auditRows(audit.records,{route:'all',query:sample.sha256}).some(r=>r.row===sample.row));
 assert.equal(auditRows(audit.records,{query:'not-a-source-record'}).length,0);
});
test('Controlled BTV filtering matches Python without reading expected labels',()=>{
 const inputs=read('../dist/data/filter/input.json'),reference=read('../dist/data/filter/results.json');
 inputs.forEach(r=>r.generation_truth.expected_route='deliberately-wrong');
 const output=assessBatch(inputs);
 assert.equal(output.length,24);
 assert.deepEqual(output.map(r=>r.route),reference.records.map(r=>r.route));
 for(let i=0;i<output.length;i++)if(output[i].btv.status==='computed')assert.ok(Math.abs(output[i].btv.score-reference.records[i].btv.score)<1e-12);
 assert.equal(output.filter(r=>r.route==='candidate').length,6);
 assert.equal(output.filter(r=>r.route==='problem').length,15);
 assert.equal(output.filter(r=>r.route==='review').length,3);
});
