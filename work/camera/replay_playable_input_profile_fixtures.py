import ctypes as C,json,hashlib,time
from pathlib import Path
folder=Path('work/camera/prototype-runs/slow-hud-1791448905477795700');manifest=json.loads((folder/'captures.json').read_text())
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/playable-input-profile-fixtures-20261008');cp.mkdir(exist_ok=True)
outputs={};timings={};profiles=None
for label,dll in [('baseline','owned-sky-source-context-candidate.dll'),('rowview','owned-gpu-playable-input-profile-candidate.dll')]:
 d=C.CDLL(str(Path('work/camera',dll).resolve()));P=C.c_void_p
 d.nf_owned_gpu_draw_scene_clips_sky_timed.argtypes=[P,C.c_size_t,P,P,P,C.c_uint,P,P,C.c_size_t,C.c_double,P];d.nf_owned_gpu_read.argtypes=[P,C.c_size_t]
 results=[];durations=[]
 try:
  assert d.nf_owned_gpu_window(0)==0
  for index,rec in enumerate(manifest['records']):
   data={name:Path(f['path']).read_bytes() for name,f in rec['files'].items()}
   assert all(hashlib.sha256(data[name]).hexdigest()==f['sha256'] for name,f in rec['files'].items())
   owners={name:C.create_string_buffer(raw) for name,raw in data.items()};rgb=C.create_string_buffer(3840*2160*3);samples=[];first=None
   for repeat in range(4):
    row=(C.c_uint64*2)();rc=d.nf_owned_gpu_draw_scene_clips_sky_timed(owners['frame'],len(data['frame']),owners['camera'],owners['models'],owners['bounds'],rec['geometry_records'],owners['lower'],owners['upper'],15136,rec['sky_weight'],row);assert rc==0,(label,index,rc)
    samples.append(list(row));assert d.nf_owned_gpu_read(rgb,len(rgb))==0
    sha=hashlib.sha256(rgb.raw).hexdigest()
    if first is None:first=sha
    else:assert first==sha,(label,index,'repeat')
   results.append(first);durations.append(dict(index=index,refresh=rec['frame_refresh'],draw_wall_ns_thread_100ns=samples))
  if label=='rowview':
   n=d.nf_hud_cpu_profile_count();values=(C.c_uint64*(n*11))();d.nf_hud_cpu_profile_read.argtypes=[P,C.c_uint];assert d.nf_hud_cpu_profile_read(values,n)==1 and d.nf_hud_cpu_profile_dropped()==0
   profiles=[list(values[i*11:(i+1)*11]) for i in range(n)];assert n==12
   count=d.nf_hud_input_profile_count();input_values=(C.c_uint64*(count*7))();d.nf_hud_input_profile_read.argtypes=[P,C.c_uint];assert d.nf_hud_input_profile_read(input_values,count)==1 and count==12 and d.nf_hud_input_profile_dropped()==0;input_records=[list(input_values[i*7:(i+1)*7]) for i in range(count)]
 finally:assert d.nf_owned_gpu_close()==1
 outputs[label]=results;timings[label]=durations
assert outputs['baseline']==outputs['rowview'],'Complete4K fixture outputs changed'
out=dict(result='PASS_RETAINED_HUD_FIXTURE_PARITY',fixtures=3,complete_draws=24,repeat_exact=True,full_rgb_sha256=outputs,timings=timings,hud_cpu_records=profiles,hud_input_records=input_records,scope='Exact retained HUD/frame/pose/sky replay through common scene-clips API; source anchors/visibility masks absent so not original source-world callback image oracle. Readback and profiling invalidate live cadence comparison; tiny uncontrolled samples do not establish optimization speedup.')
(cp/'replay.json').write_text(json.dumps(out,indent=2));print(out['result'],outputs)

