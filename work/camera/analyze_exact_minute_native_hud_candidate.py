import json,statistics
from pathlib import Path
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791538928871594200.json').read_text());rows=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['records'];out=[]
for x in rows:
 b=x['hud_build_split'];h=x['hud_lease_stages'];assert len(b)==8 and b[0] in (0,1) and b[1] in (0,160)
 callback=h['callback_end_ns']-h['callback_begin_ns'];assert 0<=b[7]<=callback
 out.append(dict(display_index=x['display_index'],reuse=bool(b[0]),rows_built=b[1],hud_prepare_ms=b[7]/1e6,text_ms=b[2]/1e6,controls_ms=b[3]/1e6,decode_ms=b[4]/1e6,metadata_ms=b[5]/1e6,cache_ms=b[6]/1e6,callback_ms=callback/1e6,callback_outside_hud_prepare_ms=(callback-b[7])/1e6))
result=dict(result='PASS_EXISTING_NATIVE_HUD_SUBSTAGE_AUDIT',count=len(out),reuse=sum(x['reuse'] for x in out),rebuild=sum(not x['reuse'] for x in out),medians={k:statistics.median(x[k] for x in out) for k in out[0] if k.endswith('_ms')},rows=out,scope='Complete58 long intervals; existing native HUD prepare elapsed, not exclusive threadCPU. Remaining callback includes other scene work, HUD output ownership/effect batching and scheduling; no exclusive cause claim.')
Path('work/camera/prototype-runs/exact-minute-native-hud-stage-audit-20261009.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='rows'})
