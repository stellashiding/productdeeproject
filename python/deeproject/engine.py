"""Standard-library harness. Exact checks do not establish semantic correctness."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import importlib
import json
import os
import urllib.request


def validate_specification(spec, executable=False):
    if isinstance(spec, dict) and spec.get('schema_version') == 2:
        from .agent import validate_specification as validate_agent
        return validate_agent(spec, executable)
    errors = []
    text = lambda v: isinstance(v, str) and bool(v.strip())
    if not isinstance(spec, dict):
        return ['Provide a specification object.']
    if spec.get('schema_version') != 1:
        errors.append('schema_version must be 1.')
    if not text(spec.get('id')) or type(spec.get('version')) is not int or spec['version'] < 1:
        errors.append('A specification needs an ID and positive integer version.')
    for key in ['domain', 'task', 'source']:
        if not text(spec.get('context', {}).get(key)):
            errors.append('Context needs ' + key + '.')
    if not isinstance(spec.get('criteria'), list) or not spec['criteria']:
        return errors + ['Add at least one criterion.']
    seen = set()
    for c in spec['criteria']:
        if not isinstance(c, dict):
            errors.append('Each criterion must be an object.')
            continue
        cid = c.get('id')
        if not text(cid) or cid in seen:
            errors.append('Criterion IDs must be nonempty and unique.')
        if isinstance(cid, str):
            seen.add(cid)
        if c.get('dimension') not in ['R', 'H', 'C', 'A']:
            errors.append('Choose an RHCA dimension.')
        for key in ['definition', 'evidence']:
            if not text(c.get(key)):
                errors.append(str(cid) + ' needs ' + key + '.')
        for key in ['1', '2', '3']:
            if not text(c.get('anchors', {}).get(key)):
                errors.append(str(cid) + ' needs rating anchor ' + key + '.')
        a = c.get('applicability', {})
        start, end = a.get('from_turn'), a.get('to_turn')
        if type(start) is not int or start < 1 or (end is not None and (type(end) is not int or type(start) is not int or end < start)):
            errors.append(str(cid) + ' needs a valid turn range.')
        e = c.get('evaluator', {})
        if e.get('type') not in ['required_phrase', 'python', 'unbound']:
            errors.append(str(cid) + ' has an unknown evaluator binding.')
        if e.get('type') == 'required_phrase' and not text(e.get('phrase')):
            errors.append(str(cid) + ' needs required text.')
        if e.get('type') == 'python' and not text(e.get('callable')):
            errors.append(str(cid) + ' needs a Python evaluator callable.')
        if executable and e.get('type') == 'unbound':
            errors.append(str(cid) + ' needs an evaluator before execution.')
    return errors


def load_callable(reference):
    module, separator, name = reference.partition(':')
    if not separator or not module or not name:
        raise ValueError('Use a Python callable reference such as my_app:reply.')
    fn = getattr(importlib.import_module(module), name)
    if not callable(fn):
        raise ValueError('The referenced object is not callable.')
    return fn


def _check(turns, spec):
    evaluated = deepcopy(turns)
    for index, turn in enumerate(evaluated):
        turn['number'] = index + 1
        turn['evaluations'] = []
        for c in spec['criteria']:
            n = index + 1
            item = dict(criterion_id=c['id'], dimension=c['dimension'], score=None,
                        status='unknown', evidence=[], source='Configured evaluator')
            a, e = c['applicability'], c['evaluator']
            if n < a['from_turn'] or (a['to_turn'] is not None and n > a['to_turn']):
                item.update(status='not_applicable', explanation='Outside the configured turn range.')
            elif turn.get('generation_error'):
                item.update(status='error', explanation='Target execution failed; no assessment.')
            else:
                try:
                    if e['type'] == 'required_phrase':
                        phrase, body = e['phrase'], turn['assistant']
                        if e.get('case_sensitive', False):
                            offset = body.find(phrase)
                        else:
                            offset = body.lower().find(phrase.lower())
                        ok = offset >= 0
                        item.update(score=3 if ok else 1, status='meets' if ok else 'fails',
                                    source='Deterministic exact-text check', evaluator='required_phrase-v1',
                                    explanation='Required text is present.' if ok else 'Required text is absent from the complete assistant message.',
                                    evidence=[dict(turn=n, role='assistant', quote=body[offset:offset+len(phrase)] if ok else None,
                                                   scope='matched text' if ok else 'complete message checked')])
                    else:
                        reply = load_callable(e['callable'])(deepcopy(evaluated[:n]), deepcopy(c))
                        if not isinstance(reply, dict) or type(reply.get('score')) is not int or reply['score'] not in [1, 2, 3]:
                            raise ValueError('Evaluator must return score 1, 2 or 3.')
                        if not isinstance(reply.get('explanation'), str) or not reply['explanation'].strip():
                            raise ValueError('Evaluator needs an explanation.')
                        if not isinstance(reply.get('evidence'), list) or not reply['evidence']:
                            raise ValueError('Evaluator needs evidence references.')
                        for ev in reply['evidence']:
                            tnum, role, quote = ev.get('turn'), ev.get('role'), ev.get('quote')
                            if type(tnum) is not int or not 1 <= tnum <= n or role not in ['user', 'assistant']:
                                raise ValueError('Evidence references an unavailable message.')
                            if not isinstance(quote, str) or not quote or quote not in evaluated[tnum-1][role]:
                                raise ValueError('Evidence quote must occur in the referenced message.')
                        item.update(score=reply['score'], status={1:'fails', 2:'partial', 3:'meets'}[reply['score']],
                                    explanation=reply['explanation'], evidence=reply['evidence'],
                                    source='Python evaluator · ' + e['callable'], evaluator=e.get('version', 'unversioned'))
                except Exception as exc:
                    # Do not serialize arbitrary provider errors: they may contain credentials.
                    item.update(status='error', explanation='Evaluator failed or returned invalid evidence (' + type(exc).__name__ + ').')
            turn['evaluations'].append(item)
    return evaluated


def diagnose(turns, spec):
    issues = []
    for c in spec['criteria']:
        points = [dict(turn=t['number'], **next((a for a in t.get('evaluations', []) if a['criterion_id'] == c['id']), {})) for t in turns]
        bad = [a for a in points if a.get('score') in [1, 2]]
        if not bad:
            continue
        onset = bad[0]['turn']
        after = [a for a in points if a['turn'] >= onset]
        corrections = [a['turn'] for a in after if a.get('score') == 3 and any(b['turn'] < a['turn'] and b.get('score') in [1,2] for b in after)]
        last = after[-1].get('score')
        issues.append(dict(id=c['id']+'-issue', criterion_id=c['id'], dimension=c['dimension'], title=c['definition'],
                           first_observed=onset, failing_turns=[a['turn'] for a in bad], correction_turns=corrections,
                           status='correction_observed' if last == 3 else 'unknown' if last is None else 'open',
                           recovery='Not established; no sustained-recovery protocol is configured.',
                           checkpoints=[dict(turn=a['turn'], score=a.get('score'), status=a.get('status','unknown'), evidence=a.get('evidence',[])) for a in after],
                           source='Configured check results; no causal inference'))
    return issues


def evaluate(recorded, spec):
    if spec.get('schema_version') == 2:
        from .agent import evaluate as evaluate_agent
        return evaluate_agent(recorded, spec)
    errors = validate_specification(spec, executable=True)
    if errors:
        raise ValueError(' '.join(errors))
    if not isinstance(recorded, dict) or not isinstance(recorded.get('turns'), list) or not recorded['turns']:
        raise ValueError('A recorded case needs a nonempty turns array.')
    for t in recorded['turns']:
        if not isinstance(t, dict) or not isinstance(t.get('user'), str) or not isinstance(t.get('assistant'), str):
            raise ValueError('Every turn needs user and assistant text.')
    result = deepcopy(recorded)
    result['id'] = 'RUN-' + uuid4().hex[:12]
    result['source_run_id'] = recorded.get('id')
    result.update(schema_version=1, dimension=spec['criteria'][0]['dimension'], specification=deepcopy(spec),
                  rubric_version=spec['id']+'-v'+str(spec['version']), rubric=spec['criteria'][0]['definition'],
                  execution_mode=recorded.get('execution_mode','recorded-log-evaluation'),
                  run_date=datetime.now(timezone.utc).isoformat())
    result.setdefault('scenario', 'local')
    result.setdefault('kind', 'recorded')
    result.setdefault('model_label', 'Local target')
    result.setdefault('model_id', 'custom/unspecified')
    result['turns'] = _check(recorded['turns'], spec)
    result['issues'] = diagnose(result['turns'], spec)
    result['evaluation_errors'] = sum(a['status'] == 'error' for t in result['turns'] if not t.get('generation_error') for a in t['evaluations'])
    result['generation_errors'] = sum(bool(t.get('generation_error')) for t in result['turns'])
    return result


def run_suite(suite, spec, target, target_id='custom/application', fixture=False):
    if not isinstance(suite, dict) or not isinstance(suite.get('messages'), list) or not suite['messages'] or not all(isinstance(s,str) for s in suite['messages']):
        raise ValueError('A suite needs a nonempty messages array of user strings.')
    errors = validate_specification(spec, executable=True)
    if errors:
        raise ValueError(' '.join(errors))
    messages, turns = [], []
    for n, user in enumerate(suite['messages'], 1):
        messages.append({'role':'user', 'content':user})
        try:
            output = target(deepcopy(messages))
            if not isinstance(output, str):
                raise ValueError('Target must return assistant text.')
        except Exception as exc:
            turns.append(dict(number=n, user=user, assistant='', generation_error=type(exc).__name__))
            break  # no implicit retries or continuing a corrupted conversation
        turns.append(dict(number=n, user=user, assistant=output))
        messages.append({'role':'assistant', 'content':output})
    return evaluate(dict(id=suite.get('id','suite'), scenario='local', kind='recorded', turns=turns,
                         fixture=fixture, data_type='Synthetic fixture execution' if fixture else 'Recorded target execution',
                         model_label=target_id, model_id=target_id, execution_mode='fixed-script',
                         suite_version=suite.get('version',1), planned_turns=len(suite['messages']),
                         execution_status='partial_failure' if turns[-1].get('generation_error') else 'completed'), spec)


def http_target(url, timeout=60):
    if not url.startswith(('https://','http://')):
        raise ValueError('HTTP targets need an http(s) URL.')
    def call(messages):
        headers = {'Content-Type':'application/json'}
        token = os.environ.get('DEEPROJECT_TARGET_TOKEN')
        if token:
            headers['Authorization'] = 'Bearer ' + token
        req = urllib.request.Request(url, data=json.dumps({'messages':messages}).encode(), headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.load(response)
        if not isinstance(payload.get('assistant'), str):
            raise ValueError('HTTP endpoint must return {"assistant": "..."}.')
        return payload['assistant']
    return call


def compare(a, b):
    if a.get('record_type') == 'agent_events' or b.get('record_type') == 'agent_events':
        from .agent import compare as compare_agent
        return compare_agent(a, b)
    reasons = []
    sa, sb = a.get('specification'), b.get('specification')
    if not sa or not sb:
        reasons.append('Both runs need executable specifications.')
    elif any(sa.get(k) != sb.get(k) for k in ['id','version','criteria']):
        reasons.append('Specification or evaluator version differs.')
    if [t['user'] for t in a['turns']] != [t['user'] for t in b['turns']]:
        reasons.append('Scenario inputs differ.')
    if a.get('execution_mode') != b.get('execution_mode'):
        reasons.append('Execution modes differ.')
    result = dict(baseline=a['id'], candidate=b['id'], comparable=not reasons, reasons=reasons, changes=[])
    if reasons:
        return result
    for c in sa['criteria']:
        aa = {t['number']:next((v for v in t.get('evaluations',[]) if v['criterion_id']==c['id']),{}) for t in a['turns']}
        for t in b['turns']:
            x = aa.get(t['number'],{}).get('score')
            y = next((v for v in t.get('evaluations',[]) if v['criterion_id']==c['id']),{}).get('score')
            if x != y:
                result['changes'].append(dict(criterion_id=c['id'], turn=t['number'], baseline=x, candidate=y,
                                              change='unknown' if x is None or y is None else 'improved checkpoint' if y>x else 'regressed checkpoint'))
    result['note'] = 'Single-run comparison; checkpoint improvement does not establish sustained recovery.'
    return result


def report(run):
    if run.get('record_type') == 'agent_events':
        from .agent import report as report_agent
        return report_agent(run)
    lines = ['# Deeproject findings', '', 'Case: '+run['id'], 'Target: '+run.get('model_id','not recorded'),
             'Specification: '+run['specification']['id']+' v'+str(run['specification']['version']), '']
    for i in run['issues']:
        lines += ['## '+i['title'], '', 'First observed: turn '+str(i['first_observed']),
                  'Failing checkpoints: '+', '.join(map(str,i['failing_turns'])),
                  'Correction checkpoints: '+(', '.join(map(str,i['correction_turns'])) or 'none'), i['recovery'], '']
    lines += ['Evaluation errors: '+str(run.get('evaluation_errors',0)),
              'Only configured checks were executed; no general quality or safety guarantee.', '', '## Original conversation', '']
    for t in run['turns']:
        lines += ['### Turn '+str(t['number']), '', '**User**', t['user'], '', '**Assistant**', t['assistant'], '']
        for a in t['evaluations']:
            lines += [a['criterion_id']+': '+a['status']+' — '+a.get('explanation',''), 'Evidence: '+json.dumps(a['evidence'],ensure_ascii=False), '']
    return '\n'.join(lines)


def write_result(run, directory):
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    (root/'result.json').write_text(json.dumps(run,ensure_ascii=False,indent=2,allow_nan=False)+'\n', encoding='utf-8')
    (root/'report.md').write_text(report(run), encoding='utf-8')
    return root
