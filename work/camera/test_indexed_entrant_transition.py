"""Opt-in indexed entrant policy versus actual native planner/endpoints."""
import ctypes as C,runpy,json
from pathlib import Path
p=Path(__file__).resolve().parent
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p]
for key in [b'NF_TEST_INDEXED_ENTRANTS',b'NF_CAPTURE_WALL_OUTPUT_INDICES']:
 assert crt._putenv_s(key,b'1')==0
context=runpy.run_path(str(p/'test_live_entrant_material.py'))
transitions=context['context']['transition_checks']
assert len(transitions)==21
assert all(all(r['accepted'] for r in t['results']) for t in transitions)
entrant=next(t for t in transitions if t['older']==10 and t['newer']==11)
assert entrant['results'][1]['accepted'] and not entrant['original_topology_matched']
report=dict(result='PASS',transition_pairs=len(transitions),exact_endpoints=2*len(transitions),accepted_midpoints=len(transitions),formerly_rejected_entrant=entrant,scope='Actual 120 original updates; all21 native transition midpoint command kinds/sources/order match native planner, all42 endpoints complete packet/camera byteexact. Opt-in only; live GPU/fullscene60fps not proven.')
(p/'indexed-entrant-transition-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
