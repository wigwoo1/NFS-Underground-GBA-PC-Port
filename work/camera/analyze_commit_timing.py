"""Separate observed native lock/callback wall durations; no causal GPU claim."""
import json,sys,statistics
from pathlib import Path
p=Path(sys.argv[1]);d=json.loads(p.read_text());rows=[]
for r in d['presentation_samples']:
 t=r.get('native_commit_ticks')
 if t is None:continue
 assert t[5]>0 and t[4]>=sum(t[:4]);stages=[v*1000/t[5] for v in t[:5]]
 native=r.get('native_present_ns');native=None if native is None else native/1e6
 outer=(r['commit_return_ns']-r['present_begin_ns'])/1e6
 assert outer>=0
 rows.append(dict(native_present_callback=bool(r.get('native_present_callback')),refresh=r['refresh'],display_index=r['display_index'],presentation_lock_ms=stages[0],queue_lock_ms=stages[1],validation_ms=stages[2],callback_ms=stages[3],native_commit_ms=stages[4],native_present_ms=native,callback_minus_present_ms=None if native is None else stages[3]-native,outer_minus_commit_ms=outer-stages[4],callback_enter_ns=r['callback_enter_ns'],callback_exit_ns=r['callback_exit_ns']))
assert rows
out=dict(scope='Measured CPU wall durations, Python callback rows include Python entry/return scheduling; direct native callback rows do not; differences alone do not prove GIL or driver causality',count=len(rows),largest_callback_overhead=sorted((r for r in rows if r['callback_minus_present_ms'] is not None),key=lambda r:r['callback_minus_present_ms'],reverse=True)[:10],largest_outer_overhead=sorted(rows,key=lambda r:r['outer_minus_commit_ms'],reverse=True)[:10],lock_max_ms={k:max(r[k] for r in rows) for k in ('presentation_lock_ms','queue_lock_ms')})
p.with_suffix('.commit-timing.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ('largest_callback_overhead','largest_outer_overhead')},indent=2));print(out['largest_callback_overhead'][:2]);print(out['largest_outer_overhead'][:2])
