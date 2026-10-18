"""Valid legacy packets must reject before indexed display palette drawing."""
import os,json,struct,subprocess,uuid
from pathlib import Path
p=Path(__file__).resolve().parent
base=p/'prototype-runs/threaded-prepared-c90ce62f38a7417d898be3c380f9fe3a-dense-01'
raw=Path(str(base)+'-native-scene.bin').read_bytes()
out=p/'prototype-runs'/('indexed-admission-'+uuid.uuid4().hex);out.mkdir()
hud=Path(str(base)+'-owned-hud.bin').read_bytes()
(out/'palette.bin').write_bytes(b''.join(hud[y*34944+32896:y*34944+33408] for y in range(160)))
(out/'cameras.bin').write_bytes(Path(str(base)+'-owned-cameras.bin').read_bytes()[24:])
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')}
env.update(NF_ENDPOINT_DISPLAY_PALETTE=str(out/'palette.bin'),NF_ENDPOINT_COMMAND_CAMERAS=str(out/'cameras.bin'))
parts=[raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+j*12) for j in range(5))]
model=parts[0];assert model[:4]==b'NFM2'
vertices,faces,corners,w,h=struct.unpack_from('<5I',model,4)
core=160+vertices*24+faces+corners*18+w*h*4
assert model[core:core+4]==b'NZI1';parts[0]=model[:core]
packet=bytearray(raw[:96])
for j,part in enumerate(parts):
 packet+=bytes((-len(packet))%8);struct.pack_into('<3I',packet,32+j*12,j+1,len(packet),len(part));packet+=part
struct.pack_into('<I',packet,8,len(packet));missing=out/'missing-model-indices.bin';missing.write_bytes(packet)
legacy=p/'prototype-runs/threaded-prepared-2d9f8b417e1943be80cb86a65dc8f12d-dense-01-native-scene.bin'
for path in [missing,legacy]:
 target=out/'reject.ppm'
 result=subprocess.run([str(p/'sampled-scene-preview.exe'),str(path),str(target)],env=env,capture_output=True)
 assert result.returncode==43,(path,result.returncode,result.stderr)
 assert not Path(str(target)+'-0.ppm').exists()
report=dict(result='PASS',missing_model_indices_rejected=True,legacy_wall_metadata_rejected=True,output=str(out),scope='Two packet admission negative tests; valid current capture rendering covered by owned wall GPU audit. No fullscene60fps proof.')
(p/'display-palette-admission-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
