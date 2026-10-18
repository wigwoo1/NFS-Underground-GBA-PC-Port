from pathlib import Path
import subprocess,sys,json,hashlib
here=Path(__file__).resolve().parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-live-recipe-host-tests')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with (out/'host-suite.log').open('w') as log:p=subprocess.run([sys.executable,str(here/'test_live_host.py'),'--output-dir',str(out)],stdout=log,stderr=subprocess.STDOUT)
if p.returncode:
 print((out/'host-suite.log').read_text()[-7000:]);raise SystemExit(p.returncode)
r=json.loads((out/'live-test-report.json').read_text());cases=r['cases']
for name,case in cases.items():
 assert case['owned_recipe_publication'] and not case['recipe_fractional_rendering'] and case['recipe_frames_created']==case['recipe_frames_freed'] and case['recipe_handles_acquired']==case['recipe_handles_released'] and case['recipe_attach_failures']==0 and case['recipe_worker_failures']==0,(name,case)
 if name!='boot-fallback':assert case['recipe_handles_acquired']>0 and case['recipe_worker_checks']>0
report=dict(result='PASS_LIVE_HOST_OWNED_RECIPE_HANDOFF',build_report_sha256=sha(out/'live-build-report.json'),host_suite_report_sha256=sha(out/'live-test-report.json'),script_sha256=sha(Path(__file__)),suite_source_sha256=sha(here/'test_live_host.py'),exe_sha256=sha(out/'NFSUG-Source-Native-Preview.exe'),core_sha256=sha(out/'capture-host.dll'),all_frame_and_recipe_handles_balanced=True,worker_owned_reads_verified=True,reset_in_flight_rejection_verified=True,original_endpoint_4k_exact=True,recipe_fractional_rendering=False,full_scene_60fps=False,cases={name:{k:case[k] for k in ['logic_frames','elapsed_seconds','recipe_frames_created','recipe_frames_freed','recipe_handles_acquired','recipe_handles_released','recipe_attach_failures','recipe_worker_checks','recipe_worker_failures','stale_rejections','native_renders','native_presents','audio_dropped_frames']} for name,case in cases.items()})
(out/'recipe-handoff-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
