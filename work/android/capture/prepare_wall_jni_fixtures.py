"""Prepare explicit private wall JNI inputs; never package the supplied ROM in an APK."""
from pathlib import Path
import hashlib,json,shutil
b=Path(r'C:\NFSUG-Workspace');r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');out=b/'NFSUG-wall-jni-fixtures';out.mkdir(exist_ok=True)
for path,name,digest in [(r.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba','wall-test.gba','53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593'),(r/'work/integration-0.state','wall-test.state','49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104')]:
 assert hashlib.sha256(path.read_bytes()).hexdigest()==digest;shutil.copyfile(path,out/name)
frames=[]
with (b/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as f:
 for i in range(600):
  raw=bytearray(f.read(153600));assert len(raw)==153600;raw[3::4]=b'\xff'*38400;frames.append(hashlib.sha256(raw).hexdigest())
(out/'wall-frames.txt').write_text('\n'.join(frames)+'\n');owners=b/'NFSUG-wall-owner-api-fixtures';files=sorted(owners.glob('owner-*.nwh'));assert len(files)==13
(out/'wall-owners.txt').write_text('\n'.join(f"{p.stem.split('-')[1]} {hashlib.sha256(p.read_bytes()).hexdigest()}" for p in files)+'\n')
manifest={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ('wall-test.gba','wall-test.state','wall-frames.txt','wall-owners.txt')};(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print('PASS_WALL_JNI_FIXTURES 600 original opaque RGBA references,13 host owner hashes')

