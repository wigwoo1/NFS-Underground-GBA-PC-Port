"""Actual threaded worker integration with immutable menu fixtures, no emulation."""
import hashlib,json,subprocess
from pathlib import Path
p=Path(__file__).resolve().parent;out=p/'prototype-runs/lifecycle-hardware';checks=[]
for name in ['stage-0','stage-2','stage-6','menu-2','menu-4','menu-5']:
 prefix=out/('threaded-'+name);run=subprocess.run([str(p/'threaded-hardware-worker-test.exe'),str(out/(name+'-bg-source.bin')),str(prefix)],check=True,capture_output=True,text=True);assert 'result=0 rendered=3 pushed=3 popped=3 worker_window_owner=1' in run.stdout
 reference=hashlib.sha256((out/(name+'-composed-gpu.rgba')).read_bytes()).hexdigest()
 for i in range(3):assert hashlib.sha256(Path(str(prefix)+f'-hardware-{i:02d}.rgba').read_bytes()).hexdigest()==reference
 checks.append(dict(checkpoint=name,worker_frames=3,pushed=3,popped=3,worker_window_owner=True,rgba_sha256=reference));print(name,'PASS',flush=True)
(out/'threaded-hardware-worker-report.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Actual threaded render worker queue/GL/window/commit with compact source-only hardware fixtures; exact full4K composition match. Synthetic arrival mode, no emulation/input/navigation or gameplay60fps claim.'),indent=2))
