import json,statistics,sys,shutil
from pathlib import Path
root=Path(r'G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port')
sys.path.insert(0,str(root/'work/camera'))
from verify_pause_native_segment_coverage import verify
label=sys.argv[1];enabled='candidate' in label
f=max((root/'work/camera/prototype-runs').glob('owned-native-*.json'),key=lambda x:x.stat().st_mtime)
r=json.loads(f.read_text());rows=[]
for j in r['world_preparation_stage_samples']:
 t=j['terminal'][5]
 assert t['road_single_join_candidate'] is True
 assert j['parent_start_timing']['single_join_pack_selected']==enabled
 rows.append(dict(pair=[j['older'],j['newer']],pack_ms=(j['parent_start_timing']['packed_ns']-j['parent_start_timing']['pack_begin_ns'])/1e6))
assert len(rows)>100
q=r['shutdown_evidence']['preparation_service_shutdown'];assert q['child_exitcode']==0 and not q['child_alive'] and not q['preparation_thread_alive']
cp=root/'outputs/nfsug-native-renderer/camera-research/checkpoints/road-single-join-20261010'
shutil.copy2(f,cp/(label+'-live10-raw.json'))
out=dict(raw=str(f),jobs=len(rows),direct_decode_requested=True,single_join_pack_selected=enabled,road_single_join_selected=True,summary={k:dict(median=statistics.median(x[k] for x in rows),maximum=max(x[k] for x in rows)) for k in ('pack_ms',)},coverage=verify(r),rows=rows,clean_shutdown=True)
(cp/(label+'-live10-audit.json')).write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))


