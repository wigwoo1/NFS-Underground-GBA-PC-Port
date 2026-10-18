"""Build and test the bounded private-copy cache, without enabling it in gameplay."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

source = Path(__file__).resolve().parent
out = Path(r'C:\NFSUG-Workspace\NFSUG-pc-geometry-cache-tests')
out.mkdir(exist_ok=True)
env = dict(os.environ)
env['PATH'] = 'C:/msys64/mingw64/bin;' + env.get('PATH', '')
gcc = 'C:/msys64/mingw64/bin/gcc.exe'
flags = ['-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-pedantic']
commands = [
    [gcc, *flags, '-c', str(source / 'geometry_packet_cache.c'), '-o', str(out / 'geometry_packet_cache.o')],
    [gcc, *flags, str(source / 'test_geometry_packet_cache.c'), '-o', str(out / 'test_geometry_packet_cache.exe')],
    [str(out / 'test_geometry_packet_cache.exe')],
]
outputs = []
for cmd in commands:
    result = subprocess.run(cmd, env=env, text=True, capture_output=True)
    outputs.append({'command': cmd, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    if result.returncode:
        (out / 'failed-test-log.json').write_text(json.dumps(outputs, indent=2))
        raise RuntimeError(result.stdout + result.stderr)
assert outputs[-1]['stdout'].strip() == 'PASS_GEOMETRY_PACKET_CACHE_OWNERSHIP_BUDGET_FAILURE_LRU'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
report = {
    'result': 'PASS_GEOMETRY_PACKET_CACHE_COMPONENT',
    'commands': outputs,
    'source_sha256': {n: sha(source / n) for n in ['geometry_packet_cache.c', 'geometry_packet_cache.h', 'test_geometry_packet_cache.c', Path(__file__).name]},
    'binary_sha256': sha(out / 'test_geometry_packet_cache.exe'),
    'compiler': subprocess.check_output([gcc, '--version'], env=env, text=True).splitlines()[0],
    'verified': ['independent_output_allocations', 'private_input_copies', 'full_key_and_exact_guard_misses',
                 'failed_output_allocation', 'failed_first_and_second_store_allocations_preserve_entries',
                 'four_entry_lru', 'same_key_guard_replacement', 'byte_budget_eviction', 'exact_and_short_budget',
                 'overflow_rejection', 'clear_and_retained_output_lifetime', 'hard_cap_includes_insertion_staging',
                 'no_leaked_allocations'],
    'runtime_integration_added': False,
    'full_scene_60fps': False,
}
(out / 'geometry-cache-test-report.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != 'commands'}, indent=2))
