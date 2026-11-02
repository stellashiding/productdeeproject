import {validateAgentSpecification,validateEvents} from './agent-contract.js';
export const DIMENSIONS = [
  {id:'R', name:'Reasoning transparency', short:'Reasoning', shape:'fern'},
  {id:'H', name:'Helpfulness', short:'Helpfulness', shape:'flower'},
  {id:'C', name:'Consistency', short:'Consistency', shape:'vine'},
  {id:'A', name:'Context alignment', short:'Context', shape:'tree'}
];
export const STATUS = {
  meets:{label:'Meets criterion',color:'#67856c'}, partial:{label:'Partly meets criterion',color:'#ae8b50'},
  fails:{label:'Does not meet criterion',color:'#b97868'}, unassessed:{label:'Not assessed',color:'#a9b3af'},
  disputed:{label:'Review needed',color:'#8d87a4'}
};
export function scoreStatus(score){return score===3?'meets':score===2?'partial':score===1?'fails':'unassessed'}
export function assessment(run, turnIndex, dimension='A', options={}){
  const turn=run.turns[turnIndex];
  if(!turn)return {status:'unassessed',score:null,source:'No record',disagreement:false};
  if(options.review && [1,2,3].includes(options.review.score)){const base=assessment(run,turnIndex,dimension,{override:options.override});return {status:scoreStatus(options.review.score),score:options.review.score,source:'Your local review',disagreement:base.disagreement||(base.score!==null&&base.score!==options.review.score),local:true};}
  if(options.override)return {status:'unassessed',score:null,source:'Edited criterion · not assessed',disagreement:false};
  if(run.specification){
    const applied=(turn.evaluations||[]).filter(a=>a.dimension===dimension);
    if(!applied.length)return {status:'unassessed',score:null,source:'No applicable configured assessment',disagreement:false};
    const scored=applied.filter(a=>[1,2,3].includes(a.score));
    const incomplete=scored.length!==applied.length;
    const score=scored.length?Math.min(...scored.map(a=>a.score)):null;
    return {status:score===1?'fails':score===2?'partial':incomplete?'unassessed':scoreStatus(score),score:incomplete&&score===3?null:score,source:applied.length>1?'Configured checks · lowest applicable score; no averaging':applied[0].source,disagreement:false,configured:true};
  }
  if(dimension!==run.dimension)return {status:'unassessed',score:null,source:'No annotation for this dimension',disagreement:false};
  if(run.kind==='authored')return {status:scoreStatus(turn.authored_score),score:turn.authored_score,source:'Authored illustration · no model run',disagreement:false};
  const anns=turn.annotations||[];
  if(anns.length>=2){
    const same=anns.every(a=>a.score===anns[0].score);
    return {status:same?scoreStatus(anns[0].score):'disputed',score:same?anns[0].score:null,source:same?'Human agreement':'Human disagreement',disagreement:!same||(!!turn.judge&&turn.judge.score!==anns[0].score),human:true};
  }
  if(anns.length===1)return {status:'disputed',score:null,source:'Single annotation · review pending',disagreement:false,human:true};
  if(turn.judge)return {status:scoreStatus(turn.judge.score),score:turn.judge.score,source:'LLM assessment · unreviewed',disagreement:false};
  return {status:'unassessed',score:null,source:'No assessment',disagreement:false};
}
export function history(run, at, dimension, optionsForTurn=()=>({})){
  const records=run.turns.slice(0,at+1).map((_,i)=>assessment(run,i,dimension,optionsForTurn(i)));
  return {firstIssue:records.findIndex(r=>r.status==='partial'||r.status==='fails')+1,
    issueCount:records.filter(r=>r.status==='partial'||r.status==='fails').length,
    disputedCount:records.filter(r=>r.status==='disputed').length,
    hasPriorIssue:records.slice(0,-1).some(r=>r.status==='partial'||r.status==='fails')};
}
export function parseRoute(hash){
  const [page,search='']=(hash||'#home').replace(/^#/,'').split('?');
  const params=new URLSearchParams(search);
  return {page:['home','garden','workbench','diagnostics','design','run','compare','docs'].includes(page)?page:'home',run:params.get('run')||'R06',turn:Math.max(1,parseInt(params.get('turn')||'1',10)||1),dimension:/^[A-Za-z][A-Za-z0-9_-]{0,63}$/.test(params.get('dim')||'')?params.get('dim'):'A'};
}
export function route(page,run='R06',turn=1,dimension='A'){return '#'+page+'?'+new URLSearchParams({run,turn:String(turn),dim:dimension})}
export function validateRun(run){
  if(run?.record_type==='agent_events'){validateEvents(run);const errors=validateAgentSpecification(run.specification);if(errors.length)throw Error(errors.join(' '));if(typeof run.id!=='string'||!run.id||!Array.isArray(run.issues))throw Error('Event results need an ID and issue records.');for(const e of run.events){if(!Array.isArray(e.evaluations))throw Error('Import evaluated results, or evaluate a raw log in Run.');for(const a of e.evaluations){if(!run.specification.criteria.some(c=>c.id===a.criterion_id)||!['pass','fail','unknown','not_applicable','error'].includes(a.status))throw Error('Invalid event assessment.');for(const ev of a.evidence||[]){const source=run.events.find(v=>v.id===ev.event_id);if(!source||source.sequence>e.sequence||typeof ev.quote!=='string'||!source.text.includes(ev.quote))throw Error('Invalid or future event evidence.');}}}return run;}

  if(!run||typeof run!=='object'||!Array.isArray(run.turns)||!run.turns.length||run.turns.length>200)throw Error('Provide a case with 1–200 turns.');
  if(typeof run.id!=='string'||!run.id||typeof run.rubric!=='string')throw Error('The case needs an id and a rubric.');
  if(!['recorded','authored'].includes(run.kind))throw Error('kind must be recorded or authored.');
  if(!DIMENSIONS.some(d=>d.id===run.dimension))throw Error('dimension must be R, H, C or A.');
  if(run.kind==='recorded'&&(!run.model_id||typeof run.model_id!=='string'))throw Error('Recorded cases need a model_id.');
  if(run.model_label!==undefined&&typeof run.model_label!=='string')throw Error('model_label must be text.');
  if(run.rubric_version!==undefined&&typeof run.rubric_version!=='string')throw Error('rubric_version must be text.');
  run.model_label=run.model_label||(run.kind==='authored'?'Authored example':'Imported model');
  run.rubric_version=run.rubric_version||'imported-unversioned';
  run.turns.forEach((t,i)=>{
    if(t.number!==i+1||typeof t.user!=='string'||typeof t.assistant!=='string')throw Error('Each turn needs a consecutive number, user text and assistant text.');
    if(t.annotations!==undefined&&!Array.isArray(t.annotations))throw Error('annotations must be an array.');
    for(const a of [...(t.annotations||[]),...(t.judge?[t.judge]:[])])if(![1,2,3].includes(a.score))throw Error('Assessment scores must be 1, 2 or 3.');
    if(t.evaluations!==undefined&&(!Array.isArray(t.evaluations)||t.evaluations.some(a=>!['R','H','C','A'].includes(a.dimension)||(![1,2,3].includes(a.score)&&a.score!==null))))throw Error('Configured assessments need valid dimensions and scores.');
    if(t.authored_score!==undefined&&![1,2,3].includes(t.authored_score))throw Error('Authored scores must be 1, 2 or 3.');
  });
  return run;
}
