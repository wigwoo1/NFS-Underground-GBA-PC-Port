"""Measure source sky travel/velocity changes without inferring scanout quality."""
import json,sys,math
from pathlib import Path
from verify_live_sky_motion_evidence import verify
r=json.loads(Path(sys.argv[1]).read_text());verify(r)
s={(x['epoch'],x['publication']):x for x in r['sky_capture_records']}
rows=[]
for x in r['presentation_samples']:
 if not x.get('native_committed_sample') or not x.get('sky_interpolated'):continue
 a=s[x['epoch'],x['source_older']];b=s[x['epoch'],x['refresh']]
 delta=((b['angle']-a['angle']+8192)&16383)-8192
 phase=(((a['angle']&16383)+delta*x['alpha'])*240/4096)%240
 rows.append(dict(index=x['display_index'],epoch=x['epoch'],pair=[x['source_older'],x['refresh']],phase=phase,alpha=x['alpha'],source_velocity_per_refresh=delta*240/4096/(x['refresh']-x['source_older']),commit_ns=x['native_committed_sample'][6]))
steps=[];last=None
for a,b in zip(rows,rows[1:]):
 if a['epoch']!=b['epoch'] or b['index']!=a['index']+1:last=None;continue
 travel=((b['phase']-a['phase']+120)%240)-120
 step=dict(index=b['index'],source_pixel_travel=travel,output_pixel_travel=travel*13.5,pair_boundary=a['pair']!=b['pair'],commit_gap_ms=(b['commit_ns']-a['commit_ns'])/1e6,source_velocity_before=a['source_velocity_per_refresh'],source_velocity_after=b['source_velocity_per_refresh'])
 if last is not None:step['travel_change']=travel-last['source_pixel_travel']
 steps.append(step);last=step
assert steps and all(math.isfinite(x['source_pixel_travel']) for x in steps)
def stats(items):
 v=sorted(abs(x['source_pixel_travel']) for x in items)
 return dict(count=len(v),median_source_pixels=v[len(v)//2] if v else None,p95_source_pixels=v[min(len(v)-1,int(len(v)*.95))] if v else None,max_source_pixels=max(v) if v else None,over_one_source_pixel=sum(x>1 for x in v))
result=dict(result='MEASURED_SKY_TRAVEL',steps=stats(steps),boundary_steps=stats([x for x in steps if x['pair_boundary']]),interior_steps=stats([x for x in steps if not x['pair_boundary']]),largest_travel=sorted(steps,key=lambda x:abs(x['source_pixel_travel']),reverse=True)[:12],largest_travel_changes=sorted([x for x in steps if 'travel_change' in x],key=lambda x:abs(x['travel_change']),reverse=True)[:12],scope='Captured original angles and interpolated source phase on consecutive native commits. Output travel assumes viewport3240/240. Large travel or velocity changes alone do not establish perceptual stepping or physical scanout. No clock/renderer changes.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps({k:result[k] for k in ('result','steps','boundary_steps','interior_steps')},indent=2))
