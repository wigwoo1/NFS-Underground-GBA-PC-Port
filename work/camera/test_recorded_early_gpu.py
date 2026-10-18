"""Record diagnostic early GPU driving and verify original input replay."""
from pathlib import Path
import os,subprocess,json,sys,uuid,hashlib
p=Path(__file__).resolve().parent;rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p.parent/'driving.state'
run=p/'prototype-runs'/('early-gpu-'+uuid.uuid4().hex);manifest=Path(str(run)+'-session.json')
(p/'recorded-early-gpu-tests.json').write_text(json.dumps(dict(result='RUNNING',session_manifest=str(manifest))))
session=dict(status='RUNNING',rom=str(rom),state=str(state),rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),state_sha256=hashlib.sha256(state.read_bytes()).hexdigest(),input_trace=str(run)+'-input.csv',display_trace=str(run)+'-display.csv',log=str(run)+'-host.log',ram_prefix=str(run)+'-final')
manifest.write_text(json.dumps(session,indent=2))
traffic='--traffic' in sys.argv
profile='--profile' in sys.argv
dirty='--dirty' in sys.argv
submission='--submission' in sys.argv
retire='--submission-retire' in sys.argv
consumer='--owned-consumer' in sys.argv
gl_worker='--owned-gl-worker' in sys.argv
assert not gl_worker or consumer
assert not consumer or submission
assert not retire or submission
if submission:
 session['owned_submission']=True;manifest.write_text(json.dumps(session,indent=2))
 (p/'recorded-owned-submission-tests.json').write_text(json.dumps(dict(result='RUNNING',session_manifest=str(manifest))))
if dirty:(p/'recorded-layer-dirty-tests.json').write_text(json.dumps(dict(result='RUNNING',session_manifest=str(manifest))))
if profile:(p/'recorded-original-profile-tests.json').write_text(json.dumps(dict(result='RUNNING',session_manifest=str(manifest))))
duration=60 if traffic or profile or dirty else 15
window_lifecycle='--window-lifecycle' in sys.argv
clock_restarts='--clock-restarts' in sys.argv
epoch_cuts='--epoch-cuts' in sys.argv
epoch_events=[]
window_events=[]
try:
 env={k:v for k,v in os.environ.items() if not k.startswith('NF_')}
 env.update(NF_PREPARATION_LEAD_US='8000',NF_PREPARE_GPU='1',NF_TEST_DISCARD_GPU='1',NF_VERIFY_EARLY_GPU_PIXELS='1',NF_LIVE_HUD='1',NF_LIVE_WORLD_CLASSIFIED='1',NF_LIVE_ROAD_ATTRIBUTES='1',NF_CONTINUOUS_CAMERA='1',NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'),NF_REFRESH_TRACE=session['input_trace'],NF_ENDPOINT_RAM_PREFIX=session['ram_prefix'])
 if dirty:env.update(NF_LAYER_DIRTY='1',NF_VERIFY_LAYER_DIRTY='1')
 if submission:env.update(NF_OWNED_SUBMISSION='1',NF_VERIFY_EARLY_GPU_LIMIT='64')
 if retire:env['NF_TEST_SUBMISSION_RETIRE']='1'
 if consumer:env['NF_TEST_OWNED_CONSUMER']='1'
 if gl_worker:env['NF_TEST_OWNED_GL_WORKER']='1'
 if profile:
  assert not (traffic or window_lifecycle or clock_restarts or epoch_cuts), 'Profile capture must run without injected lifecycle/readback diagnostics'
  env.pop('NF_TEST_DISCARD_GPU');env.pop('NF_VERIFY_EARLY_GPU_PIXELS');env['NF_CAPTURE_PROFILE']='1'
 if window_lifecycle:env['NF_TEST_WINDOW_LIFECYCLE']='1'
 if clock_restarts:env['NF_TEST_CLOCK_RESTART']='1'
 if epoch_cuts:env['NF_TEST_EPOCH_CUT']='1'
 if traffic:env['NF_VERIFY_EARLY_GPU_MIN_MODELS']='2'
 r=subprocess.run([str(p/'native-endpoint-road-attributes.exe'),str(p/'visibility-probe-wide.dll'),str(rom),str(state),session['display_trace'],'--paired-packets','--layer-sync','--scripted-route','--seconds',str(duration),'--delay-refreshes','8','--window-buffer'],env=env,text=True,capture_output=True,timeout=duration+20)
 Path(session['log']).write_text(r.stdout+r.stderr)
 session.update(status='HOST_COMPLETE' if r.returncode==0 else 'HOST_FAILED',exit_code=r.returncode);manifest.write_text(json.dumps(session,indent=2));assert r.returncode==0,r.stdout+r.stderr
 subprocess.run([sys.executable,str(p/'verify_prototype_session.py'),str(manifest)],check=True)
 verification=json.loads(manifest.with_name(manifest.stem+'-verification.json').read_text());
 if submission:
  if consumer:
   import re
   checks=re.findall(r'owned_consumer_verified=(\d+)',Path(session['log']).read_text())
   assert len(checks)==verification['early_gpu_accounting']['early_gpu_verified'] and int(checks[-1])==len(checks)
   consumer_checks=len(checks)
   if gl_worker:
    threads=re.findall(r'owned_gl_worker_draw=1 producer=(\d+) consumer=(\d+)',Path(session['log']).read_text())
    assert len(threads)==consumer_checks and all(a!=b for a,b in threads)
    assert len(set(threads))==1, 'Persistent worker identity changed'
    worker_counts=re.search(r'owned_gl_worker_starts=(\d+) owned_gl_worker_joins=(\d+) owned_gl_worker_total_draws=(\d+)',Path(session['log']).read_text())
    assert worker_counts and list(map(int,worker_counts.groups()))==[1,1,consumer_checks]
    if epoch_cuts:
     worker_epoch_draws=[len(re.findall(r'owned_gl_worker_draw=1',segment)) for segment in Path(session['log']).read_text().split('test_epoch_cut_index=')]
     assert sum(worker_epoch_draws)==consumer_checks and sum(n>0 for n in worker_epoch_draws)>=2
  import re
  log=Path(session['log']).read_text();assert int(re.search(r'submission_created=(\d+)',log)[1])>0 and int(re.search(r'submission_failed=(\d+)',log)[1])==0
  if retire:assert int(re.search(r'submission_retirement_tests=(\d+)',log)[1])==verification['early_gpu_accounting']['early_gpu_verified']>0
 if window_lifecycle:
  import re
  log=Path(session['log']).read_text();assert int(re.search(r'test_window_freezes=(\d+)',log)[1])==4 and int(re.search(r'test_window_pending_discards=(\d+)',log)[1])==4 and int(re.search(r'test_window_closed=(\d+)',log)[1])==1 and verification['presentation_segments']>=5
  suspended=re.findall(r'test_window_suspend=(\d+) total_steps=(\d+) refresh=(\d+)',log)
  resumed=re.findall(r'test_window_resume=(\d+) total_steps=(\d+) refresh=(\d+)',log)
  assert len(suspended)==4 and suspended==resumed and [int(e[0]) for e in suspended]==[1,2,3,4]
  assert verification['recorded_epoch_count']>=5
  window_events=[dict(handler=name,original_steps=int(e[1]),source_refresh=int(e[2]),unchanged_on_resume=True) for name,e in zip(['manual_pause','minimize','resize_loop','focus_loss'],suspended)]
 if clock_restarts:
  import re
  log=Path(session['log']).read_text();assert len(re.findall(r'test_clock_restart=',log))==3 and verification['presentation_segments']>=4 and verification['recorded_epoch_count']>=4
 if epoch_cuts:
  import re
  log=Path(session['log']).read_text();assert int(re.search(r'test_epoch_cuts=(\d+)',log)[1])==3 and int(re.search(r'test_epoch_rejections=(\d+)',log)[1])==3 and verification['recorded_epoch_count']>=4
  import csv
  displays=list(csv.DictReader(Path(session['display_trace']).open()))
  events=re.findall(r'test_epoch_cut_index=(\d+) old_epoch=(\d+) new_epoch=(\d+)',log);assert len(events)==3
  for index,old,new in events:
   assert int(new)>int(old)
   row=next(row for row in displays if int(row['display_index'])>=int(index))
   assert int(row['ready'])==0 and int(row['early_gpu_reused'])==0 and int(row['repeated'])==0
   epoch_events.append(dict(prepared_index=int(index),old_epoch=int(old),new_epoch=int(new),first_display_index=int(row['display_index']),stale_frame_presented=False))
 
 if traffic:
  import re
  from verify_early_gpu_traffic import verify_traffic
  traffic_samples=verify_traffic(manifest);model_checks=[row['models'] for row in traffic_samples]
 else:model_checks=[];traffic_samples=[]
 if profile:
  subprocess.run([sys.executable,str(p/'analyze_original_refresh_profile.py'),session['input_trace']],check=True,stdout=subprocess.DEVNULL)
  profile_report=json.loads((p/'original-refresh-profile-tests.json').read_text())
  assert profile_report['refreshes']==verification['refreshes']
  subprocess.run([sys.executable,str(p/'analyze_profile_intervals.py'),str(manifest)],check=True,stdout=subprocess.DEVNULL)
  interval_report=json.loads(manifest.with_name(manifest.stem+'-profile-intervals.json').read_text())
 else:
  profile_report=None
  assert verification['early_gpu_accounting']['early_gpu_discarded']>0 and verification['early_gpu_accounting']['early_gpu_verified']>0
 report=dict(result='PASS',window_lifecycle=window_lifecycle,window_events=window_events,clock_restarts=clock_restarts,epoch_events=epoch_events,traffic_model_checks=model_checks,traffic_samples=traffic_samples,session_manifest=str(manifest),verification=verification,scope='Scripted recorded original inputs and complete RAM replay; early GPU render accounting including intentional discards and after-update pixel checks. Window lifecycle uses synthetic messages to actual hidden-window handlers; no physical focus, resize, Xbox or smooth60fps proof.')
 (p/'recorded-early-gpu-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
 if submission:
  if consumer:report['owned_consumer_checks']=consumer_checks
  if gl_worker:report['owned_gl_worker_draws']=len(threads)
  if gl_worker:report['persistent_worker_starts_joins']=[1,1]
  if gl_worker and epoch_cuts:report['worker_epoch_draws']=worker_epoch_draws
  report.update(owned_submission=True,retire_before_redraw=retire,scope='Native rendering from complete copied packet and160selectedHUDrows; after-update bundle inputs and full4KRGB compared. Retirement diagnostic poisons/frees original allocation before redraw and compares retained independent clone. Exact original input/RAM replay. Same-thread prototype only; no concurrent renderer or smooth60fps proof.')
  if gl_worker:report['scope']='Bounded handoff to distinct GL worker with exclusive context migration, full4KRGB equality and exact original input/RAM replay. Producer joins each diagnostic draw; no independent presentation schedule, worker-owned window or smooth60fps proof.'
  (p/'recorded-owned-submission-tests.json').write_text(json.dumps(report,indent=2))
 if dirty:
  import re
  values=list(map(int,re.search(r'layer_clean_reused=(\d+) layer_clean_verified=(\d+) layer_clean_failed=(\d+)',Path(session['log']).read_text()).groups()))
  assert values[0]>0 and values[0]==values[1] and values[2]==0
  report.update(layer_dirty=True,clean_pages_compared=True,scope='Recorded native4K route with renderer-write dirty tracking; every clean-page reuse checked against exact live bytes, original input replay and full RAM parity. Lifecycle mode ends after800 updates. Readback/forced-discard diagnostics add overhead; no smooth60fps or physical Xbox proof.')
  report['clean_page_counts']=dict(zip(['reused','verified','failed'],values))
  (p/'recorded-layer-dirty-tests.json').write_text(json.dumps(report,indent=2))
 if profile:
  report.update(capture_profile=profile_report,interval_profile=interval_report,scope='Full-minute recorded native4K route and exact original RAM replay with per-refresh hook timings. No readback or forced discard; instrumentation adds overhead and wall time includes preemption. Not scanout or smooth60fps proof.')
  (p/'recorded-original-profile-tests.json').write_text(json.dumps(report,indent=2))
except Exception as error:
 failure=dict(result='FAIL',session_manifest=str(manifest),error=str(error))
 (p/'recorded-early-gpu-tests.json').write_text(json.dumps(failure,indent=2))
 if profile:(p/'recorded-original-profile-tests.json').write_text(json.dumps(failure,indent=2))
 if dirty:(p/'recorded-layer-dirty-tests.json').write_text(json.dumps(failure,indent=2))
 if submission:(p/'recorded-owned-submission-tests.json').write_text(json.dumps(failure,indent=2))
 raise

