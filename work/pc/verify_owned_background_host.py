from pathlib import Path
import hashlib,json,os,subprocess,sys,statistics
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-owned-background-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((out/'owned-background-build-report.json').read_text());assert b['exe_sha256']==sha(out/'NFSUG-Source-Native-Preview.exe') and b['core_sha256']==sha(out/'capture-host.dll')
(out/'live-build-report.json').write_text(json.dumps(dict(result='BUILT_OWNED_BACKGROUND_CANDIDATE_TESTS_PENDING',exe_sha256=b['exe_sha256'],core_sha256=b['core_sha256'],candidate_receipt_sha256=sha(out/'owned-background-build-report.json')),indent=2))
s=(here/'test_live_host.py').read_text();a='source=Path(__file__).resolve().parent;root=source.parent.parent;';assert s.count(a)==1;s=s.replace(a,f'source=Path({str(here)!r});root=source.parent.parent;',1)
a="cmd=[str(exe),'--rom'";assert s.count(a)==1;s=s.replace(a,"cmd=[str(exe),'--owned-background','--rom'",1)
staged=out/'test-live-host-owned.py';staged.write_text(s)
with (out/'live-regression.log').open('w') as log:p=subprocess.run([sys.executable,str(staged),'--output-dir',str(out)],stdout=log,stderr=subprocess.STDOUT)
if p.returncode:print((out/'live-regression.log').read_text()[-6000:]);raise SystemExit(p.returncode)
t=json.loads((out/'live-test-report.json').read_text())
for name,r in t['cases'].items():assert r['owned_background_capture'] and r['background_allocations']==r['background_releases']==r['background_transfers'],(name,r)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in (rom,state)}
env=dict(os.environ)
for k in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS']:env.pop(k,None)
runs=[]
for i,owned in enumerate((False,True,True,False)):
 label=f'paired-{i}-'+('owned' if owned else 'copied');rpath=out/(label+'.json');audio=out/(label+'.pcm')
 cmd=[str(out/'NFSUG-Source-Native-Preview.exe'),'--rom',str(rom),'--state',str(state),'--hidden','--script','--frames','1200','--no-audio','--report',str(rpath),'--audio-dump',str(audio)]
 if owned:cmd+=['--owned-background']
 subprocess.run(cmd,env=env,check=True,timeout=90);r=json.loads(rpath.read_text());assert r['logic_frames']==1200 and r['timing_errors']==r['present_failures']==r['audio_dropped_frames']==0 and r['processed_sequence']==r['final_sequence'] and r['native_renders']>0
 assert r['owned_background_capture']==owned and r['background_allocations']==r['background_releases']
 if owned:assert r['background_transfers']==r['published_frames'] and r['background_transferred_bytes']>0
 runs.append(dict(label=label,owned=owned,report=r,audio_sha256=sha(audio)));print(label,r['elapsed_seconds'],r['phases']['source_capture']['mean_ms'],flush=True)
assert len({r['audio_sha256'] for r in runs})==1
copied=[r['report'] for r in runs if not r['owned']];owned=[r['report'] for r in runs if r['owned']]
assert len({r['reader_copied_bytes'] for r in copied})==1
assert all(r['reader_copied_bytes']+r['background_transferred_bytes']==copied[0]['reader_copied_bytes'] for r in owned)
assert before=={str(p):sha(p) for p in (rom,state)}
cap=lambda rows:statistics.median(r['phases']['source_capture']['mean_ms'] for r in rows)
wall=lambda rows:statistics.median(r['elapsed_seconds'] for r in rows)
report=dict(result='VERIFIED_OWNED_BACKGROUND_HOST_AND_PAIRED_PROFILE',full_regression_passed=True,live_allocation_release_balanced=True,logic_frames_per_profile=1200,order='copied,owned,owned,copied',runs_per_mode=2,baseline_capture_mean_ms=cap(copied),candidate_capture_mean_ms=cap(owned),capture_reduction_percent=(1-cap(owned)/cap(copied))*100,baseline_elapsed_median_seconds=wall(copied),candidate_elapsed_median_seconds=wall(owned),ideal_seconds=1200*280896/16777216,baseline_copied_bytes=copied[0]['reader_copied_bytes'],candidate_copied_bytes=owned[0]['reader_copied_bytes'],transferred_background_bytes=owned[0]['background_transferred_bytes'],audio_sha256=runs[0]['audio_sha256'],rom_state_unchanged=True,diagnostic_live_host_profile=True,limited_local_runs_not_full_race=True,full_scene_60fps=False,exe_sha256=sha(out/'NFSUG-Source-Native-Preview.exe'),core_sha256=sha(out/'capture-host.dll'),cases={r['label']:r['report'] for r in runs})
(out/'owned-background-profile-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
