import json,hashlib,struct,shutil
from pathlib import Path
folder=Path('work/camera/prototype-runs/slow-hud-1791448905477795700');m=json.loads((folder/'captures.json').read_text());total=0
for r in m['records']:
 for f in r['files'].values():
  data=Path(f['path']).read_bytes();assert len(data)==f['bytes'] and hashlib.sha256(data).hexdigest()==f['sha256'];total+=len(data)
 data=Path(r['files']['frame']['path']).read_bytes();h=struct.unpack_from('<6I2Q',data);assert h[0]==0x3346474e and h[6]==r['epoch'] and h[1]==r['frame_refresh'] and h[7]==h[1]*280896 and 40+sum(h[2:6])==len(data)
assert len(m['records'])<=3 and total==m['retained_bytes'] and total<=32*1024*1024
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/playable-slow-hud-capture-20261008');shutil.copytree(folder,cp/'fixtures',dirs_exist_ok=True)
out=dict(result='PASS_CAPTURE_HASHES_LAYOUT_BUDGET',records=len(m['records']),retained_bytes=total,rejected=m['rejected'],refreshes=[r['frame_refresh'] for r in m['records']],scope='Immutable sampled HUD/frame/pose/sky inputs; source anchor arrays/visibility masks are not included, so replay cannot claim identical source-world callback output.')
(cp/'fixture-integrity.json').write_text(json.dumps(out,indent=2));print(out)
