"""Prepare named private JNI fixtures from verified original replay inputs."""
import hashlib,json,shutil
from pathlib import Path
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');local=Path('C:/NFSUG-Workspace');out=local/'NFSUG-source-world-jni-fixtures';out.mkdir(exist_ok=True)
inputs=((root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba','source-world-test.gba','53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593'),(root/'work/integration-0.state','source-world-test.state','49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104'))
for source,name,digest in inputs:
 assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
 shutil.copyfile(source,out/name)
hashes=[];alpha=set()
with (local/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as reference:
 for i in range(600):
  raw=bytearray(reference.read(153600));assert len(raw)==153600;alpha.update(raw[3::4])
  # frameNative exposes RGB unchanged and explicitly sets opaque alpha.
  raw[3::4]=bytes([255])*38400;hashes.append(hashlib.sha256(raw).hexdigest())
(out/'source-world-frames.txt').write_text('\n'.join(hashes)+'\n')
ref=json.loads((local/'NFSUG-android-shared-outcome-local/600-frame-audit/enabled-report.json').read_text());assert len(ref['source_packets'])==148
(out/'source-world-packets.txt').write_text('\n'.join(f"{r['serial']} {r['bytes']} {r['sha256']}" for r in ref['source_packets'])+'\n')
names=('source-world-test.gba','source-world-test.state','source-world-frames.txt','source-world-packets.txt')
manifest={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in names};(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
(out/'frame-format.json').write_text(json.dumps(dict(reference='capture-off/frames.raw',conversion='Preserve RGB; set alpha255 per frameNative documented opaque RGBA interface',original_alpha_values=sorted(alpha)),indent=2))
print('PASS_PREPARED_SOURCE_WORLD_JNI_FIXTURES: 600 opaque-RGBA hashes and 148 source packets; ROM/state hashes verified')
