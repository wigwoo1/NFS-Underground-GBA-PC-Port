"""Join exact-comparison probes to actual consumer boundary intervals."""
import json,sys,statistics
from pathlib import Path
rp,lp,out=map(Path,sys.argv[1:4]);r=json.loads(rp.read_text());ledger=json.loads(lp.read_text());checks=[]
assert ledger['records'] and ledger['dropped']==0
for x in ledger['records']:
 if x['frame_identity'] is None:continue
 refresh,epoch=x['frame_identity']
 candidates=[b for b in r['consumer_boundary_stage_samples'] if b['refresh']==refresh and b['snapshot_ready_ns']<=x['start_ns']<=x['end_ns']<=b['copied_ns']]
 assert len(candidates)==1,(refresh,epoch,len(candidates))
 b=candidates[0];checks.append(dict(refresh=refresh,epoch=epoch,probe_ms=x['wall_ns']/1e6,probe_cycles=x['thread_cycles'],interval_ms=(b['copied_ns']-b['snapshot_ready_ns'])/1e6,outside_probe_ms=((b['copied_ns']-b['snapshot_ready_ns'])-x['wall_ns'])/1e6,result=x['result'],exception=x['exception'],interval_thread_cpu_ns=None if b['thread_cpu_stamps'] is None else b['thread_cpu_stamps'][3]-b['thread_cpu_stamps'][2]))
assert len(checks)==len(ledger['records']) and all(x['result']==1 and not x['exception'] for x in checks)
result=dict(result='PASS_ATTRIBUTION',calls=len(checks),median_probe_ms=statistics.median(x['probe_ms'] for x in checks),largest_probe_calls=sorted(checks,key=lambda x:x['probe_ms'],reverse=True)[:12],largest_intervals=sorted(checks,key=lambda x:x['interval_ms'],reverse=True)[:12],scope='Probe wall timestamps wholly contained in same refresh consumer compare interval. Cycles are executed work, not elapsed time; diagnostic overhead and scheduling included; no exclusive cause or scanout proof.')
out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('largest_probe_calls','largest_intervals')},indent=2));print(json.dumps(result['largest_intervals'][:3],indent=2))
