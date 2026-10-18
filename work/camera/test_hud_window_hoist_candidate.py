import ctypes as C,json,struct,time,statistics
from pathlib import Path
p=Path('work/camera');libraries={}
for name,file in [('baseline','hud-window-baseline-candidate.dll'),('hoist','hud-window-hoist-candidate.dll')]:
 d=C.CDLL(str((p/file).resolve()));d.nf_hud_rows.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_uint];libraries[name]=d
pairs=json.loads((p/'prototype-runs/hud-row-render-input-equality-20261009.json').read_text())['pairs'];accepted=0;rejected=0;fixtures=[]
for pair in pairs:
 for file in ['older.frame.bin','newer.frame.bin']:
  data=(Path(pair['folder'])/file).read_bytes();h=struct.unpack_from('<6I2Q',data);hud=data[40+h[2]:40+h[2]+h[3]];src=C.create_string_buffer(hud);outputs={};status={}
  for name,d in libraries.items():
   out=C.create_string_buffer(384000);status[name]=d.nf_hud_rows(src,len(hud),out,1);outputs[name]=out.raw
  assert status['baseline']==status['hoist'],pair
  assert outputs['baseline']==outputs['hoist'],pair
  if status['baseline']:accepted+=1;fixtures.append(src)
  else:rejected+=1
assert accepted>0
trials=[]
for trial in range(6):
 costs={}
 for name in (['baseline','hoist'] if trial%2==0 else ['hoist','baseline']):
  out=C.create_string_buffer(384000);v=[]
  for src in fixtures[-10:]:
   begin=time.perf_counter_ns();assert libraries[name].nf_hud_rows(src,5591040,out,10);v.append((time.perf_counter_ns()-begin)/10/1e6)
  costs[name]=statistics.median(v)
 trials.append(costs)
result=dict(result='PASS_CAPTURED_HUD_WINDOW_HOIST_PARITY',accepted_frames=accepted,rejected_frames=rejected,trials_ms=trials,median_trial_ms={k:statistics.median(t[k] for t in trials) for k in libraries},scope='Exact allcolor/tag/visible/backdrop bytes for independent captured frames, six alternating matched10frame batches/10repeats. Decoder component only; no4Krenderer/livecadence claim.')
(p/'prototype-runs/hud-window-hoist-cost-20261009.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
