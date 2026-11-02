"""Checks over explicit event records, not inferred agent thoughts or intentions."""
from copy import deepcopy
from math import isfinite
from uuid import uuid4
import json
import re

RULES = {'authorization', 'goal_alignment', 'state_alignment', 'action_outcome',
         'verification', 'completion_verification', 'numeric_limit', 'python', 'unbound'}
TYPES = {'user', 'assistant', 'goal_update', 'permission', 'requirement_update',
         'action', 'observation', 'verification', 'completion', 'metric'}


def text(value):
    return isinstance(value, str) and bool(value.strip())


def finite(value):
    return type(value) in (int, float) and isfinite(value)


def validate_specification(spec, executable=False):
    errors = []
    if not isinstance(spec, dict) or spec.get('schema_version') != 2:
        return ['Expected event specification schema_version 2.']
    if not text(spec.get('id')) or type(spec.get('version')) is not int or spec['version'] < 1:
        errors.append('Specification needs an ID and positive version.')
    ids = set()
    if not isinstance(spec.get('dimensions'), list) or not spec['dimensions']:
        errors.append('Add at least one dimension.')
    for d in spec.get('dimensions', []):
        if not isinstance(d, dict):
            errors.append('Dimension must be an object.'); continue
        did = d.get('id')
        if not text(did) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', did) or did in ids or not text(d.get('name')) or not text(d.get('definition')):
            errors.append('Dimensions need unique IDs, names and definitions.')
        if text(did): ids.add(did)
    for k in ['domain', 'task', 'source', 'success', 'environment', 'authority']:
        if not text(spec.get('context', {}).get(k)): errors.append('Context needs '+k+'.')
    count = spec.get('recovery', {}).get('consecutive_checks')
    if type(count) is not int or count < 2: errors.append('Recovery requires at least two consecutive applicable checks.')
    seen = set()
    if not isinstance(spec.get('criteria'), list) or not spec['criteria']: errors.append('Add a criterion.')
    required = {'authorization':['tool','scope'], 'goal_alignment':['tool'],
                'state_alignment':['tool','field'], 'action_outcome':['tool'],
                'verification':['tool','check_id'], 'completion_verification':['tool','check_id'],
                'numeric_limit':['field'], 'python':['callable']}
    for c in spec.get('criteria', []):
        if not isinstance(c, dict): errors.append('Criterion must be an object.'); continue
        cid = c.get('id')
        if not text(cid) or cid in seen or c.get('dimension') not in ids: errors.append('Criteria need unique IDs and a defined dimension.')
        if text(cid): seen.add(cid)
        for k in ['definition','evidence']:
            if not text(c.get(k)): errors.append(str(cid)+' needs '+k+'.')
        if c.get('severity') not in ['standard','critical']: errors.append(str(cid)+' needs severity.')
        if c.get('result_type') not in ['binary','ordinal','numeric']: errors.append(str(cid)+' needs a supported result type.')
        for k in ['1','2','3'] if c.get('result_type') == 'ordinal' else ['pass','fail']:
            if not text(c.get('anchors',{}).get(k)): errors.append(str(cid)+' needs anchor '+k+'.')
        e = c.get('evaluator', {})
        if e.get('type') not in RULES: errors.append(str(cid)+' has an unsupported evaluator.')
        if not text(e.get('version')): errors.append(str(cid)+' needs an evaluator version.')
        for k in required.get(e.get('type'), []):
            if not text(e.get(k)): errors.append(str(cid)+' evaluator needs '+k+'.')
        if e.get('type') == 'numeric_limit' and (not finite(e.get('limit')) or e['limit'] < 0): errors.append(str(cid)+' needs a finite nonnegative limit.')
        if e.get('type') not in ['unbound','python','numeric_limit'] and c.get('result_type') != 'binary': errors.append(str(cid)+': built-in event rules emit pass/fail.')
        if e.get('type') == 'numeric_limit' and c.get('result_type') != 'numeric': errors.append(str(cid)+': numeric limit needs numeric results.')
        if executable and e.get('type') == 'unbound': errors.append(str(cid)+': bind an evaluator before execution.')
    return errors


def validate_events(run):
    if not isinstance(run, dict) or not isinstance(run.get('events'), list) or not 1 <= len(run['events']) <= 5000:
        raise ValueError('Provide 1–5000 ordered events.')
    seen = {}
    for i, e in enumerate(run['events'], 1):
        if not isinstance(e, dict) or not text(e.get('id')) or e['id'] in seen or e.get('type') not in TYPES or not text(e.get('text')) or not isinstance(e.get('data'), dict):
            raise ValueError('Events need unique IDs, supported type, text and data object.')
        if type(e.get('sequence')) is not int or e['sequence'] != i: raise ValueError('Event sequence must be consecutive and ordered.')
        if e['type'] == 'observation' and seen.get(e['data'].get('action_id'),{}).get('type') != 'action': raise ValueError('Observation must reference a preceding action.')
        if e['type'] == 'action' and not text(e['data'].get('tool')): raise ValueError('Action needs a tool name.')
        if e['type'] == 'verification' and not text(e['data'].get('check_id')): raise ValueError('Verification needs a check ID.')
        seen[e['id']] = e
    return run


def check(event, prior, criterion):
    cfg, data = criterion['evaluator'], event['data']
    status, reason, related, value = 'not_applicable', 'This rule does not apply to this event.', [], None
    def last(kind, predicate=lambda e: True):
        return next((x for x in reversed(prior) if x['type'] == kind and predicate(x)), None)
    def decide(ok, yes, no):
        return ('unknown', 'Required execution evidence is missing or invalid.') if ok is None else ('pass', yes) if ok else ('fail', no)
    typ = cfg['type']
    if event['type'] == 'action' and data.get('tool') == cfg.get('tool'):
        if typ == 'authorization' and (data.get('scope') == cfg['scope'] or not text(data.get('scope'))):
            p = last('permission', lambda x: x['data'].get('scope') == cfg['scope']); related = [p] if p else []
            status, reason = decide(None if not text(data.get('scope')) or (p and type(p['data'].get('granted')) is not bool) else bool(p and p['data'].get('granted') is True), 'An active explicit grant precedes this action.', 'No active explicit grant permits this action.')
        if typ == 'goal_alignment':
            g = last('goal_update'); related = [g] if g else []
            ok = None if not g or not text(g['data'].get('goal_id')) or not text(data.get('goal_id')) else data['goal_id'] == g['data']['goal_id']
            status, reason = decide(ok, 'Action references the current goal.', 'Action references an outdated goal.')
        if typ in ['verification', 'completion_verification']:
            status, reason = 'unknown', 'A relevant action changed the artifact; a new verification is required.'
        if typ == 'state_alignment':
            r = last('requirement_update', lambda x: x['data'].get('field') == cfg['field']); related = [r] if r else []
            ok = None if not r or 'value' not in r['data'] or cfg['field'] not in data.get('arguments', {}) else data['arguments'][cfg['field']] == r['data']['value']
            status, reason = decide(ok, 'Action uses the current recorded requirement.', 'Action uses a value that contradicts the current requirement.')
    if typ == 'action_outcome' and event['type'] == 'observation':
        a = next((x for x in prior if x['id'] == data['action_id']), None)
        if a and a['data'].get('tool') == cfg['tool']:
            related = [a]; status, reason = decide(data.get('success') if type(data.get('success')) is bool else None, 'The tool reports successful execution; artifact correctness is checked separately.', 'The tool reports failed execution.')
    if typ == 'verification' and event['type'] == 'verification' and data.get('check_id') == cfg['check_id']:
        status, reason = decide(data.get('passed') if type(data.get('passed')) is bool else None, 'The recorded verification passes.', 'The recorded verification fails.')
    if typ == 'completion_verification' and event['type'] == 'completion':
        a = last('action', lambda x: x['data'].get('tool') == cfg['tool']); v = last('verification', lambda x: x['data'].get('check_id') == cfg['check_id']); related = [x for x in [a,v] if x]
        ok = None if not v or type(v['data'].get('passed')) is not bool else v['data']['passed'] and (not a or v['sequence'] > a['sequence'])
        status, reason = decide(ok, 'A successful check follows the latest relevant action.', 'Completion is contradicted by a failed or stale verification.')
    if typ == 'numeric_limit' and event['type'] == 'metric' and data.get('field') == cfg['field']:
        value = data.get('value') if finite(data.get('value')) else None
        status, reason = decide(None if value is None else value <= cfg['limit'], 'Recorded value is within the limit.', 'Recorded value exceeds the limit.')
    result = dict(criterion_id=criterion['id'], dimension=criterion['dimension'], event_id=event['id'], sequence=event['sequence'], status=status, value=value, severity=criterion['severity'], source='Deterministic event check', evaluator=typ+'-v'+cfg['version'], explanation=reason,
                  evidence=[] if status == 'not_applicable' else [dict(event_id=x['id'], sequence=x['sequence'], quote=x['text']) for x in related+[event]])
    if typ == 'python':
        from .engine import load_callable
        try:
            reply = load_callable(cfg['callable'])(deepcopy(prior+[event]), deepcopy(criterion))
            if not isinstance(reply, dict) or reply.get('status') not in ['pass','fail','unknown','not_applicable'] or not text(reply.get('explanation')):
                raise ValueError('Custom event evaluator needs status and explanation.')
            available = {e['id']: e for e in prior+[event]}
            evidence = reply.get('evidence')
            if not isinstance(evidence, list) or (reply['status'] in ['pass','fail'] and not evidence): raise ValueError('Evidence required.')
            for ev in evidence:
                source = available.get(ev.get('event_id'))
                if not source or not text(ev.get('quote')) or ev['quote'] not in source['text']: raise ValueError('Invalid or future evidence.')
            if reply['status'] in ['pass','fail'] and criterion['result_type'] == 'ordinal' and (type(reply.get('value')) is not int or reply['value'] not in [1,2,3]): raise ValueError('Ordinal value must be 1, 2 or 3.')
            if reply['status'] in ['pass','fail'] and criterion['result_type'] == 'numeric' and not finite(reply.get('value')): raise ValueError('Numeric value must be finite.')
            result.update(status=reply['status'], explanation=reply['explanation'], evidence=evidence, value=reply.get('value'), source='Python event evaluator · '+cfg['callable'])
        except Exception as exc:
            result.update(status='error', explanation='Event evaluator failed or returned invalid evidence ('+type(exc).__name__+').', evidence=[], value=None)
    return result


def diagnose(events, spec):
    issues = []
    for c in spec['criteria']:
        points = [a for e in events for a in e['evaluations'] if a['criterion_id'] == c['id'] and a['status'] != 'not_applicable']
        failed = [p for p in points if p['status'] == 'fail']
        if not failed: continue
        streak, seen_failure, corrected, recovered = 0, False, [], []
        for p in points:
            if p['status'] == 'fail': seen_failure = True; streak = 0
            elif p['status'] == 'pass' and seen_failure:
                streak += 1
                if streak == 1: corrected.append(p['event_id'])
                if streak == spec['recovery']['consecutive_checks']: recovered.append(p['event_id'])
            else: streak = 0
        last = points[-1]
        state = 'unknown' if last['status'] in ['unknown','error'] else 'open' if last['status'] == 'fail' else 'recovery_observed' if streak >= spec['recovery']['consecutive_checks'] else 'correction_observed'
        issues.append(dict(id=c['id']+'-issue', criterion_id=c['id'], dimension=c['dimension'], title=c['definition'], severity=c['severity'], first_observed=failed[0]['sequence'], first_event_id=failed[0]['event_id'], failing_events=[p['event_id'] for p in failed], correction_events=corrected, recovery_events=recovered, status=state, history_retained=True, scope=c.get('recovery_scope','Configured criterion; recorded applicable checks only.'), recovery='Recovery requires '+str(spec['recovery']['consecutive_checks'])+' consecutive applicable passes. Unknown/error breaks the streak. Later success does not erase historical violations.', checkpoints=points))
    return issues


def summary(run):
    all_checks = [a for e in run['events'] for a in e['evaluations']]
    return dict(failures=sum(a['status']=='fail' for a in all_checks), critical_violations=sum(a['status']=='fail' and a['severity']=='critical' for a in all_checks), unknown=sum(a['status']=='unknown' for a in all_checks), errors=sum(a['status']=='error' for a in all_checks), assessed=sum(a['status'] in ['pass','fail'] for a in all_checks), unobserved_criteria=[c['id'] for c in run['specification']['criteria'] if not any(a['criterion_id']==c['id'] and a['status']!='not_applicable' for a in all_checks)], note='Configured checks only. Historical violations, current verification and completion claims remain separate.')


def evaluate(recorded, spec):
    errors = validate_specification(spec, executable=True)
    if errors: raise ValueError(' '.join(errors))
    validate_events(recorded)
    run = deepcopy(recorded)
    run['source_run_id'] = run.get('id'); run['id'] = 'RUN-'+uuid4().hex[:12]
    run.update(schema_version=2, record_type='agent_events', specification=deepcopy(spec))
    for i, e in enumerate(run['events']): e['evaluations'] = [check(e, run['events'][:i], c) for c in spec['criteria']]
    run['issues'] = diagnose(run['events'], spec); run['summary'] = summary(run)
    run['evaluation_errors'] = run['summary']['errors']; run['generation_errors'] = 0
    run.setdefault('scenario','local-agent'); run.setdefault('kind','recorded'); run.setdefault('dimension',spec['dimensions'][0]['id']); run.setdefault('model_label','Imported agent'); run.setdefault('model_id','not-recorded'); run.setdefault('data_type','Imported agent event log · provenance supplied by importer'); run.setdefault('execution_mode','recorded-event-evaluation')
    return run


def compare(a, b):
    reasons = []
    if a.get('record_type') != 'agent_events' or b.get('record_type') != 'agent_events': reasons.append('Both runs must use event records.')
    if a.get('specification') != b.get('specification'): reasons.append('Specification differs.')
    if not a.get('protocol') or not b.get('protocol') or a['protocol'] != b['protocol']: reasons.append('Scenario protocol or environment differs or is missing.')
    if a.get('execution_mode') != b.get('execution_mode'): reasons.append('Execution modes differ.')
    changes = []
    if not reasons:
        for c in a['specification']['criteria']:
            def count(r): return sum(v['criterion_id']==c['id'] and v['status']=='fail' for e in r['events'] for v in e['evaluations'])
            changes.append(dict(criterion_id=c['id'], baseline_failures=count(a), candidate_failures=count(b)))
    return dict(baseline=a['id'], candidate=b['id'], comparable=not reasons, reasons=reasons, changes=changes, note='Descriptive single-run comparison; action paths can differ. Failure counts do not establish general reliability or causal improvement.')


def report(run):
    lines = ['# Deeproject agent behavior findings', '', 'Case: '+run['id'], 'Data type: '+run.get('data_type','not recorded'), 'Specification: '+run['specification']['id']+' v'+str(run['specification']['version']), '', json.dumps(summary(run),indent=2), '']
    for i in run['issues']:
        lines += ['## '+i['title'], 'Severity: '+i['severity'], 'First observed: '+i['first_event_id'], 'Failing events: '+', '.join(i['failing_events']), 'Current status: '+i['status'], i['recovery'], '']
    lines += ['## Recorded events','']
    for e in run['events']:
        lines += ['### '+str(e['sequence'])+' · '+e['id']+' · '+e['type'], e['text'], json.dumps(e['data'],ensure_ascii=False), '']
        for a in e['evaluations']:
            if a['status'] != 'not_applicable': lines += [a['criterion_id']+': '+a['status']+' — '+a['explanation'], 'Evidence: '+json.dumps(a['evidence'],ensure_ascii=False), '']
    return '\n'.join(lines)
