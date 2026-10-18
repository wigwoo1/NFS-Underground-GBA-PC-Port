"""Summarize immediate preparation stages without summing nested/shared traces."""
import json,sys
from pathlib import Path
from collections import defaultdict
r=json.loads(Path(sys.argv[1]).read_text())
s=r['largest'][0]['preparation_readiness']['stages']
a=defaultdict(float);samples=[]
for sample in s['sample_timings']:
 stages=sample['source_sample_stages']
 for stage in sample['assembly_stages']:a[stage['name']]+=stage['wall_ns']/1e6
 samples.append(dict(alpha=sample['alpha'],wall_ms=sample['wall_ns']/1e6,source_stages=[dict(name=x['name'],ms=x['wall_ns']/1e6) for x in stages],assembly_ms=sum(x['wall_ns'] for x in sample['assembly_stages'])/1e6))
setup=s['sample_timings'][0]['source_setup_stages']
covered=sum(x['wall_ns'] for x in setup)+sum(x['wall_ns'] for x in s['sample_timings'])
assert covered<=s['precompute_ns']
out=dict(result='PASS_IMMEDIATE_STAGE_ACCOUNTING',pair=[s['older'],s['newer']],precompute_ms=s['precompute_ns']/1e6,setup_ms=sum(x['wall_ns'] for x in setup)/1e6,samples=samples,unassigned_precompute_ms=(s['precompute_ns']-covered)/1e6,assembly_totals_ms=sorted(a.items(),key=lambda x:-x[1]),scope='Immediate assembly stages summed once per sample. Nested shared metadata not added. Recorded wall intervals include scheduling and diagnostic overhead; no causal CPU or display claim.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
