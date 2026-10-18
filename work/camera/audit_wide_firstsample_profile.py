import json,re,statistics
from pathlib import Path
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010');raw=re.findall(r'G:[^\r\n]*owned-native-\d+\.json',(p/'wide-firstsample-profile30.log').read_text())[-1];r=json.loads(Path(raw).read_text());rows=[]
for j in r['world_preparation_stage_samples']:
 t=j['terminal'][5]
 if not t['fine_trace']:continue
 assert t['cpu_trace'] and t['cycle_trace'] and t['child_gc_trace']['dropped']==0 and t['clean_request_close']
 if not t['sample_transfer_rows']:
  assert j['history_only'] and j['prepared_sample_count']==0
  continue
 first=t['sample_transfer_rows'][0];a=t['constructed_ns'];b=first['ready_ns'];assert first['prepare_thread_cycles']>0
 gc=t['child_gc_trace']['rows'];intervals=sorted((max(a,x['start_ns']),min(b,x['end_ns'])) for x in gc if max(a,x['start_ns'])<min(b,x['end_ns']));merged=[]
 for lo,hi in intervals:
  if merged and lo<=merged[-1][1]:merged[-1]=(merged[-1][0],max(hi,merged[-1][1]))
  else:merged.append((lo,hi))
 stages=[]
 for sample in t['sample_timings']:
  if not a<=sample['started_ns']<=b<=sample['completed_ns']:continue
  assert sample['wall_ns']==sample['completed_ns']-sample['started_ns']
  stages.append(dict(wall_ms=sample['wall_ns']/1e6,cycles=sample['thread_cycles'],assembly=[dict(name=x['name'],wall_ms=x['wall_ns']/1e6,cycles=x['thread_cycles']) for x in sample['assembly_stages']],source_stages=[dict(name=x['name'],wall_ms=x['wall_ns']/1e6,cycles=x['thread_cycles']) for x in sample['source_sample_stages']]))
 rows.append(dict(older=j['older'],newer=j['newer'],first_ready_ms=(b-a)/1e6,first_cycles=first['prepare_thread_cycles'],first_cpu_ns=first['prepare_cpu_ns'],gc_overlap_ms=sum(hi-lo for lo,hi in merged)/1e6,gc_generations=[x['generation'] for x in gc if max(a,x['start_ns'])<min(b,x['end_ns'])],samples=stages))
assert len(rows)>50
q=r['shutdown_evidence']['preparation_service_shutdown'];assert not q['child_alive'] and not q['preparation_thread_alive'] and q['child_exitcode']==0 and not q['errors']
out=dict(result='PASS_WIDE_FIRSTSAMPLE_PROFILE_ACCOUNTING',raw=raw,rows=rows,active_intervals=r['live_observation_stats']['whole_run_api_intervals']['all_successful_native_intervals'],scope='Actual range9500..10500 first-ready clocks/cycles and clipped GCunion; fine sample finishes afterpublicationack, source publicationstage includesack and mustnotbe treated as first-readycompute. Timing/profile run can differ from previous; GCoverlap is temporal evidence, not exclusivecause. Coarse CPUtime zero notidle; no60 qualification.')
(p/'wide-firstsample-profile30-audit.json').write_text(json.dumps(out,indent=2));print(out['result']);print('fine jobs',len(rows));print([{k:v for k,v in x.items() if k!='samples'} for x in sorted(rows,key=lambda x:x['first_ready_ms'],reverse=True)[:5]])
