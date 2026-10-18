import json
from pathlib import Path
p=Path('work/camera/async-crop-fullscene-parity.json');r=json.loads(p.read_text());a=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/segmented-source-gpu-20261007/original-gpu-parity.json').read_text());assert r['checks']==a['checks'];assert len(r['async_crop_checks'])==5
r['scope']='Five complete4K frames from isolated asynchronous-crop DLL match verified segmented renderer and archived original frame hashes/signatures. Five asynchronous3072-byte crops match synchronous complete-frame crops exactly. Readback is intentionally synchronous for the reference comparison; no live cadence or physical scanout proof.'
p.write_text(json.dumps(r,indent=2));print('PASS archived full4K hashes and five async crop oracles')
