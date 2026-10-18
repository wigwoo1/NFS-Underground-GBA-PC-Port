import subprocess,sys,json,time,hashlib
from pathlib import Path
p=Path('work/camera');folder=p/'prototype-runs'/('matched-gl-sync-'+str(time.time_ns()));folder.mkdir();rows=[]
flags='--capture-probe-candidate viewport-sky-capture-probe.dll --interpolate --startup-readiness --full-scene --background-prepare --precompute-world-samples --presentation-delay-refreshes 12 --python-thread-switch-ms 1 --capture-sky --interpolate-sky --continuous-sky --native-present-callback --original-update-boundary --producer-cycles --boundary-cpu --native-commit-stages --smoke-seconds 30 --smoke-steering --smoke-repeat-pause --show-smoke-window'.split()
binary=p/'owned-gpu-gl-display-cadence-candidate.dll';digest=hashlib.sha256(binary.read_bytes()).hexdigest()
for enabled in [False,True]:
 log=folder/('enabled.txt' if enabled else 'disabled.txt');args=[sys.executable,str(p/'run_playable_gl_cadence_candidate.py')]+['--swap-interval',str(int(enabled))]+flags
 print('Starting matched GL synchronization',enabled,flush=True)
 with log.open('w') as stream:result=subprocess.run(args,stdout=stream,stderr=subprocess.STDOUT)
 assert hashlib.sha256(binary.read_bytes()).hexdigest()==digest
 rows.append(dict(enabled=enabled,exit_code=result.returncode,log=str(log),binary_sha256=digest));(folder/'manifest.json').write_text(json.dumps(rows,indent=2));print('Finished',rows[-1],flush=True)
 if result.returncode:break
print('Matched manifest',folder/'manifest.json',flush=True)
