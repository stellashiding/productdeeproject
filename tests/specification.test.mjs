import test from 'node:test';
import assert from 'node:assert/strict';
import {defaultSpecification,validateSpecification,evaluateTurns,diagnose,fixtureRun,compatibility} from '../dist/specification.js';
import {assessment} from '../dist/core.js';
test('specifications require all rating anchors and do not execute unbound criteria',()=>{
 const s=defaultSpecification();delete s.criteria[0].anchors['2'];assert.match(validateSpecification(s).join(' '),/anchor 2/);
 s.criteria[0].anchors['2']='Review';s.criteria[0].evaluator={type:'unbound'};assert.equal(validateSpecification(s).length,0);assert.match(validateSpecification(s,{executable:true}).join(' '),/Bind/);
});
test('exact-text fixture records evidence, corrections and the absence of sustained recovery',()=>{
 const s=defaultSpecification(),r=fixtureRun(s,'drift');assert.deepEqual(r.turns.map(t=>t.evaluations[0].score),[3,1,1,3]);assert.equal(r.issues[0].first_observed,2);assert.deepEqual(r.issues[0].correction_turns,[4]);assert.match(r.issues[0].recovery,/Not established/);assert.equal(assessment(r,1,'A').status,'fails');assert.equal(assessment(r,1,'R').status,'unassessed');assert.equal(r.fixture,true);
});
test('inapplicable and missing observations do not establish recovery',()=>{
 const s=defaultSpecification();s.criteria[0].applicability.to_turn=2;const t=evaluateTurns([{number:1,user:'x',assistant:'Atlas'},{number:2,user:'x',assistant:'missing'},{number:3,user:'x',assistant:'Atlas'}],s);assert.equal(t[2].evaluations[0].score,null);assert.equal(diagnose(t,s)[0].status,'unknown');
});
test('comparison rejects specification changes and mismatched scenario inputs',()=>{
 const s=defaultSpecification(),a=fixtureRun(s,'drift'),b=fixtureRun(s);assert.deepEqual(compatibility(a,b),[]);b.specification.version++;assert.match(compatibility(a,b).join(' '),/Specification/);b.specification.version--;b.turns[0].user='Different input';assert.match(compatibility(a,b).join(' '),/inputs/);
});
test('a local review cannot erase disagreement with a configured assessment',()=>{
 const r=fixtureRun(defaultSpecification(),'drift');const v=assessment(r,1,'A',{review:{score:3}});assert.equal(v.source,'Your local review');assert.equal(v.disagreement,true);assert.equal(r.turns[1].evaluations[0].score,1);
});
