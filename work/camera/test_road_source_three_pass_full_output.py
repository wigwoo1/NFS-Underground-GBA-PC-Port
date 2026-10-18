from pathlib import Path
import json,struct,hashlib
p=Path('work/camera');checks=[]
for command in [3,4,7]:
 original=(p/f'stable-road-{command}-all-original-samples.bin').read_bytes();expected={struct.unpack_from('<IB',original,i)[0]:struct.unpack_from('<IB',original,i)[1] for i in range(0,len(original),5)}
 source=p/f'road-{command}-three-pass-4k-index-output.bin';pixels=source.read_bytes();assert len(pixels)==3840*2160*8
 count=covered=0
 for y in range(2160):
  source_y=int((2160-(y+.5))/13.5);row=bytearray()
  for x in range(3840):
   destination=source_y*240+int(((x+.5)-300)//13.5)
   value=(expected[destination],1) if 300<=x<3540 and destination in expected else (-77,-77)
   row.extend(struct.pack('<2i',*value));covered+=value[1]==1
  actual=pixels[y*3840*8:(y+1)*3840*8]
  assert actual==row,(command,y,next((x for x in range(3840) if actual[x*8:x*8+8]!=row[x*8:x*8+8]),None))
  count+=3840
 checks.append(dict(command=command,exact_pixels=count,covered_pixels=covered,output_sha256=hashlib.sha256(pixels).hexdigest()))
report=dict(result='PASS',checks=checks,scope='Every pixel of all three captured three-pass 4K index targets versus immutable original index/coverage oracle expanded with declared viewport mapping, including borders. Endpoint pixel-grid diagnostic, not continuous native4K motion.');(p/'road-source-three-pass-full-output-tests.json').write_text(json.dumps(report,indent=2));print(report)
