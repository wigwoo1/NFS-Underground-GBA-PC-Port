from pathlib import Path
import hashlib,json,os,subprocess,math
base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-present-deadline-tests';old=base/'NFSUG-pc-present-lock-tests';root=Path('Y:/CODEX/NFSUG-Native-PC-Port');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TRACE_NATIVE_COMMANDS','NF_TEST_MOTION_CAPTURE_PROFILE','NF_AUDIO_POSITION_CSV']:env.pop(key,None)
rows=[]
for trial in range(2):
 for label,folder in [('baseline',old),('deadline',out)]:
  b=json.loads((folder/'live-build-report.json').read_text());assert sha(folder/'NFSUG-Source-Native-Preview.exe')==b['exe_sha256'];assert sha(folder/'capture-host.dll')==b['core_sha256']
  tag=f'visible-{label}-{trial}';report=out/(tag+'.json');pcm=out/(tag+'.pcm');assert not report.exists()
  cmd=[str(folder/'NFSUG-Source-Native-Preview.exe'),'--rom',str(root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'),'--state',str(root/'work/integration-0.state'),'--frames','296','--script','--geometry-cache','--oracle',str(base/'NFSUG-android-capture-local/capture-off/frames.raw'),'--audio-dump',str(pcm),'--report',str(report)]
  p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=60);p.check_returncode();r=json.loads(report.read_text())
  assert r['exit_code']==r['timing_errors']==r['original_frame_mismatches']==r['present_failures']==r['prepare_failures']==0 and r['logic_frames']==296
  assert r['processed_sequence']==r['final_sequence'] and r['geometry_allocations']==r['geometry_releases'] and r['background_allocations']==r['background_releases']
  assert r['audio_dropped_frames']==0 and sha(pcm)==sha(old/'candidate-delay.pcm')
  s=r['presentation_sync'];assert s['observed'] and s['visible_presents']>0 and s['reported_interval']==s['requested_interval']==1 and s['set_failures']==0
  ideal=296*280896/16777216;assert ideal<=r['elapsed_seconds']<=ideal+.25
  if label=='deadline':assert s['visible_presents']+s['hidden_presents']<=math.ceil(r['elapsed_seconds']*60)+4
  row=dict(label=label,trial=trial,session=r,command=cmd,exe_sha256=b['exe_sha256'],core_sha256=b['core_sha256'],pcm_sha256=sha(pcm));rows.append(row)
  print(json.dumps(dict(label=label,trial=trial,elapsed=r['elapsed_seconds'],swaps=s['visible_presents']+s['hidden_presents'],interval=r['phases']['present_interval'])),flush=True)
(out/'visible-comparison-report.json').write_text(json.dumps(dict(result='PASS_SEQUENTIAL_VISIBLE_DEADLINE_COMPARISON_LIMITED_SCOPE',rows=rows,full_scene_60fps=False,physical_scanout_verified=False,tearing_verified=False,limits='Two sequential baseline/candidate pairs on local AMD. Scheduler caps accepted presentation slots; prepared endpoints may coalesce. Average host intervals and driver interval1 do not establish monitor scanout or interpolation.'),indent=2))
