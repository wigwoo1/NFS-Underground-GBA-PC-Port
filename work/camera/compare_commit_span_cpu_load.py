"""Weighted accessible-process load over actual commit spans; explicit coverage."""
import json
from pathlib import Path
ledger=Path('work/camera/prototype-runs/process-cpu-load-1791431550248.json');load=json.loads(ledger.read_text(encoding='utf-8-sig'));out={}
for name,n in [('baseline','1791431512020853000'),('candidate','1791431563847273800')]:
 r=json.loads(Path('work/camera/prototype-runs/owned-native-'+n+'.json').read_text());t=[x['native_committed_sample'][6] for x in r['presentation_samples'] if x.get('native_committed_sample')];a,b=min(t),max(t);covered=0;totals={}
 for sample in load['samples']:
  duration=max(0,min(b,sample['end_ns'])-max(a,sample['begin_ns']))
  if not duration:continue
  covered+=duration
  for process in sample['top']:totals[process['name']]=totals.get(process['name'],0)+duration*process['system_capacity_fraction']
 out[name]=dict(coverage_fraction=covered/(b-a),covered_seconds=covered/1e9,mean_recorded_capacity_fraction={k:v/covered for k,v in sorted(totals.items(),key=lambda x:-x[1])[:6]})
result=dict(runs=out,scope='Weighted one-second top12 accessibleprocess observations only; candidate52%coverage; sequential differentload,notcausal cachebenefit or exclusive stall proof.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/cache-load-candidate-20261007/weighted-load-comparison.json').write_text(json.dumps(result,indent=2));print(result)
