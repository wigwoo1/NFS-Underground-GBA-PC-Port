"""ABBA profile of one live executable/core, exact audio and original clocks."""
from pathlib import Path
import hashlib,json,os,statistics,subprocess
source=Path(__file__).resolve().parent;root=source.parent.parent
base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-geometry-cache-host'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'live-build-report.json').read_text())
tests=json.loads((out/'live-test-report.json').read_text())
assert tests['result']=='PASS_LIVE_SOURCE_NATIVE_HOST_LIMITED_PROTOTYPE'
assert tests['build_receipt_sha256']==sha(out/'live-build-report.json')
assert tests['test_source_sha256']==sha(source/'test_live_host.py')
exe=out/'NFSUG-Source-Native-Preview.exe';core=out/'capture-host.dll'
assert tests['exe_sha256']==build['exe_sha256']==sha(exe)
assert tests['core_sha256']==build['core_sha256']==sha(core)
for n,h in build['source_sha256'].items():assert sha(source/n)==h,n
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
state=root/'work/integration-0.state';before={str(p):sha(p) for p in (rom,state)}
env=dict(os.environ)
for k in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TRACE_NATIVE_COMMANDS','NF_TEST_MOTION_CAPTURE_PROFILE']:env.pop(k,None)
rows=[]
for index,enabled in enumerate([False,True,True,False]):
    report=out/f'profile-{index}.json';audio=out/f'profile-{index}.pcm'
    cmd=[str(exe),'--rom',str(rom),'--state',str(state),'--hidden','--frames','1200','--fast','--script','--no-audio','--report',str(report),'--audio-dump',str(audio),'--geometry-cache' if enabled else '--direct-cached']
    subprocess.run(cmd,env=env,check=True,timeout=90)
    r=json.loads(report.read_text());assert r['exit_code']==0 and r['logic_frames']==1200
    assert r['timing_errors']==r['original_frame_mismatches']==r['present_failures']==r['audio_dropped_frames']==0
    assert r['processed_sequence']==r['final_sequence'] and r['native_renders']>0 and r['direct_cached_capture']
    assert r['reader_scratch_bytes']==r['reader_copied_bytes']==0
    assert r['background_allocations']==r['background_releases']==1190
    assert r['geometry_allocations']==r['geometry_releases']==1418
    assert r['audio_frames']==886021 and sha(audio)=='84d8e27f4ecdf97eff82a279523a546331d31c7c03b2b6f5723462d485ec08be'
    stats=r['geometry_cache_statistics'];assert r['geometry_cache_enabled']==enabled
    if enabled:assert stats[1]>0 and stats[2]>0 and stats[0]==stats[11]==stats[9]==0 and stats[6]<=stats[8] and stats[7]<=stats[8]
    else:assert not any(stats)
    row=dict(enabled=enabled,report_sha256=sha(report),audio_sha256=sha(audio),elapsed_seconds=r['elapsed_seconds'],phases=r['phases'],cache_statistics=stats,geometry_transferred_bytes=r['geometry_transferred_bytes'],renderer=r['renderer'])
    rows.append(row)
    print(json.dumps(dict(run=index,enabled=enabled,elapsed_seconds=r['elapsed_seconds'],capture_mean_ms=r['phases']['source_capture']['mean_ms'],cache_statistics=stats)),flush=True)
assert before=={str(p):sha(p) for p in (rom,state)}
medians={}
for name,enabled in [('uncached',False),('cached',True)]:
    group=[r for r in rows if r['enabled']==enabled]
    medians[name]=dict(elapsed_seconds=statistics.median(r['elapsed_seconds'] for r in group),capture_mean_ms=statistics.median(r['phases']['source_capture']['mean_ms'] for r in group),core_step_mean_ms=statistics.median(r['phases']['core_step']['mean_ms'] for r in group))
result=dict(result='PASS_GUARDED_CACHE_HOST_ABBA_PROFILE',order='uncached,cached,cached,uncached',steps_per_run=1200,original_timing_ideal_seconds=1200*280896/16777216,medians=medians,runs=rows,build_receipt_sha256=sha(out/'live-build-report.json'),test_receipt_sha256=sha(out/'live-test-report.json'),script_sha256=sha(Path(__file__)),exe_sha256=sha(exe),core_sha256=sha(core),rom_state_sha256=before,full_scene_60fps=False,scope='Same-machine short scripted segment, no audio playback, live renderer active. Not full-race pacing, interpolation or Intel/NVIDIA verification.')
(out/'geometry-cache-profile-report.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='runs'},indent=2))
