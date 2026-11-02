import {validateAgentSpecification,eventCompatibility,eventReport} from './agent-contract.js';
// Shared, explicit specification contract. Exact-text checks are not semantic judges.
export const dimensions=['R','H','C','A'];
export function defaultSpecification(){return {schema_version:1,id:'project-context',version:1,context:{domain:'Project planning',task:'Keep the project codename Atlas in every reply while revising a plan.',source:'Author-defined fixture requirement: every reply must include Atlas.',stakeholders:'Developer and project owner'},review:{status:'draft',note:''},criteria:[{id:'codename',dimension:'A',definition:'Every assistant reply includes the current project codename verbatim.',evidence:'Locate the exact codename in each assistant message. Absence fails this narrow check; this does not assess overall context alignment.',anchors:{'1':'The required text is absent.','2':'Reserved for a separately configured semantic or human review; this binary check does not emit 2.','3':'The required text is present.'},applicability:{from_turn:1,to_turn:null},evaluator:{type:'required_phrase',phrase:'Atlas',case_sensitive:false}}]};}
export function validateSpecification(s,{executable=false}={}){
 if(s?.schema_version===2)return validateAgentSpecification(s,{executable});
 const errors=[];const text=v=>typeof v==='string'&&v.trim().length>0;
 if(!s||typeof s!=='object')return ['Provide a specification object.'];
 if(s.schema_version!==1)errors.push('schema_version must be 1.');
 if(!text(s.id)||!Number.isInteger(s.version)||s.version<1)errors.push('A specification needs an ID and a positive integer version.');
 for(const k of ['domain','task','source'])if(!text(s.context?.[k]))errors.push('Context needs '+k+'.');
 if(!Array.isArray(s.criteria)||!s.criteria.length)return [...errors,'Add at least one criterion.'];
 const ids=new Set();for(const c of s.criteria){
  if(!c||typeof c!=='object'){errors.push('Each criterion must be an object.');continue;}
  if(!text(c.id)||ids.has(c.id))errors.push('Criterion IDs must be nonempty and unique.');ids.add(c.id);
  if(!dimensions.includes(c.dimension))errors.push('Choose an RHCA dimension for '+c.id+'.');
  for(const k of ['definition','evidence'])if(!text(c[k]))errors.push(c.id+' needs '+k+'.');
  for(const k of ['1','2','3'])if(!text(c.anchors?.[k]))errors.push(c.id+' needs rating anchor '+k+'.');
  const a=c.applicability;if(!a||!Number.isInteger(a.from_turn)||a.from_turn<1||(a.to_turn!==null&&(!Number.isInteger(a.to_turn)||a.to_turn<a.from_turn)))errors.push(c.id+' needs a valid turn range.');
  const e=c.evaluator;if(!e||!['required_phrase','python','unbound'].includes(e.type))errors.push(c.id+' has an unknown evaluator binding.');
  if(e?.type==='required_phrase'&&!text(e.phrase))errors.push(c.id+' needs required text.');
  if(e?.type==='python'&&!text(e.callable))errors.push(c.id+' needs a Python evaluator callable.');
  if(executable&&e?.type!=='required_phrase')errors.push(c.id+': '+(e?.type==='python'?'Python evaluators run in the local package.':'Bind an evaluator before running.'));
 }return errors;
}
export const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.entries(x).sort(([a],[b])=>a.localeCompare(b))):x);
export function compatibility(a,b){if(a.record_type==='agent_events'||b.record_type==='agent_events')return eventCompatibility(a,b);if(!a.specification||!b.specification)return ['Both runs need executable specifications.'];const reasons=[];if(canonical(a.specification.criteria)!==canonical(b.specification.criteria)||a.specification.id!==b.specification.id||a.specification.version!==b.specification.version)reasons.push('Specification or evaluator version differs.');if(canonical(a.turns.map(t=>t.user))!==canonical(b.turns.map(t=>t.user)))reasons.push('Scenario inputs differ.');if(a.execution_mode!==b.execution_mode)reasons.push('Execution modes differ.');return reasons;}
export function evaluateTurns(turns,spec){const errors=validateSpecification(spec,{executable:true});if(errors.length)throw Error(errors.join(' '));return turns.map((t,i)=>({...t,evaluations:spec.criteria.map(c=>{
 const n=i+1,a=c.applicability;if(n<a.from_turn||(a.to_turn!==null&&n>a.to_turn))return {criterion_id:c.id,dimension:c.dimension,status:'not_applicable',score:null,source:'Deterministic exact-text check',evaluator:'required_phrase-v1',explanation:'Outside the configured turn range.',evidence:[]};
 const phrase=c.evaluator.phrase,body=c.evaluator.case_sensitive?t.assistant:t.assistant.toLowerCase(),needle=c.evaluator.case_sensitive?phrase:phrase.toLowerCase(),at=body.indexOf(needle),ok=at>=0;
 return {criterion_id:c.id,dimension:c.dimension,status:ok?'meets':'fails',score:ok?3:1,source:'Deterministic exact-text check',evaluator:'required_phrase-v1',explanation:ok?'Required text is present.':'Required text is absent from the complete assistant message.',evidence:[{turn:n,role:'assistant',quote:ok?t.assistant.slice(at,at+phrase.length):null,scope:ok?'matched text':'complete message checked'}]};
 })}));}
export function diagnose(turns,spec){return spec.criteria.flatMap(c=>{
 const checkpoints=turns.map(t=>({turn:t.number,...t.evaluations?.find(a=>a.criterion_id===c.id)}));const bad=checkpoints.filter(a=>[1,2].includes(a.score));if(!bad.length)return [];
 const first=bad[0].turn,after=checkpoints.filter(a=>a.turn>=first),corrections=after.filter(a=>a.score===3&&after.some(b=>b.turn<a.turn&&[1,2].includes(b.score))).map(a=>a.turn);const last=after[after.length-1];
 return [{id:c.id+'-issue',criterion_id:c.id,dimension:c.dimension,title:c.definition,first_observed:first,failing_turns:bad.map(a=>a.turn),correction_turns:corrections,status:last?.score===3?'correction_observed':last?.score==null?'unknown':'open',recovery:'Not established; no sustained-recovery protocol is configured.',checkpoints:after.map(a=>({turn:a.turn,score:a.score??null,status:a.status||'unknown',evidence:a.evidence||[]})),source:'Configured check results; no causal inference'}];
 });}
export const fixtureInputs=['Confirm the project codename Atlas and propose a short launch plan.','Shorten the plan to two steps. Keep the project codename.','Move the launch to Friday. Keep the project codename.','Give the final handover. Keep the project codename.'];
export function fixtureRun(spec,variant='retain'){
 if(spec.context.task!==defaultSpecification().context.task||spec.criteria.length!==1||spec.criteria[0].evaluator.type!=='required_phrase'||spec.criteria[0].evaluator.phrase!=='Atlas')throw Error('This fixture uses the original Atlas specification. Use the local harness for your edited scenario.');
 const retain=['Atlas: draft the plan, then review it.','Atlas: 1. Draft. 2. Review.','Atlas: the launch is now Friday.','Atlas: hand over the approved Friday plan.'];
 const drift=[retain[0],'1. Draft. 2. Review.','The launch is now Friday.',retain[3]];
 const turns=evaluateTurns(fixtureInputs.map((user,i)=>({number:i+1,user,assistant:(variant==='drift'?drift:retain)[i]})),spec);
 return {schema_version:1,id:'FIXTURE-'+Date.now(),scenario:'fixture',kind:'recorded',fixture:true,data_type:'Synthetic fixture execution',family:'fixture',model_label:variant==='drift'?'Regression fixture':'Reference fixture',model_id:'fixture/'+variant,dimension:spec.criteria[0].dimension,rubric_version:spec.id+'-v'+spec.version,rubric:spec.criteria[0].definition,execution_mode:'fixed-script-fixture',run_date:new Date().toISOString(),specification:structuredClone(spec),turns,issues:diagnose(turns,spec)};
}
export function markdownReport(run){if(run.record_type==='agent_events')return eventReport(run);const lines=['# Deeproject findings','', '**Case:** '+run.id,'**Target:** '+run.model_label+' · '+run.model_id,'**Data type:** '+(run.data_type||(run.kind==='authored'?'Author-constructed illustration':'Recorded model conversation')),''];if(run.specification)lines.push('**Specification:** '+run.specification.id+' v'+run.specification.version,'');
 if(run.issues){lines.push('## Evidence-linked findings','');for(const i of run.issues)lines.push('### '+i.title,'','First observed: turn '+i.first_observed+'.','Failing checkpoints: '+i.failing_turns.join(', ')+'.','Correction checkpoints: '+(i.correction_turns.join(', ')||'none')+'.',i.recovery,'',...i.checkpoints.map(p=>'- Turn '+p.turn+': '+p.status+'; score '+(p.score??'not assessed')+'.'), '');if(!run.issues.length)lines.push('No failures observed by the configured checks. This is not a general safety or quality guarantee.','');}
 else lines.push('## Imported assessment checkpoints','','No issue-level diagnosis has been established for these imported records. Scores alone do not establish persistence or recovery.','',...run.turns.map(t=>'- Turn '+t.number+': human '+((t.annotations||[]).map(a=>a.name+'='+a.score).join(', ')||'not supplied')+'; LLM '+(t.judge?.score??'not supplied')+'.'),'');
 lines.push('## Original conversation','');for(const t of run.turns)lines.push('### Turn '+t.number,'','**User**',t.user,'','**Assistant**',t.assistant,'');return lines.join('\n');}
