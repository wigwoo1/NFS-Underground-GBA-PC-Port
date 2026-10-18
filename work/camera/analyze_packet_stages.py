"""Validate deferred packet-stage telemetry against the same live display run."""
import csv,json,statistics,sys
from pathlib import Path
p=Path('work/camera')
rows=list(csv.DictReader((p/'road-attribute-live-parity.csv').open()))
ready={int(r['display_index']):r for r in rows if int(r['ready'])}
trace=list(csv.DictReader((Path(sys.argv[1]) if len(sys.argv)>1 else p/'continuous-packet-stage-trace.csv').open()))
assert len(trace)==len(ready) and len({int(t['display']) for t in trace})==len(trace)
fields=['begin_ns','validated_ns','prepared_ns','metadata_ns','assembled_ns','selected_ns','rendered_ns','released_ns']
labels=['source_validation','pair_prepare_total','world_metadata','model_assembly_pose','layer_selection','legacy_renderer','release_capture']
samples=[]
for t in trace:
 r=ready[int(t['display'])];v=[int(t[k]) for k in fields]
 assert all(a<=b for a,b in zip(v,v[1:]))
 assert int(r['render_start_ns'])<=v[0]<=v[-1]<=int(r['render_end_ns'])
 assert int(t['native_generation_ns'])==int(r['paired_prepare_ns'])
 times={k:(b-a)/1e6 for k,a,b in zip(labels,v,v[1:])}
 times['paired_validation_other']=times['pair_prepare_total']-int(t['native_generation_ns'])/1e6
 assert times['paired_validation_other']>=0
 samples.append(dict(display=int(t['display']),stages_ms=times))
summary={}
for k in samples[0]['stages_ms']:
 values=sorted(s['stages_ms'][k] for s in samples)
 summary[k]=dict(median=statistics.median(values),p95=values[int(.95*len(values))],maximum=max(values))
misses=[]
for previous,row in zip(rows,rows[1:]):
 if int(row['skipped']):
  sample=next((s for s in samples if s['display']==int(previous['display_index'])),None)
  misses.append(dict(display=int(row['display_index']),previous_packet=sample))
report=dict(result='PASS',frames=len(samples),stage_ms=summary,miss_events=misses,scope='Opt-in timestamp telemetry, written after timed loop. Stage timings include OS preemption. Pair total overlaps its native-generation substage; do not sum both. Source validation includes snapshot acquire; model assembly includes pose sampling; release includes optional capture. Not whole-scene fidelity or 60fps proof.')
(p/'continuous-packet-stage-tests.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
