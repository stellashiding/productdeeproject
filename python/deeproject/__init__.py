"""Executable specifications with separate generation and assessment records."""
from .engine import validate_specification, evaluate, run_suite, diagnose, compare, write_result
__version__ = '0.2.0a13'
__all__ = ['validate_specification', 'evaluate', 'run_suite', 'diagnose', 'compare', 'write_result']
