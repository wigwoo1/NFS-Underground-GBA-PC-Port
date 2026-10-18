"""Owned22-record scene asset coverage and isolated new-wall rendering."""
from pathlib import Path
import ctypes as C,struct,json,hashlib,os,subprocess,collections
from PIL import Image,ImageChops
p=Path('work/camera').resolve();f=p/'overflow-scene-171';m=json.loads((f/'manifest.json').read_text())
result=(f/'visibility.bin').read_bytes();batch=(f/'queue-plans.bin').read_bytes()
assert len(result)==4868 and len(batch)==66180 and struct.unpack_from('<H',result,238)[0]==22
assert result[256:256+22*16]==(p/'visibility-overflow-171/original-queue-0.5.bin').read_bytes()
assert not m['missing_wall_assets']
for source,a in m['assets'].items():
 b=(f/f'wall-{source}.bin').read_bytes();v,w,h=struct.unpack_from('<3I',b)
 assert len(b)==a['bytes']==12+v*40+w*h*4 and hashlib.sha256(b).hexdigest()==a['sha256']
 assert a['identity'][2]==int(source) and a['identity'][1]==m['state']
for o in m['occurrences']:
 assert str(o['source']) in m['assets'];off=4+o['queue_index']*2068
 assert struct.unpack_from('<2I',batch,off+20+o['draw_index']*32)==(o['source'],o['phase'])
for source,a in m['road_assets'].items():
 b=(f/f'road-{source}.bin').read_bytes();assert len(b)==a['bytes'] and hashlib.sha256(b).hexdigest()==a['sha256']
new_sources=[int(k) for k,v in m['assets'].items() if v['origin']=='owned candidate'];assert new_sources==[139913036,139913240]
old=(f/'old.bin').read_bytes();new=(f/'new.bin').read_bytes();world=next(old[o:o+n] for t,o,n in (struct.unpack_from('<3I',old,32+i*12) for i in range(5)) if t==2);n=struct.unpack_from('<I',world,4)[0]
d=C.CDLL(str(p/'candidate-packet-test.dll'));d.nf_scene_packet_insert_wall.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p];d.nf_scene_packet_free.argtypes=[C.c_void_p]
raw=old;bounds=[[0,240,0,160] for _ in range(n)]
for source in new_sources:
 a=m['assets'][str(source)];asset=(f/f'wall-{source}.bin').read_bytes();out=C.c_void_p();size=C.c_size_t()
 assert d.nf_scene_packet_insert_wall(raw,len(raw),asset,len(asset),(C.c_uint32*5)(*a['identity']),0,C.byref(out),C.byref(size))
 try:raw=C.string_at(out,size.value)
 finally:d.nf_scene_packet_free(out)
 bounds.append(next(o['bounds'] for o in m['occurrences'] if o['source']==source))
(f/'isolated-input.bin').write_bytes(raw)
header=struct.unpack_from('<8I',raw);clips=struct.pack('<5Id',0x3150434e,*header[4:7],len(bounds),.5)
identity_section=next(raw[o:o+size] for t,o,size in (struct.unpack_from('<3I',raw,32+i*12) for i in range(5)) if t==5)
for index,b in enumerate(bounds):clips+=identity_section[8+index*20:28+index*20]+struct.pack('<4H',*b)
(f/'isolated.clips').write_bytes(clips)
env=os.environ.copy();env.update(NF_CAPTURE_CLIPS=str(f/'isolated.clips'),NF_PREVIEW_FRACTION='.5',NF_PREVIEW_PHASE='2')
cases=[]
for index in [999]+list(range(n,n+2)):
 env['NF_ONLY_SURFACE']=str(index);prefix=f/f'isolated-{index}'
 subprocess.run([str(p/'isolated-clip-preview.exe'),str(f/'isolated-input.bin'),str(f/'new.bin'),str(prefix)],env=env,check=True,capture_output=True)
 with Image.open(str(prefix)+'-2.ppm') as im:image=im.convert('RGB');assert image.size==(3840,2160)
 if index==999:empty=image;continue
 diff=ImageChops.difference(image,empty);pixels=sum(v!=(0,0,0) for v in diff.get_flattened_data())
 cases.append(dict(source=new_sources[index-n],pixels=pixels,bbox=diff.getbbox()))
report=dict(result='PASS',queue_records=22,wall_occurrences=len(m['occurrences']),unique_wall_assets=len(m['assets']),road_assets=len(m['road_assets']),isolated=cases,scope='Complete queue asset coverage plus isolated new walls at midpoint. Synthetic command positions only for isolated testing; full-scene order, object and road eligibility remain unverified.')
(p/'overflow-scene-render-tests.json').write_text(json.dumps(report,indent=2));print(report)
