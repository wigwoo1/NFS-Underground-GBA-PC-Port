import sys,json,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());groups={k:[] for k in ('pair_take','sample','sky','owned_context','setup_total')};seen=set();slow=[]
for row in r['presentation_samples']:
 p=row['source_setup_profile'];assert p['pair_begin_ns']<=p['pair_take_begin_ns']<=p['pair_ready_ns']<=p['setup_begin_ns']<=p['sample_ready_ns']<=p['sky_ready_ns']<=p['owned_ready_ns']<=row['transaction_begin_ns']
 if p['pair_begin_ns'] not in seen:
  groups['pair_take'].append((p['pair_ready_ns']-p['pair_take_begin_ns'])/1e6);seen.add(p['pair_begin_ns'])
 parts=dict(sample=(p['sample_ready_ns']-p['setup_begin_ns'])/1e6,sky=(p['sky_ready_ns']-p['sample_ready_ns'])/1e6,owned_context=(p['owned_ready_ns']-p['sky_ready_ns'])/1e6,setup_total=(p['owned_ready_ns']-p['setup_begin_ns'])/1e6)
 for name,value in parts.items():groups[name].append(value)
 slow.append(dict(index=row['display_index'],**parts))
result=dict(result='PASS_NATIVE_SOURCE_SETUP_TIMING',stages={},slowest=sorted(slow,key=lambda x:x['setup_total'],reverse=True)[:20],scope='Wall-time setup including scheduling; pair wait counted once per interval; nested setup_total is not additive with substages. No causal GIL or physical cadence proof.')
for name,values in groups.items():
 v=sorted(values);assert v;result['stages'][name]=dict(count=len(v),median_ms=statistics.median(v),p95_ms=v[int(.95*(len(v)-1))],max_ms=v[-1])
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result['stages'],indent=2))
