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
 clips=bytearray((f/f'composed-{alpha}.clips').read_bytes());road_inputs=json.loads((p/f'road-clip-inputs-{alpha}-motion-writes-full.json').read_text())['cases']
 road_draws=[v for v in trace['draws'] if v['kind']=='road'];assert len(road_inputs)==len(road_draws)
 for i,(road,draw) in enumerate(zip(road_inputs,road_draws)):
  off=28+i*28;identity=struct.unpack_from('<5I',clips,off);bounds=struct.unpack_from('<4H',clips,off+20)
  assert identity[0]==1 and identity[2]==road['source']==draw['source'] and road['owner']==draw['owner'] and list(bounds)==road['bounds']
  bottom=road['native_clip_bounds'][3];assert road['native_clip_bounds'][:3]==list(bounds[:3]) and bottom<=160
  struct.pack_into('<H',clips,off+26,bottom)
 policy=f/f'road-native-bottom-{alpha}.clips';policy.write_bytes(clips)
 env=os.environ.copy();env.update(NF_CAPTURE_CLIPS=str(policy),NF_PREVIEW_FRACTION=alpha,NF_PREVIEW_PHASE='2')
 subprocess.run([str(p/'sampled-road-clip-preview.exe'),str(f/f'composed-{alpha}.bin'),str(other),str(f/f'road-native-bottom-{alpha}')],check=True,capture_output=True,env=env)
 with Image.open(f/f'road-native-bottom-{alpha}-2.ppm') as im:
  assert im.size==(3840,2160);image=im.convert('RGB');background=image.getpixel((0,0));pixels=sum(v!=background for v in image.get_flattened_data());assert pixels>1000000
  baseline=json.loads((p/'sampled-scene-render-tests.json').read_text())['cases'][len(cases)]['pixels']
  assert pixels>baseline*.95, 'large scene coverage loss requires visual investigation'
  image.resize((960,540)).save(f/f'road-native-bottom-{alpha}-review.png');digest=hashlib.sha256(image.tobytes()).hexdigest()
 bottom_pixels=sum(image.getpixel((x,2159))!=background for x in range(300,3540))
 assert (bottom_pixels>2000) if max(r['native_bottom_cell_end'] for r in road_inputs)==160 else bottom_pixels==0
 cases.append(dict(alpha=float(alpha),bottom_row_pixels=bottom_pixels,commands=n,pixels=pixels,image_sha256=digest,packet_order_exact=True))
assert len({c['image_sha256'] for c in cases})==3
report=dict(result='PASS',cases=cases,scope='Three complete offline sampled draw traces assembled and rendered with exact packet command source order. Experimental continuous rectangular road geometry clipping; bottom clipping expanded only to native span pixel-cell end; lateral padding/seam and final fidelity policy unverified; no live native eligibility,60fps timing or playable port claim.')
(p/'road-native-bottom-render-tests.json').write_text(json.dumps(report,indent=2));print(report)
