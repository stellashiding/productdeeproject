import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
import tempfile
import webbrowser
from .engine import validate_specification, evaluate, run_suite, compare, write_result, load_callable, http_target


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Design specifications, run multi-turn checks, inspect evidence.')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('btv', help='Compute paper Eq. (1) from supplied complete RHCA anchors.')
    p.add_argument('ratings'); p.add_argument('--out')
    p = sub.add_parser('pipeline', help='Evaluate and route a batch locally; no model calls.')
    p.add_argument('--input'); p.add_argument('--template'); p.add_argument('--count', type=int, default=60)
    p.add_argument('--controlled', action='store_true', help='Use controlled BTV rating sequences, with no semantic judge.')
    p.add_argument('--seed', type=int, default=20261102); p.add_argument('--out', required=True)
    p = sub.add_parser('init', help='Write an Atlas fixture specification, suite and target module.')
    p.add_argument('directory', nargs='?', default='deeproject-example')
    p.add_argument('--profile', choices=['rhca','agent'], default='rhca')
    p = sub.add_parser('validate'); p.add_argument('spec'); p.add_argument('--executable', action='store_true')
    p = sub.add_parser('evaluate'); p.add_argument('recorded'); p.add_argument('--spec', required=True); p.add_argument('--out', required=True)
    p = sub.add_parser('run'); p.add_argument('suite'); p.add_argument('--spec',required=True); p.add_argument('--target',required=True); p.add_argument('--target-id'); p.add_argument('--fixture',action='store_true',help='Label a synthetic fixture target.'); p.add_argument('--timeout',type=float,default=60); p.add_argument('--out',required=True)
    p = sub.add_parser('compare'); p.add_argument('baseline'); p.add_argument('candidate'); p.add_argument('--out')
    p = sub.add_parser('view'); p.add_argument('result', nargs='?'); p.add_argument('--port',type=int,default=8765); p.add_argument('--no-browser',action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'btv':
            from .btv import verify
            output = json.dumps(verify(read(args.ratings)), indent=2)
            if args.out: Path(args.out).write_text(output + '\n', encoding='utf-8')
            print(output)
        elif args.command == 'pipeline':
            from .pipeline import generate, write_batch
            if args.input and args.controlled:
                raise ValueError('Choose --input or --controlled, not both.')
            if args.input:
                records = read(args.input)
            else:
                template = Path(args.template) if args.template else Path(__file__).parent / 'viewer' / 'data' / 'agent-spec.json'
                if args.controlled:
                    from .stress import controlled_cases
                    records = controlled_cases(read(template))
                else:
                    records = generate(read(template), args.count, args.seed)
            print(json.dumps(write_batch(records, args.out), indent=2))
        elif args.command == 'init':
            root=Path(args.directory); root.mkdir(parents=True,exist_ok=True)
            source=Path(__file__).parent/'viewer'/'data'
            if args.profile == 'agent':
                for name in ['spec.json','events.json','reference-events.json']:
                    if (root/name).exists(): raise ValueError('Choose an empty example directory.')
                for src,dest in [('agent-spec.json','spec.json'),('agent-violation.json','events.json'),('agent-reference.json','reference-events.json')]:
                    shutil.copyfile(source/src,root/dest)
                print('Created author-constructed agent event fixtures; no model run.'); return 0
            for name in ['spec.json','suite.json','example_target.py']:
                dest=root/name
                if dest.exists():
                    raise ValueError(str(dest)+' already exists; choose another directory.')
            source=Path(__file__).parent/'viewer'/'data'
            shutil.copyfile(source/'fixture-spec.json',root/'spec.json')
            shutil.copyfile(source/'fixture-suite.json',root/'suite.json')
            (root/'example_target.py').write_text('"""Synthetic fixture. Replace reply with your own application call."""\ndef reply(messages):\n    return "Atlas: " + messages[-1]["content"]\n',encoding='utf-8')
            print('Created '+str(root)+'. This example target is synthetic, not a model.')
        elif args.command == 'validate':
            errors=validate_specification(read(args.spec), executable=args.executable)
            if errors:
                print('\n'.join(errors),file=sys.stderr); return 2
            print('Specification valid. Completeness does not establish semantic correctness.')
        elif args.command in ['run','evaluate']:
            if args.command == 'run':
                if args.timeout <= 0:
                    raise ValueError('timeout must be positive.')
                sys.path.insert(0,str(Path.cwd()))
                target=http_target(args.target,args.timeout) if args.target.startswith(('https://','http://')) else load_callable(args.target)
                run=run_suite(read(args.suite),read(args.spec),target,args.target_id or ('custom/http-endpoint' if args.target.startswith(('https://','http://')) else args.target),fixture=args.fixture)
                if args.fixture:
                    run.update(fixture=True,data_type='Synthetic fixture execution',family='fixture',model_label='Reference fixture')
            else:
                sys.path.insert(0,str(Path.cwd()))
                run=evaluate(read(args.recorded),read(args.spec))
            write_result(run,args.out)
            print(str(Path(args.out)/'result.json'))
            print(str(len(run['issues']))+' issue(s); '+str(run['evaluation_errors'])+' evaluation error(s); '+str(run.get('generation_errors',0))+' generation error(s).')
            return 1 if run.get('evaluation_errors') or run.get('execution_status')=='partial_failure' else 0
        elif args.command == 'compare':
            def result(path):
                p=Path(path); return read(p/'result.json' if p.is_dir() else p)
            output=compare(result(args.baseline),result(args.candidate))
            serialized=json.dumps(output,ensure_ascii=False,indent=2)
            if args.out:
                Path(args.out).write_text(serialized+'\n',encoding='utf-8')
            print(serialized)
            return 0 if output['comparable'] else 2
        elif args.command == 'view':
            with tempfile.TemporaryDirectory(prefix='deeproject-view-') as tmp:
                shutil.copytree(Path(__file__).parent/'viewer',tmp,dirs_exist_ok=True)
                index=read(Path(tmp)/'data'/'index.json')
                index['runtime']={'mode':'local','version':'0.2.0a13'}
                if args.result:
                    p=Path(args.result); run=read(p/'result.json' if p.is_dir() else p)
                    (Path(tmp)/'data'/'local-result.json').write_text(json.dumps(run),encoding='utf-8')
                    index['scenarios'].append(dict(id=run['scenario'],name='Local execution',description='Results from your local harness.',goal='Inspect configured checks and original messages.',constraints=[])) if not any(s['id']==run['scenario'] for s in index['scenarios']) else None
                    index['runs'].append(dict(id=run['id'],scenario=run['scenario'],kind=run['kind'],dimension=run['dimension'],record_type=run.get('record_type'),configured=True,issue_count=len(run.get('issues',[])),first_issue_turn=(run.get('issues') or [{}])[0].get('first_observed'),family=run.get('family'),model_label=run['model_label'],model_id=run['model_id'],turn_count=len(run.get('events',run.get('turns',[]))),human_count=0,path='data/local-result.json'))
                    (Path(tmp)/'data'/'index.json').write_text(json.dumps(index),encoding='utf-8')
                    start='/#diagnostics?run='+run['id']+'&turn=1&dim='+run['dimension']
                else:
                    start='/#design'
                (Path(tmp)/'data'/'index.json').write_text(json.dumps(index),encoding='utf-8')
                server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(SimpleHTTPRequestHandler,directory=tmp))
                url='http://127.0.0.1:'+str(server.server_port)+start
                print(url,flush=True)
                if not args.no_browser: webbrowser.open(url)
                try: server.serve_forever()
                except KeyboardInterrupt: pass
                finally: server.server_close()
        return 0
    except Exception as exc:
        # Exception text from third-party targets can contain secrets.
        print('Operation failed ('+type(exc).__name__+'). Check input paths, specification, and target configuration.',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
