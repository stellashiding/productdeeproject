"""Reproduce the local synthetic batch. No external API or model calls."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from deeproject.pipeline import generate, write_batch

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--count', type=int, default=60)
parser.add_argument('--seed', type=int, default=20261102)
parser.add_argument('--out', default=str(ROOT / 'dist/data/pipeline'))
args = parser.parse_args()
template = json.loads((ROOT / 'dist/data/agent-spec.json').read_text())
print(json.dumps(write_batch(generate(template, args.count, args.seed), args.out), indent=2))
