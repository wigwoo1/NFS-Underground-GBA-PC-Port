import subprocess,sys,json
from pathlib import Path
p=Path('work/camera')
args=['--capture-probe-candidate','viewport-sky-private-capture-probe.dll','--process-prepare','--shared-process-output','--interpolate','--startup-readiness','--full-scene','--background-prepare','--precompute-world-samples','--presentation-delay-refreshes','12','--python-thread-switch-ms','1','--capture-sky','--interpolate-sky','--continuous-sky','--native-present-callback','--original-update-boundary','--native-capture-batch','--producer-cycles','--smoke-seconds','25','--smoke-steering','--smoke-repeat-pause','--gc-trace']
rows=[]
for variant,runner in [('baseline','run_native_hud_short_lock_live_candidate.py'),('array_types','run_native_draw_array_types_live_candidate.py')]:
 print('START',variant,flush=True)
 r=subprocess.run([sys.executable,str(p/runner),*args],capture_output=True,text=True)
 print(r.stdout,flush=True)
 if r.returncode:
  print(r.stderr,flush=True);raise SystemExit(r.returncode)
 lines=r.stdout.splitlines()
 raw=next(Path(x) for x in lines if x.endswith('.json') and 'owned-native-' in x)
 audits={}
 for name in ['verify_active_wall_game_speed_candidate','verify_async_handoff_candidate','verify_exact_preparation_lifecycle_candidate','verify_whole_sky_phase_coverage_candidate','verify_complete_25ms_ledger_candidate','analyze_native_transaction_long_intervals_candidate','analyze_native_pre_draw_wait_candidate','analyze_child_gc_anchor_candidate']:
  out=p/'prototype-runs'/('draw-types-repeat-'+variant+'-'+name+'-20261009.json')
  test=subprocess.run([sys.executable,str(p/(name+'.py')),str(raw),str(out)],capture_output=True,text=True)
  if test.returncode:
   out.write_text(json.dumps(dict(result='FAILED_AUDIT',exit_code=test.returncode,stderr=test.stderr,raw=str(raw)),indent=2))
   print('AUDIT_FAILED',variant,name,flush=True)
  audits[name]=str(out)
 rows.append(dict(variant=variant,raw=str(raw),audits=audits))
 print('AUDITS_COMPLETE',variant,flush=True)
Path('work/camera/prototype-runs/record-draw-types-repeat-manifest-20261009.json').write_text(json.dumps(dict(result='TWO_REPEAT_RUNS_AUDITED',rows=rows,scope='One additional original/selective run each, fixed options, normal GC, no per-call census; not visible60 or causal certainty.'),indent=2))
