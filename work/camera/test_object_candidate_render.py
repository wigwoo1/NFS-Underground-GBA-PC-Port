from pathlib import Path
import ctypes as C,struct,json,os,subprocess,math
from PIL import Image,ImageChops
p=Path(__file__).resolve().parent
d=C.CDLL(str(p/'candidate-packet-test.dll'))
d.nf_scene_packet_insert_wall.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
d.nf_scene_packet_free.argtypes=[C.c_void_p]
def sections(raw):return {t:raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+i*12) for i in range(5))}
results=[]
for scene in (122,143):
 stem=p/f'object-replay-{scene}';meta=json.loads(Path(str(stem)+'.json').read_text())
 raw=Path(str(stem)+'-old.bin').read_bytes();surface=(p/f'object-candidate-{scene}.bin').read_bytes()
 out=C.c_void_p();size=C.c_size_t();identity=(C.c_uint32*5)(*meta['identity'])
 assert d.nf_scene_packet_insert_wall(raw,len(raw),surface,len(surface),identity,meta['slot'],C.byref(out),C.byref(size))
 expanded=C.string_at(out,size.value);d.nf_scene_packet_free(out);Path(str(stem)+'.bin').write_bytes(expanded)
 original=sections(raw);s=sections(expanded);count=struct.unpack_from('<I',s[2],4)[0]
 indexed=[[0]*4 for _ in range(count)];ordinal=0
 for index in struct.unpack_from('<'+'I'*count,original[3],8):
  if index!=0xffffffff:indexed[index]=meta['bounds'][ordinal*4:ordinal*4+4];ordinal+=1
 indexed[-1]=meta['candidate_bounds'];h=struct.unpack_from('<8I',expanded)
 images=[]
 for label in ('shown','hidden','unclipped','isolated','isolated-hidden'):
  clips=struct.pack('<5Id',0x3150434e,h[4],h[5],h[6],count,.5)
  for i in range(count):clips+=s[5][8+i*20:28+i*20]+struct.pack('<4H',*([0]*4 if label in ('hidden','isolated-hidden') and i==count-1 else [0,240,0,160] if label in ('unclipped','isolated') and i==count-1 else indexed[i]))
  clip=Path(str(stem)+f'-{label}.clips');clip.write_bytes(clips)
  env=os.environ.copy();env.update(NF_CAPTURE_CLIPS=str(clip),NF_PREVIEW_PHASE='2',NF_PREVIEW_FRACTION='.5')
  env['NF_ONLY_SURFACE']=str(count-1)
  executable='isolated-clip-preview.exe' if label.startswith('isolated') else 'sampled-clip-preview.exe'
  prefix=str(stem)+f'-{label}'
  subprocess.run([str(p/executable),str(stem)+'.bin',str(stem)+'-new.bin',prefix],env=env,check=True,capture_output=True)
  with Image.open(prefix+'-2.ppm') as image:images.append(image.convert('RGB'))
 diff=ImageChops.difference(images[0],images[1]);changed=sum(rgb!=(0,0,0) for rgb in diff.get_flattened_data())
 bbox=diff.getbbox();l,r,t,bottom=meta['candidate_bounds']
 scissor=(math.ceil(300+l*13.5-.5),2160-math.ceil((160-t)*13.5-.5),math.ceil(300+r*13.5-.5),2160-math.ceil((160-bottom)*13.5-.5))
 if bbox:assert bbox[0]>=scissor[0] and bbox[1]>=scissor[1] and bbox[2]<=scissor[2] and bbox[3]<=scissor[3]
 unbounded=ImageChops.difference(images[2],images[1]);unbounded_count=sum(rgb!=(0,0,0) for rgb in unbounded.get_flattened_data())
 images[0].save(str(stem)+'-shown.png')
 isolated=ImageChops.difference(images[3],images[4]);isolated_count=sum(rgb!=(0,0,0) for rgb in isolated.get_flattened_data())
 results.append(dict(isolated_pixels=isolated_count,isolated_bbox=isolated.getbbox(),scene=scene,changed_pixels=changed,bbox=bbox,scissor=scissor,unclipped_pixels=unbounded_count,unclipped_bbox=unbounded.getbbox(),queue_entrants=meta['queue_entrants'],bounds=meta['candidate_bounds']))
report=dict(result='PASS',cases=results,scope='Diagnostic object packet render with candidate-hidden controls; no live object integration or independent fidelity proof.')
(p/'object-candidate-render-tests.json').write_text(json.dumps(report,indent=2));print(report)
