"""All actual owned BG palettes through GL fragment lookup and exact readback."""
import hashlib,json,subprocess,uuid
from pathlib import Path
p=Path(__file__).resolve().parent
out=p/'prototype-runs'/('display-palettes-'+uuid.uuid4().hex);out.mkdir()
prefix=p/'prototype-runs/threaded-prepared-2d9f8b417e1943be80cb86a65dc8f12d'
checks=[]
for frame in range(1,17):
    hud=Path(str(prefix)+f'-dense-{frame:02}-owned-hud.bin').read_bytes()
    assert len(hud)==160*34944
    raw=b''.join(hud[y*34944+32896:y*34944+32896+512] for y in range(160))
    file=out/f'frame-{frame:02}.bin';file.write_bytes(raw)
    result=subprocess.run([str(p/'display-palette-gpu-test.exe'),str(file)],capture_output=True,text=True,check=True)
    assert 'fragment_colors=40960' in result.stdout
    checks.append(dict(frame=frame,palette_sha256=hashlib.sha256(raw).hexdigest(),fragment_colors_exact=40960))
report=dict(result='PASS',checks=checks,scope='655360 exact GL fragment palette lookups from16 real owned display palettes; component lookup only, native geometry/index transport and60fps unverified.')
(p/'captured-palette-gpu-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(result='PASS',captures=16,fragment_colors_exact=655360)))
