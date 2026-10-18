import json,statistics,shutil
from pathlib import Path
from verify_pause_native_segment_coverage import verify
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/vertex-conversion-profile-20261010')
f=max(Path('work/camera/prototype-runs').glob('owned-native-*.json'),key=lambda x:x.stat().st_mtime);r=json.loads(f.read_text());q=r['shutdown_evidence']['preparation_service_shutdown'];assert q['child_exitcode']==0 and not q['child_alive'] and not q['preparation_thread_alive'];shutil.copy2(f,cp/'callback-cycles30-raw.json');shutil.copy2(cp/'conversions.json',cp/'callback-cycles30-conversions.json')
rows=[]
for x in r['presentation_samples']:
 h=x['prepared']['hud_lease_stages'];n=h['native_callback_profile'];c=h['callback_outer_cycles'];assert c and c[1]>=c[0] and h['callback_begin_ns']<=n[0]<=n[1]<=h['callback_end_ns']<=h['release_end_ns']
 rows.append(dict(pair=[x['source_older'],x['refresh']],index=x['display_index'],outer_ms=(h['callback_end_ns']-h['callback_begin_ns'])/1e6,native_ms=(n[1]-n[0])/1e6,before_ms=(n[0]-h['callback_begin_ns'])/1e6,after_ms=(h['callback_end_ns']-n[1])/1e6,release_ms=(h['release_end_ns']-h['callback_end_ns'])/1e6,native_cycles=n[2],outer_cycles=c[1]-c[0],outside_native_cycles=c[1]-c[0]-n[2]))
assert len(rows)==120
keys=[k for k in rows[0] if k.endswith('_ms') or k.endswith('_cycles')]
out=dict(result='PASS_RENDERER_CALLBACK_CYCLE_BOUNDARIES',count=len(rows),summary={k:dict(median=statistics.median(x[k] for x in rows),maximum=max(x[k] for x in rows)) for k in keys},worst=sorted(rows,key=lambda x:x['outer_ms'],reverse=True)[:8],coverage=verify(r),clean_shutdown=True,scope='Last120 retained actual presentations; native and outer cycles have nested instrumentation overhead. Waiting/scheduling cannot be assigned exclusively to GIL; release interval includes other postcallback work.')
(cp/'callback-cycles30-audit.json').write_text(json.dumps(out,indent=2));(cp/'callback-cycles30-rows.json').write_text(json.dumps(rows,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ('worst','coverage')},indent=2));print(out['coverage']['active_intervals'])
