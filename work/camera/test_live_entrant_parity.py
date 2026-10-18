"""Compare live inserted-wall frames against exported packet replays at 4K."""
from pathlib import Path
import json, os, subprocess, sys, time
from PIL import Image, ImageChops

p = Path(__file__).resolve().parent
env = os.environ.copy()
env.update(NF_LIVE_ENTRANTS='1', NF_ENTRANT_EXPORT=str(p/'entrant-phase'),
           NF_ENTRANT_LIVE_CAPTURE=str(p/'entrant-capture'))
started = time.time_ns()
subprocess.run([sys.executable,str(p/'test_live_sampled_parity.py')],env=env,check=True,capture_output=True)
subprocess.run([sys.executable,str(p/'test_live_entrant_render.py')],env=env,check=True,capture_output=True)
cases = []
for epoch in (2,3):
    for scene, alpha in ((27,1/3),(27,2/3),(28,.75)):
        suffix = f'-e{epoch}-s{scene}-a{alpha:.9f}'
        live = p/f'entrant-capture{suffix}.ppm'
        replay = p/f'entrant-phase{suffix}-shown-2.ppm'
        assert live.stat().st_mtime_ns >= started and replay.stat().st_mtime_ns >= started
        with Image.open(live) as a, Image.open(replay) as b:
            assert a.size == b.size == (3840,2160)
            difference = ImageChops.difference(a,b)
            assert difference.getbbox() is None, (epoch,scene,alpha,difference.getbbox())
        cases.append(dict(epoch=epoch,scene=scene,alpha=alpha,changed_pixels=0))
report = dict(result='PASS',cases=cases,scope='Live inserted geometry/clips versus matching offscreen packets. Unpaced diagnostic, not original-render fidelity or gameplay timing proof.')
(p/'live-entrant-parity-tests.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
