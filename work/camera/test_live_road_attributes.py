from pathlib import Path
import subprocess,os,re,ctypes as C,hashlib,json,csv,statistics,sys
p=Path('work/camera').resolve();root=p.parent
rom='G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
duration=int(sys.argv[1]) if len(sys.argv)>1 else 15
window='--window-buffer' in sys.argv[2:]
bridge=p/('visibility-probe-wide-reference-palette.dll' if '--reference-palette' in sys.argv[2:] else 'visibility-probe-wide.dll')
hud='NF_LIVE_HUD' in os.environ
env=dict(os.environ,NF_ENDPOINT_RAM_PREFIX=str(p/'road-attribute-live-parity'),NF_LAYER_SYNC_LOG=str(p/'road-attribute-live-layer-sync.csv'))
try:
 log=subprocess.check_output([str(p/'native-endpoint-road-attributes.exe'),str(bridge),rom,str(root/'driving.state'),str(p/'road-attribute-live-parity.csv'),'--paired-packets','--layer-sync','--scripted-route','--seconds',str(duration),'--delay-refreshes','8']+(['--window-buffer'] if window else []),env=env,text=True)
except subprocess.CalledProcessError as error:
 (p/"road-attribute-live-layer-sync-tests.json").write_text(json.dumps(dict(result="FAIL",duration_seconds=duration,exit_code=error.returncode,host_output=error.output,scope="Diagnostic host failed; do not reuse prior PASS or infer completed capture"),indent=2))
 raise
(p/'road-attribute-live-parity.log').write_text(log)
failures={key:int(re.search(key+r'=(\d+)',log)[1]) for key in ('rejected_scenes','layer_missing','paired_rejected')}
if any(failures.values()):
 (p/'road-attribute-live-layer-sync-tests.json').write_text(json.dumps(dict(result='FAIL',duration_seconds=duration,refreshes=int(re.search(r'simulated=(\d+)',log)[1]),failures=failures,host_output=log,scope='Scene/layer/pair rejection: run failed before final game RAM comparison; retain diagnostics, never reuse stale PASS'),indent=2))
assert int(re.search(r'rejected_scenes=(\d+)',log)[1])==0,log
assert int(re.search(r'layer_missing=(\d+)',log)[1])==0,log
assert int(re.search(r'paired_rejected=(\d+)',log)[1])==0,log
n=int(re.search(r'simulated=(\d+)',log)[1])
d=C.CDLL(str(root/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32]
assert d.nf_init(rom.encode(),b'') and d.nf_state(str(root/'driving.state').encode(),0)
try:
 for i in range(n):d.nf_frame(1|(32 if 180<=i<500 else 16 if 500<=i<720 else 0))
 hashes={}
 for name,base,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=p/f'live-paired-baseline-{name}.bin';d.nf_dump(str(path).encode(),base,size)
  baseline=path.read_bytes();actual=(p/f'road-attribute-live-parity-{name}.bin').read_bytes();assert baseline==actual,name
  hashes[name]=hashlib.sha256(actual).hexdigest()
finally:d.nf_close()
rows=list(csv.DictReader(open(p/'road-attribute-live-parity.csv')));ready=[r for r in rows if int(r['ready'])]
previous_work=previous_steps=0
for row in rows:
 work,steps=int(row['simulation_total_ns']),int(row['original_steps_total'])
 assert work>=previous_work and work-previous_work==int(row['simulation_since_display_ns'])
 assert steps>=previous_steps and steps-previous_steps==int(row['original_steps_since_display'])
 assert int(row['display_simulation_steps'])<=int(row['original_steps_since_display'])
 previous_work,previous_steps=work,steps
assert previous_work+int(re.search(r'original_work_unreported_ns=(\d+)',log)[1])==int(re.search(r'original_work_ns=(\d+)',log)[1])
assert previous_steps+int(re.search(r'original_steps_unreported=(\d+)',log)[1])==n
gpu_counts={key:int(re.search(key+r'=(\d+)',log)[1]) for key in ('early_gpu_rendered','early_gpu_presented','early_gpu_discarded','early_gpu_pending','early_gpu_ns')}
gpu_verify={key:int(re.search(key+r'=(\d+)',log)[1]) for key in ('early_gpu_verified','early_gpu_verification_draws','early_gpu_verify_failed','early_gpu_verified_updates','early_gpu_verification_ns')}
gpu_extra=gpu_counts['early_gpu_discarded']+gpu_counts['early_gpu_pending']+gpu_verify['early_gpu_verification_draws']
if 'NF_VERIFY_EARLY_GPU_PIXELS' in os.environ:assert gpu_verify['early_gpu_verified']>0 and gpu_verify['early_gpu_verify_failed']==0 and gpu_verify['early_gpu_verified_updates']>=gpu_verify['early_gpu_verified']

assert gpu_counts['early_gpu_rendered']==gpu_counts['early_gpu_presented']+gpu_counts['early_gpu_discarded']+gpu_counts['early_gpu_pending']
if 'NF_PREPARE_GPU' in os.environ:
 assert gpu_counts['early_gpu_presented']>0
 gpu_counts['presented_after_original_updates']=sum(int(r['early_gpu_reused']) and int(r['display_simulation_steps'])>0 for r in rows)
 assert gpu_counts['presented_after_original_updates']>0
 if 'NF_TEST_DISCARD_GPU' in os.environ:assert gpu_counts['early_gpu_discarded']>0

assert sum(int(r['early_gpu_reused']) for r in rows)==gpu_counts['early_gpu_presented']
gpu_previous=0
for r in rows:
 total=int(r['early_gpu_total_ns']);assert total-gpu_previous==int(r['early_gpu_since_display_ns']);gpu_previous=total
assert gpu_previous+int(re.search(r'early_gpu_unreported_ns=(\d+)',log)[1])==gpu_counts['early_gpu_ns']


def stats(values):return dict(median=statistics.median(values),p95=sorted(values)[int(.95*len(values))],maximum=max(values),over_16_667ms=sum(v>1000/60 for v in values))
sim=[(int(r['simulation_end_ns'])-int(r['simulation_start_ns']))/1e6 for r in rows]
combined=[(int(r['render_end_ns'])-int(r['simulation_start_ns']))/1e6 for r in ready]
poses=[tuple(r[k] for k in ('camera_x','camera_y','camera_z','object_x','object_y','object_z','camera_qx','camera_qy','camera_qz','camera_qw','object_qx','object_qy','object_qz','object_qw')) for r in ready]
swap_ms=[(int(r['swap_end_ns'])-int(r['render_end_ns']))/1e6 for r in rows]
intervals=[(int(b['swap_end_ns'])-int(a['swap_end_ns']))/1e6 for a,b in zip(rows,rows[1:])]
components={name:stats([int(r[name])/1e6 for r in ready]) for name in ('endpoint_prepare_ns','paired_prepare_ns')}
report=dict(original_work_total_ns=int(re.search(r'original_work_ns=(\d+)',log)[1]),original_work_interval_ms=stats([int(row['simulation_since_display_ns'])/1e6 for row in rows]),early_gpu_pixel_checks=gpu_verify,early_gpu_checks=gpu_counts,pose_changes=sum(a!=b for a,b in zip(poses,poses[1:])),nonzero_alpha=sum(float(r["alpha"])>0 for r in ready),window_stage_swap_ms=stats(swap_ms),swap_interval_ms=stats(intervals),duration_seconds=duration,window_buffer=window,component_ms=components,result='PASS',scope='Exact final EWRAM/IWRAM at identical scripted input and refresh count; diagnostic offscreen timing, no smooth60fps claim',refreshes=n,ram_hashes=hashes,simulation_batch_ms=stats(sim),simulation_plus_generation_render_ms=stats(combined),host_output=log)
layer_rows=list(csv.DictReader(open(p/'road-attribute-live-layer-sync.csv')));assert layer_rows and all(int(r['found'])==1 and int(r['selected_refresh'])==__import__('math').floor(float(r['target'])) for r in layer_rows)
report.update(layer_selection_count=len(layer_rows),exact_layer_refresh_selection=True,scope='Exact layer refresh/epoch selection during native paired rendering and identical final game RAM; HUD not displayed, no smooth60fps proof')
if hud:
 count=int(re.search(r'hud_drawn=(\d+)',log)[1]);failed=int(re.search(r'hud_failed=(\d+)',log)[1])
 assert count==len(ready)+gpu_extra and count>0 and failed==0,log
 report.update(hud_drawn=count,hud_failed=failed,scope='Live native world with GPU HUD composition using all160exact owned scanline states; native CPU candidate/affine resolution; final game RAM parity, unsupported effects/windows rejected; no smooth60fps proof')
if any(key in os.environ for key in ('NF_LIVE_MULTIMODEL_INDEXED','NF_LIVE_WORLD_INDEXED','NF_LIVE_WORLD_CLASSIFIED')):
 mode=int(re.search(r'indexed_multimodel=(\d+)',log)[1]);draws=int(re.search(r'model_zero_draws=(\d+)',log)[1]);assert mode==1 and draws>=len(ready),log
 report.update(indexed_multimodel=mode,model_zero_draws=draws)
report['road_attribute_corrected_rings']=int(re.search(r'road_attribute_corrected_rings=(\d+)',log)[1]);assert report['road_attribute_corrected_rings']>0
report['scope']='Opt-in live raw-source road UV correction with native4Kworld/GPUHUD and exact original gameRAM; no original fullscene pixel fidelity or smooth60fps proof'
if os.environ.get('NF_CONTINUOUS_CAMERA')=='1':
 count=int(re.search(r'continuous_camera_frames=(\d+)',log)[1]);assert count==len(ready)+gpu_extra and count>0
 report['continuous_camera_frames']=count
 report['scope']='Opt-in continuous source-camera/native4Kworld/GPUHUD with exact original gameRAM; native quantized visibility/bounds retained. No fullscene pixel fidelity or smooth60fps proof.'
if os.environ.get('NF_CONTINUOUS_ROAD_UV')=='1':
 count=int(re.search(r'continuous_road_uv_adjustments=(\d+)',log)[1]);assert count>0
 report['continuous_road_uv_adjustments']=count
 report['scope']='Opt-in continuous camera/near-UV presentation with original gameRAM parity; front64 generated UV intentionally differs from original biased arithmetic. Native visibility/bounds retained; no fullscene fidelity or smooth60fps proof.'
if os.environ.get('NF_PREPARATION_LEAD_US'):
 counters={key:int(re.search(key+r'=(\d+)',log)[1]) for key in ('early_generated','early_reused','early_discarded','early_verified','early_failed','early_generation_ns')}
 assert counters['early_failed']==0 and counters['early_reused']>0,log
 if 'NF_VERIFY_PREPARED_PACKET' in os.environ:assert counters['early_verified']==counters['early_reused'],log
 increments=[int(r['early_generation_since_display_ns']) for r in rows]
 totals=[int(r['early_generation_total_ns']) for r in rows]
 previous=0
 for increment,total in zip(increments,totals):
  assert total>=previous and total-previous==increment
  previous=total
 unreported=int(re.search(r'preparation_unreported_ns=(\d+)',log)[1])
 assert sum(increments)+unreported==counters['early_generation_ns']
 assert sum(int(r['early_reused_since_display']) for r in rows)==counters['early_reused']
 report['early_work_reconciliation']=dict(recorded_ns=sum(increments),terminal_unreported_ns=unreported,early_plus_due_generation_ms=stats([(int(r['early_generation_since_display_ns'])+int(r['paired_prepare_ns']))/1e6 for r in rows]),scope='CPU generation work charged across display intervals; excludes rendering and simulation, not end-to-end latency')
 report['early_packet_checks']=counters
 report['scope']+=' CPU generation and early complete scene/HUD render work separately timed; early GPU reuse is opt-in, actual image/scanout smoothness not inferred.'
(p/'road-attribute-live-layer-sync-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if 'NF_LIVE_WORLD_INDEXED' in os.environ or 'NF_LIVE_WORLD_CLASSIFIED' in os.environ:
 mode=int(re.search(r'indexed_world=(\d+)',log)[1]);draws=int(re.search(r'world_zero_draws=(\d+)',log)[1]);assert mode==1 and draws>0,log
 report.update(indexed_world=mode,world_zero_draws=draws)
 (p/'road-attribute-live-indexed-tests.json').write_text(json.dumps(report,indent=2));print(dict(indexed_world=mode,world_zero_draws=draws))
if 'NF_LIVE_WORLD_CLASSIFIED' in os.environ:
 mode=int(re.search(r'classified_world=(\d+)',log)[1]);draws=int(re.search(r'wall_zero_draws=(\d+)',log)[1])
 assert mode==1 and draws>0,log
 report.update(classified_world=mode,wall_zero_draws=draws)
 (p/'road-attribute-live-classified-tests.json').write_text(json.dumps(report,indent=2));print(dict(classified_world=mode,wall_zero_draws=draws))
