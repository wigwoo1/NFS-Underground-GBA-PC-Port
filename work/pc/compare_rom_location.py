from pathlib import Path
import hashlib,json,os,shutil,subprocess,statistics
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-rom-location-tests';out.mkdir(exist_ok=True);assert shutil.disk_usage('C:/').free>10*1024**3;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
host=base/'NFSUG-pc-world-source-class-tests';b=json.loads((host/'live-build-report.json').read_text());exe=host/'NFSUG-Source-Native-Preview.exe';assert sha(exe)==b['exe_sha256'] and sha(host/'capture-host.dll')==b['core_sha256']
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';protected={str(p):sha(p) for p in [rom,state]};assert protected[str(rom)]=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593'
local=out/'temporary-verified-rom.gba';assert not local.exists();shutil.copyfile(rom,local);assert sha(local)==protected[str(rom)]
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
for n in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_MOTION_CAPTURE_PROFILE','NF_TRACE_NATIVE_COMMANDS','NF_AUDIO_POSITION_CSV']:env.pop(n,None)
rows=[];ideal=296*280896/16777216
for trial,label in enumerate(['network','local','local','network']):
 report=out/f'{trial}-{label}.json';pcm=out/f'{trial}-{label}.pcm';assert not report.exists()
 cmd=[str(exe),'--rom',str(local if label=='local' else rom),'--state',str(state),'--hidden','--frames','296','--script','--geometry-cache','--oracle',str(base/'NFSUG-android-capture-local/capture-off/frames.raw'),'--audio-dump',str(pcm),'--report',str(report)]
 p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=60);(out/f'{trial}-{label}.log').write_text(p.stdout+p.stderr);p.check_returncode();r=json.loads(report.read_text())
 assert r['exit_code']==r['timing_errors']==r['original_frame_mismatches']==r['prepare_failures']==r['present_failures']==r['audio_dropped_frames']==0 and r['logic_frames']==296
 assert r['processed_sequence']==r['final_sequence'] and r['background_allocations']==r['background_releases'] and r['geometry_allocations']==r['geometry_releases']
 assert sha(pcm)=='32e0b811f930f97ee35f958d9a701725c873b948b62a964016fe0e644d026260'
 row=dict(location=label,trial=trial,session=r,command=cmd,pcm_sha256=sha(pcm),original_wall_clock_budget_met=ideal<=r['elapsed_seconds']<=ideal+.15);rows.append(row)
 print(json.dumps(dict(location=label,trial=trial,elapsed=r['elapsed_seconds'],original_budget=row['original_wall_clock_budget_met'],core_mean_ms=r['phases']['core_step']['mean_ms'],audio_empty_events=r['audio_queue_empty_events'])),flush=True)
assert protected=={str(p):sha(Path(p)) for p in protected}
assert local.resolve().parent==out.resolve() and sha(local)==protected[str(rom)];local.unlink()
report=dict(result='VERIFIED_BALANCED_ROM_LOCATION_COMPARISON',rows=rows,location_means={k:statistics.mean(r['session']['elapsed_seconds'] for r in rows if r['location']==k) for k in ['network','local']},exe_sha256=b['exe_sha256'],core_sha256=b['core_sha256'],protected_sha256=protected,temporary_rom_removed=True,game_source_changed=False,original_ideal_seconds=ideal,full_scene_60fps=False,physical_audio_verified=False,limits='Four sequential same-binary network/local/local/network runs. ROM contents exact; only ROM path changes. Elapsed excludes startup. Cache/order and system load remain possible confounders; no blanket network or hardware attribution.')
(out/'comparison-report.json').write_text(json.dumps(report,indent=2));print('ROM_LOCATION_MEANS',report['location_means'],flush=True)
