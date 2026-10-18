from pathlib import Path
import json,struct,hashlib
p=Path('work/camera');capture=json.loads((p/'motion-original-road-source-intervals.json').read_text());known={x['source']:x['command'] for x in json.loads((p/'motion-road-source-endpoints.json').read_text())['checks']};retained={x['command']:x['bounds'] for x in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};checks=[]
sha=lambda data:hashlib.sha256(data).hexdigest()
for scene in capture['scenes']:
 for road in scene['roads']:
  blocks={int(k):bytes.fromhex(v['hex']) for k,v in road['blocks'].items()};bd=list(struct.unpack_from('<4H',blocks[1],226));cmd=known.get(road['source']);palette=blocks[67];indices=blocks[66];material=blocks[8];assert len(palette)==512 and len(material)==48
  same=None
  if cmd is not None:
   texture=(p/f'road-{cmd}-index-texture.bin').read_bytes();plane=texture[8:];width,height=struct.unpack_from('<2I',texture);assert len(indices)==width*height*2;decoded=b''.join(indices[y*width*2:y*width*2+width] for y in range(height));same=decoded==plane
  checks.append(dict(begin=scene['begin'],end=scene['end'],event=road['event'],source=road['source'],command=cmd,bounds=bd,retained_bounds_equal=bd==retained[cmd] if cmd is not None else None,material_hex=material.hex(),material_sha256=sha(material),palette_hex=palette.hex(),palette_sha256=sha(palette),index_bytes=len(indices),index_sha256=sha(indices),retained_index_plane_equal=same,flags_hex=blocks.get(69,b'').hex()))
r=dict(result='CAPTURED_SCENE_MATERIAL_STATE',checks=checks,draws=len(checks),known_draws=sum(x['command'] is not None for x in checks),known_bounds_differences=sum(x['retained_bounds_equal'] is False for x in checks),known_index_differences=sum(x['retained_index_plane_equal'] is False for x in checks),distinct_palettes=len({x['palette_sha256'] for x in checks}),scope='Original per-draw captured state; decoded packed row stride preserves paired bytes. Not display scanline palette equivalence or original clipping endpoint proof.')
(p/'motion-road-materials.json').write_text(json.dumps(r,indent=2));print({k:v for k,v in r.items() if k not in ('checks','scope')})
