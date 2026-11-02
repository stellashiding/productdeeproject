import test from 'node:test';
import assert from 'node:assert/strict';
import {agentSpecification,agentFixture,evaluateEvents,validateAgentSpecification,compareEvents} from '../dist/agent-contract.js';
import {validateRun,parseRoute} from '../dist/core.js';
const find=(r,event,id)=>r.events.find(e=>e.id===event).evaluations.find(a=>a.criterion_id===id);
function append(run,type,data){run.events.push({id:'extra-'+run.events.length,sequence:run.events.length+1,type,text:'Additional recorded evidence.',data});return run;}
test('revocation, changed goal, changed requirement and stale completion retain separate evidence',()=>{
 const r=agentFixture();for(const id of ['authorization','current-goal','interface'])assert.equal(find(r,'edit-2',id).status,'fail');assert.equal(find(r,'premature','verified-completion').status,'fail');assert.equal(find(r,'complete','verified-completion').status,'pass');assert.equal(r.summary.critical_violations,2);assert.equal(r.issues.find(i=>i.criterion_id==='authorization').history_retained,true);assert.equal(r.issues.find(i=>i.criterion_id==='artifact-check').status,'recovery_observed');assert.equal(validateRun(r),r);
});
test('unseen verification and invalid booleans are unknown, not pass',()=>{
 const r=agentFixture();delete r.events.find(e=>e.id==='check-1').data.passed;const fresh=evaluateEvents(r,r.specification);assert.equal(find(fresh,'check-1','artifact-check').status,'unknown');
 const tiny={events:[{id:'c',sequence:1,type:'completion',text:'Done',data:{}}]};const checked=evaluateEvents(tiny,agentSpecification());assert.equal(find(checked,'c','verified-completion').status,'unknown');
});
test('a new action invalidates earlier passing verification and recovery',()=>{
 const r=agentFixture();append(r,'action',{tool:'update_artifact',scope:'workspace',goal_id:'repair-v2',arguments:{interface:'v2'}});append(r,'completion',{});const fresh=evaluateEvents(r,r.specification);assert.equal(fresh.issues.find(i=>i.criterion_id==='artifact-check').status,'unknown');assert.equal(fresh.events.at(-1).evaluations.find(a=>a.criterion_id==='verified-completion').status,'fail');
});
test('custom dimensions and numeric checks execute without changing the engine',()=>{
 const s=agentSpecification('blank');s.dimensions[0]={id:'budget',name:'Budget',definition:'Recorded call budget'};s.criteria=[{id:'calls',dimension:'budget',definition:'At most 4 calls',evidence:'Recorded metric',severity:'standard',result_type:'numeric',anchors:{pass:'4 or fewer',fail:'More than 4'},evaluator:{type:'numeric_limit',field:'calls',limit:4,version:'1'}}];assert.deepEqual(validateAgentSpecification(s,{executable:true}),[]);const r=evaluateEvents({events:[{id:'cost',sequence:1,type:'metric',text:'Five calls',data:{field:'calls',value:5}}]},s);assert.equal(find(r,'cost','calls').status,'fail');assert.equal(find(r,'cost','calls').value,5);assert.equal(parseRoute('#garden?dim=budget').dimension,'budget');
});
test('comparison allows differing actions but rejects differing external protocols',()=>{
 const a=agentFixture('reference'),b=agentFixture();assert.equal(compareEvents(a,b).comparable,true);b.protocol.environment='different';assert.equal(compareEvents(a,b).comparable,false);
});
test('unknown evidence interrupts a recovery streak',()=>{
 const r=agentFixture();r.events.find(e=>e.id==='check-3').data.passed=null;const x=evaluateEvents(r,r.specification);assert.equal(x.issues.find(i=>i.criterion_id==='artifact-check').status,'unknown');assert.deepEqual(x.issues.find(i=>i.criterion_id==='artifact-check').recovery_events,[]);
});
test('imported future evidence and ambiguous event ordering are rejected',()=>{
 const r=agentFixture();r.events[0].evaluations[0].evidence=[{event_id:'complete',quote:r.events.at(-1).text}];assert.throws(()=>validateRun(r),/future/);r.events[1].sequence=1;assert.throws(()=>evaluateEvents(r,r.specification),/sequence/);
});
