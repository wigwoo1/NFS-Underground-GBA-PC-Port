import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());jobs=[]
def stages(rows):
 out=[]
 for x in rows:
  assert x['started_ns']<=x['completed_ns'] and x['wall_ns']==x['completed_ns']-x['started_ns']
  out.append(dict(name=x['name'],wall_ms=x['wall_ns']/1e6,thread_cpu_ms=None if 'thread_cpu_ns' not in x else x['thread_cpu_ns']/1e6,nested={k:v for k,v in x.items() if k.endswith('_stages')}))
 return out
for p in r['world_preparation_stage_samples']:
 t=p['terminal'][5]
 if not t['fine_trace']:continue
 assert t['sample_timings'] and t['construct_stages']
 first=t['sample_timings'][0]
 jobs.append(dict(source_pair=[p['older'],p['newer']],generation=p['generation'],construct=stages(t['construct_stages']),source_setup=stages(t['source_setup_stages']),first_sample=stages(first['source_sample_stages']),assembly=stages(first['assembly_stages']),first_sample_wall_ms=first['wall_ns']/1e6,first_sample_cpu_ms=first['thread_cpu_ns']/1e6,child_gc=t['child_gc_trace']))
assert jobs
out=dict(result='PASS_TARGETED_CHILD_STAGE_BOUNDARIES',jobs=jobs,scope='Every retained fine-traced job in selected source range; stage wall boundaries verified. Thread CPU timer and nested diagnostics are component evidence, not exclusive scheduling cause or 60fps qualification.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2))
print(json.dumps([dict(pair=x['source_pair'],construct=sorted([(z['name'],round(z['wall_ms'],3)) for z in x['construct']],key=lambda z:z[1],reverse=True)[:3],first_wall_ms=x['first_sample_wall_ms'],first_cpu_ms=x['first_sample_cpu_ms'],assembly=sorted([(z['name'],round(z['wall_ms'],3)) for z in x['assembly']],key=lambda z:z[1],reverse=True)[:3]) for x in jobs]))
