import runpy,struct,json
from pathlib import Path
from owned_sky_sampler import SkyAsset,SkySamples
from owned_sky_color import sky_rgba
s=runpy.run_path('work/camera/test_owned_sky_boundary.py');records=s['records'];raw=s['rom'];origin=records[0].asset_origin
asset=SkyAsset(origin,raw[origin-0x08000000:origin-0x08000000+15376])
palette=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-state-parity-20261006/sky-caller-probe.dll-palette.bin').read_bytes()[:512]
# Distinct row palettes prove placement including the final16bytes on row107.
rows=[]
for y in range(160):rows.append(struct.pack('<256H',*[((c+y)&32767) for c in struct.unpack('<256H',palette)]))
palettes=b''.join(rows);checks=0
for a,b in zip(records,records[1:]):
 for endpoint,boundary in ((0,a),(1,b)):
  rgba=sky_rgba(asset.sample(a,b,endpoint),palettes)
  oracle=bytearray()
  for i,index in enumerate(boundary.indices):
   c=struct.unpack_from('<H',palettes,(44+i//240)*512+index*2)[0]
   oracle.extend([*((((c>>shift)&31)<<3)|(((c>>shift)&31)>>2) for shift in (0,5,10)),255])
  assert rgba==oracle;checks+=1
# Palette index interpolation would select index127/128 instead of purple.
known=bytearray(160*512)
for y in range(160):struct.pack_into('<H',known,y*512+255*2,31<<10);struct.pack_into('<H',known,y*512,31)
x=sky_rgba(SkySamples(bytes(15136),bytes([255])*15136,.5,0x06002940),known)
assert x==bytes([128,0,128,255])*15136
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-scanline-color-oracle-20261006');out.mkdir(exist_ok=True)
for name in ('owned_sky_color.py','test_owned_sky_color.py'):(out/name).write_text((Path('work/camera')/name).read_text())
(out/'tests.json').write_text(json.dumps(dict(result='PASS',exact_original_endpoints=checks,bytes_per_endpoint=60544,scope='Original ROM source footprint converted using distinct scanline palettes; known red-blue midpoint proves post-palette blend. Reference only, no GPU/live proof'),indent=2));print('PASS sky scanline colors',checks)
