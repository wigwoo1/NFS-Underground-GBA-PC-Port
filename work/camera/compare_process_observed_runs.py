"""Compare complete process-observed live runs with explicit coverage assertions."""
import json,sys
from pathlib import Path
from analyze_active_play_cadence import analyze
runs={}
for name,rp,lp in [('baseline',sys.argv[1],sys.argv[2]),('candidate',sys.argv[3],sys.argv[4])]:
 r=json.loads(Path(rp).read_text());load=json.loads(Path(lp).read_text(encoding='utf-8-sig'));ts=[x['native_committed_sample'][6] for x in r['presentation_samples'] if x.get('native_committed_sample')];a,b=min(ts),max(ts);covered=0;weighted={}
 for sample in load['samples']:
  duration=max(0,min(b,sample['end_ns'])-max(a,sample['begin_ns']))
  if not duration:continue
  covered+=duration
  for p in sample['top']:weighted[p['name']]=weighted.get(p['name'],0)+duration*p['system_capacity_fraction']
 assert covered==b-a,'Missing process observation interval'
 runs[name]=dict(report=rp,coverage_fraction=covered/(b-a),cadence=analyze(r),mean_recorded_cpu_capacity={k:v/covered for k,v in sorted(weighted.items(),key=lambda x:-x[1])[:6]})
result=dict(result='PASS_FULL_OBSERVATION_COMPARISON',runs=runs,scope='Sequential runs with same flags and full one-second CPU observation; top12 accessible processes only. Coarse load similarity not controlled experiment or physical scanout certification.')
Path(sys.argv[5]).write_text(json.dumps(result,indent=2));print({name:dict(max_gap_ms=x['cadence']['active_gap_max_ms'],long_gaps=x['cadence']['active_gaps_over_two_refreshes'],load=x['mean_recorded_cpu_capacity']) for name,x in runs.items()})
