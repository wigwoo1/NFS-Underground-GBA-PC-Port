"""Validate captured sidecar then render the exact newer endpoint."""
from pathlib import Path
import json,struct,subprocess,os
from clip_metadata import validate
p=Path('work/camera').resolve();packet=(p/'clip-scene-141.bin').read_bytes();meta=json.loads((p/'clip-scene-141.json').read_text());validate(packet,meta['epoch'],meta)
records=sorted(meta['records'],key=lambda r:r['index'])
data=struct.pack('<5I',0x3150434e,meta['serial'],meta['begin'],meta['end'],len(records))
for r in records:data+=struct.pack('<5I4H',*r['identity'],*r['bounds'])
path=p/'captured-141.clips';path.write_bytes(data)
env=os.environ.copy();env['NF_CAPTURE_CLIPS']=str(path);env['NF_PREVIEW_FRACTION']='1';env['NF_PREVIEW_PHASE']='2'
subprocess.run([str(p/'captured-clip-preview.exe'),str(p/'clip-scene-140.bin'),str(p/'clip-scene-141.bin'),str(p/'captured-clipped')],env=env,check=True)
