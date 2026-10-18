"""Opt-in child thread CPU accounting; no exclusive scheduler attribution."""
from pathlib import Path
import json,sys,statistics,math,functools
r=json.loads(Path(sys.argv[1]).read_text())
rows=[]
for request in r['world_preparation_stage_samples']:
 d=request['terminal'][5]
 if not d.get('cpu_trace'):continue
 ticks=[d[k] for k in ['child_started_ns','decoded_ns','initialized_ns','constructed_ns']]
 cpus=[d[k] for k in ['child_started_cpu_ns','decoded_cpu_ns','initialized_cpu_ns','constructed_cpu_ns']]
 assert ticks==sorted(ticks) and cpus==sorted(cpus)
 phases={}
 for name,a,b,c,e in zip(['decode','history_initialize','construct'],ticks,ticks[1:],cpus,cpus[1:]):
  wall=b-a;cpu=e-c;assert cpu>=0
  phases[name]=dict(wall_ms=wall/1e6,cpu_ms=cpu/1e6)
 samples=[]
 for s in d['sample_transfer_rows']:
  wall=s['prepare_since_ack_ns'];cpu=s['prepare_cpu_ns'];assert cpu is not None and cpu>=0
  samples.append(dict(index=s['index'],wall_ms=wall/1e6,cpu_ms=cpu/1e6))
 rows.append(dict(started_ns=request['started_ns'],older=request['older'],newer=request['newer'],phases=phases,samples=samples))
assert rows
ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0
long=[]
for event in ledger['records']:
 if event['interval_ns']<=50000000:continue
 old,new=event['transaction']['commit'][2:4];slot=event['caller_stages']['slot_begin_ns']
 matches=[x for x in rows if (x['older'],x['newer'])==(old,new) and x['started_ns']<=slot]
 req=max(matches,key=lambda x:x['started_ns']) if matches else None
 long.append(dict(index=event['display_index'],interval_ms=event['interval_ns']/1e6,request=req))
summary={}
for phase in ['decode','history_initialize','construct','first_source']:
 values=[x['samples'][0] for x in rows if x['samples']] if phase=='first_source' else [x['phases'][phase] for x in rows]
 summary[phase]={name:dict(mean=statistics.mean(v[name] for v in values),median=statistics.median(v[name] for v in values),maximum=max(v[name] for v in values)) for name in ['wall_ms','cpu_ms']}
deltas=[int(v['cpu_ms']*1e6) for row in rows for v in [*row['phases'].values(),*row['samples']] if v['cpu_ms']>0]
quantum=functools.reduce(math.gcd,deltas) if deltas else None
out=dict(result='REJECT_COARSE_CPU_CLOCK_FOR_FINE_ATTRIBUTION' if quantum is None or quantum>=1000000 else 'OBSERVED_CHILD_CPU_PHASES',observed_delta_gcd_ns=quantum,requests=len(rows),summary=summary,long_intervals=long,scope='Thread CPU durations for full request phases, not clipped CPU within caller waits. Wall includes off-CPU scheduling and other elapsed waits; no exclusive OS/GIL cause. Coarse CPU quantization prevents per-request fine attribution; observed delta gcd is evidence from this capture, not an API resolution guarantee. Original game speed tolerance is unchanged.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result']);print(json.dumps(summary,indent=2));print('Long gaps:',len(long))
