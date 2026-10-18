from pathlib import Path
import json,shutil,hashlib
b=Path(r"C:\NFSUG-Workspace");source=b/'NFSUG-background-jni-fixtures';out=b/'NFSUG-complete-scene-gpu-fixtures';out.mkdir(exist_ok=True);manifest=json.loads((source/'manifest.json').read_text())
for name,digest in manifest.items():
 assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest;shutil.copyfile(source/name,out/name)
for row in (source/'retention-displays.txt').read_text().splitlines():
 for filename,original in [(f'background-{row}.rgba',b/f'NFSUG-wall-retention-gpu-fixtures/background-{row}.rgba'),(f'retention-{row}.ref',source/f'road-ref-{row}.bin'),(f'wall-retention-{row}.ref',source/f'wall-ref-{row}.bin')]:
  shutil.copyfile(original,out/filename);manifest[filename]=hashlib.sha256((out/filename).read_bytes()).hexdigest()
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print('Prepared complete-scene GPU reference fixtures',len(manifest))
