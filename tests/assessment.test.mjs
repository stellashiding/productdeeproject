import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {assessment,history,validateRun} from '../dist/core.js';
const root=new URL('../dist/data/',import.meta.url);
const load=async id=>JSON.parse(await readFile(new URL(id+'.json',root),'utf8'));

test('all nine recorded runs keep the actual model and annotation coverage',async()=>{
  const index=await load('index');const entries=index.runs.filter(r=>r.kind==='recorded');assert.equal(entries.length,9);
  let total=0,annotated=0;const models=new Set(),domains=new Set();
  for(const e of entries){const r=validateRun(await load(e.id));assert.equal(r.turns.length,e.turn_count);assert.equal(r.model_id,e.model_id);models.add(r.model_id);domains.add(r.scenario);total+=r.turns.length;annotated+=r.turns.filter(t=>t.annotations.length===2).length;assert.ok(r.turns.every(t=>t.user&&t.assistant&&t.judge?.model));}
  assert.equal(total,78);assert.equal(annotated,34);assert.equal(models.size,3);assert.equal(domains.size,3);
});
test('R06 never falsely recovers when its LLM judge rises to 3',async()=>{
  const r=await load('R06');for(const i of [6,7]){assert.equal(r.turns[i].judge.score,3);const a=assessment(r,i);assert.equal(a.score,1);assert.equal(a.status,'fails');assert.equal(a.source,'Human agreement');assert.equal(a.disagreement,true);assert.equal(history(r,i,'A').hasPriorIssue,true)}
});
test('six human disagreements remain unresolved rather than averaged',async()=>{
  let count=0;for(const id of ['R03','R04','R06','R07']){const r=await load(id);for(let i=0;i<r.turns.length;i++){const a=r.turns[i].annotations;if(a[0].score!==a[1].score){count++;const shown=assessment(r,i);assert.equal(shown.status,'disputed');assert.equal(shown.score,null);assert.equal(shown.source,'Human disagreement')}}}assert.equal(count,6);
});
test('LLM-only records stay provisional and other dimensions are unassessed',async()=>{
  const r=await load('R01');assert.equal(assessment(r,0).source,'LLM assessment · unreviewed');for(const dim of ['R','H','C']){assert.equal(assessment(r,0,dim).score,null);assert.equal(assessment(r,0,dim).status,'unassessed')}
});
test('criterion edits cannot inherit imported scores; an explicit local review is separate',async()=>{
  const r=await load('R06');assert.equal(assessment(r,3,'A',{override:true}).status,'unassessed');const local=assessment(r,3,'A',{override:true,review:{score:2,note:'Explicit review'}});assert.equal(local.score,2);assert.equal(local.source,'Your local review');assert.equal(r.turns[3].annotations[0].score,1);
});
test('authored correction retains the earlier issue without claiming a model run',async()=>{
  const r=await load('DEMO');assert.equal(r.kind,'authored');assert.equal(r.model_id,null);assert.equal(assessment(r,2).status,'fails');assert.equal(assessment(r,3).status,'meets');assert.equal(history(r,3,'A').hasPriorIssue,true);assert.match(assessment(r,3).source,/no model run/);
});
test('invalid imported scores and mismatched turn numbers are rejected',async()=>{
  const r=await load('R01');r.turns[0].judge.score=7;assert.throws(()=>validateRun(r),/scores/);r.turns[0].judge.score=3;r.turns[0].number=9;assert.throws(()=>validateRun(r),/consecutive/);
});
