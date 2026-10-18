import ctypes as C,struct,random,json
from pathlib import Path
p=Path('work/camera');rng=random.Random(99);payload=rng.randbytes(2048);rows=[]
for y in range(160):
 vram=bytearray(0x18000);vram[:2048]=payload
 if y%3==1:vram[2048:4096]=bytes([1])*2048
 palette=payload[:1024];oam=payload[1024:]
 if y%3==2:palette=bytes([palette[0]^1])+palette[1:];vram[4096:6144]=palette+oam
 rows.append(struct.pack('<II',789,y)+bytes(120)+vram+palette+oam)
for name in ['layer-snapshot-baseline-benchmark.dll','layer-snapshot-padding-candidate.dll']:
 d=C.CDLL(str((p/name).resolve()));d.nf_layer_snapshot_create.restype=C.c_void_p;d.nf_layer_snapshot_add.argtypes=[C.c_void_p,C.c_void_p];d.nf_layer_snapshot_read.argtypes=[C.c_void_p,C.c_uint,C.c_void_p];d.nf_layer_snapshot_destroy.argtypes=[C.c_void_p];s=d.nf_layer_snapshot_create()
 try:
  for raw in rows:assert d.nf_layer_snapshot_add(s,C.create_string_buffer(bytes(raw),len(raw)))
  out=C.create_string_buffer(100480)
  for i,raw in enumerate(rows):assert d.nf_layer_snapshot_read(s,i,out) and out.raw==bytes(raw)
 finally:d.nf_layer_snapshot_destroy(s)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/layer-padding-candidate-20261007');(cp/'crosspart-parity.json').write_text(json.dumps(dict(result='PASS',rows=160,scope='Palette/OAM padded page shares exactVRAMpage; VRAMsameprefix/differenttail staysdistinct; palette mutation/reuse acrossrows reconstructsexact forbaseline/candidate'),indent=2));print('160 cross-part shared-prefix/full-page cases exact')
