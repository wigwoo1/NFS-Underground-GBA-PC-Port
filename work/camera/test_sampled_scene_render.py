"""Available complete sampled command packets: order and 4K diagnostic render."""
from pathlib import Path
import os,subprocess,struct,json,hashlib
from PIL import Image
p=Path('work/camera').resolve();f=p/'overflow-scene-171';next_header=(f/'new.bin').read_bytes()[16:32];cases=[]
for alpha in ('0.25','0.5','0.75'):
 raw=(f/f'composed-{alpha}.bin').read_bytes();sections={t:raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+i*12) for i in range(5))};n=struct.unpack_from('<I',sections[3],4)[0];ids=[struct.unpack_from('<5I',sections[5],8+i*20) for i in range(n)]
 order=struct.unpack_from('<'+'I'*n,sections[3],8);trace=json.loads((p/f'sampled-object-dispatch-{alpha}-motion-tests.json').read_text())
 actual=[ids[-1] if i==4294967295 else ids[i] for i in order]
 assert [(v[0],v[2]) for v in actual]==[({'road':1,'wall':2,'model':3}[v['kind']],v['source']) for v in trace['draws']]
 second=bytearray(raw);second[16:32]=next_header;other=f/f'composed-{alpha}-next.bin';other.write_bytes(second)
 env=os.environ.copy();env.update(NF_CAPTURE_CLIPS=str(f/f'composed-{alpha}.clips'),NF_PREVIEW_FRACTION=alpha,NF_PREVIEW_PHASE='2')
 subprocess.run([str(p/'sampled-clip-preview.exe'),str(f/f'composed-{alpha}.bin'),str(other),str(f/f'composed-{alpha}')],check=True,capture_output=True,env=env)
 with Image.open(f/f'composed-{alpha}-2.ppm') as im:
  assert im.size==(3840,2160);image=im.convert('RGB');background=image.getpixel((0,0));pixels=sum(v!=background for v in image.get_flattened_data());assert pixels>1000000
  image.resize((960,540)).save(f/f'composed-{alpha}-review.png');digest=hashlib.sha256(image.tobytes()).hexdigest()
 cases.append(dict(alpha=float(alpha),commands=n,pixels=pixels,image_sha256=digest,packet_order_exact=True))
assert len({c['image_sha256'] for c in cases})==3
report=dict(result='PASS',cases=cases,scope='Three complete offline sampled draw traces assembled and rendered with exact packet command source order. Wall scissor only, road clipping unresolved; no live native eligibility,60fps timing or playable port claim.')
(p/'sampled-scene-render-tests.json').write_text(json.dumps(report,indent=2));print(report)
