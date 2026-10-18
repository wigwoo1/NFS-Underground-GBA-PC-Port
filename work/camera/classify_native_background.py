"""Prove which pre-world display bytes were produced by this scene."""
from pathlib import Path
import json, struct
from scene_batches import batches
p=Path('work/camera'); checks=[]
for scene in batches(p/'motion-original-sprite-inputs-world.bin'):
 refresh=scene['end_refresh']+1
 if refresh not in (8758,8762,8766,8769,8773,8776,8780): continue
 first=next(i for i,e in enumerate(scene['events']) if e['pc'] in (0x030032f0,0x03000304,0x03004770))
 page=0xa000*scene['display_page']; image=bytearray(38400); coverage=bytearray(38400); ops=[]
 for event in scene['events'][:first]:
  if event['pc']!=0xffff0095: continue
  r=event['regs']; address=r[0]-0x06000000-page; pc=struct.unpack_from('<I',event['blocks'][95][1])[0]
  if pc==0x030002c0:
   data=struct.pack('<I',r[1])*(r[2]//4)
   assert 0<=address<=38400-len(data)
   image[address:address+len(data)]=data;coverage[address:address+len(data)]=bytes([1])*len(data)
   ops.append(dict(kind='fill',offset=address,bytes=len(data)))
  elif pc==0x03003814:
   ss,ds=struct.unpack('<2I',event['blocks'][96][1]); source=event['blocks'][97][1]
   for row in range(r[3]):
    dst=address+row*ds; width=((r[2]>>5)+1)*32; data=source[row*ss:row*ss+width]
    assert len(data)==width and 0<=dst<=38400-len(data)
    image[dst:dst+len(data)]=data;coverage[dst:dst+len(data)]=bytes([1])*len(data)
   ops.append(dict(kind='copy',offset=address,width=r[2],rows=r[3],stride=ds))
  else: raise AssertionError(hex(pc))
 live_mask=(p/f'motion-actual-scanline-assets/{refresh}-native-background-coverage.bin').read_bytes()[page:page+38400]
 assert live_mask==coverage
 native=(p/f'motion-actual-scanline-assets/{refresh}-native-background.bin').read_bytes()[page:page+38400]
 assert all(not coverage[i] or image[i]==native[i] for i in range(38400))
 assert sum(coverage)==25696 and coverage==bytes([1])*25696+bytes(12704)
 # Publish only this scene's background, with an explicit ownership mask.
 (p/f'motion-actual-scanline-assets/{refresh}-background-image.bin').write_bytes(image)
 (p/f'motion-actual-scanline-assets/{refresh}-background-coverage.bin').write_bytes(coverage)
 checks.append(dict(refresh=refresh,page=page,owned_bytes=sum(coverage),unowned_bytes=38400-sum(coverage),operations=ops))
assert len(checks)==7
report=dict(result='PASS_BACKGROUND_SOURCE_COVERAGE',checks=checks,scope='Only source fill/copy bytes are published; unowned lower region are unowned and must not be drawn as background. Seven captured scenes only.')
(p/'native-background-coverage-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
