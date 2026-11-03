"""Build a wheel including the exact current viewer; no network installation."""
from pathlib import Path
import shutil
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
shutil.rmtree(root/'build',ignore_errors=True)
viewer=root/'python'/'deeproject'/'viewer'
shutil.rmtree(viewer,ignore_errors=True)
shutil.copytree(root/'dist',viewer,ignore=shutil.ignore_patterns('downloads'))
target=root/'dist'/'downloads'
target.mkdir(exist_ok=True)
subprocess.run([sys.executable,'-m','pip','wheel','--no-index','--no-deps','--no-build-isolation','--wheel-dir',str(target),str(root)],check=True)
print(target/'deeproject_rhca-0.2.0a13-py3-none-any.whl')
