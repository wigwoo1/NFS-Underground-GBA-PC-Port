import json,re,runpy,sys
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010')
raw=re.findall(r'G:[^\r\n]*owned-native-\d+\.json',(cp/'geometry-9092-profile.log').read_text())[-1]
r=json.loads(Path(raw).read_text());rows=[]
for job in r['world_preparation_stage_samples']:
 d=job['terminal'][5]
 if not d['fine_trace']:continue
 assert d['geometry_input_selected'] and d['cpu_trace'] and d['cycle_trace'] and d['child_gc_trace']['dropped']==0
 first=d['sample_transfer_rows'][0];end=first['ready_ns'];begin=d['constructed_ns'];gc=d['child_gc_trace'];overlap=sum(max(0,min(end,g['end_ns'])-max(begin,g['start_ns'])) for g in gc['rows'])
 stages=d['sample_timings'][0]['source_sample_stages']
 rows.append(dict(older=job['older'],newer=job['newer'],construct_ms=(d['constructed_ns']-d['initialized_ns'])/1e6,construct_cpu_ms=(d['constructed_cpu_ns']-d['initialized_cpu_ns'])/1e6,construct_cycles=d['world_construct_thread_cycles'],first_ready_ms=(end-begin)/1e6,first_gc_overlap_ms=overlap/1e6,first_stages=[dict(name=s['name'],wall_ms=s['wall_ns']/1e6,cpu_ms=s['thread_cpu_ns']/1e6,cycles=s['thread_cycles']) for s in stages if s['name']!='sample_publication']))
assert rows
out=dict(result='PASS_TARGETED_GEOMETRY_CHILD_PROFILE',raw=raw,rows=rows,scope='Completed targeted source pairs; wall and coarse CPU/cycle attribution, publication ack-wait excluded; no guarantee prior stall reproduced.')
(cp/'geometry-9092-profile-audit.json').write_text(json.dumps(out,indent=2));print(out)
sys.argv=['coverage',raw,str(cp/'geometry-9092-profile-coverage.json')];runpy.run_path('work/camera/verify_preclose_native_coverage.py',run_name='__main__')
