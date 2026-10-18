import json,struct,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_complete_supplemental_candidates import CompleteSupplementalCandidates
from owned_complete_supplemental_gpu import endpoint_gpu_records
from owned_complete_supplemental_projection import projection_input
from owned_scene_bundle import chunks
from owned_live_wall_adapter import reconstruct
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);checks=[];palette_rejections=0
try:
 for index,f in enumerate(r['wall_diagnostic_frames']):
  c=ClosedGraph.decode(Path(f['graph']).read_bytes());s=ClosedSupplements.decode(Path(f['supplements']).read_bytes(),c);frame=Path(f['original']).read_bytes() if 'original' in f else Path(f['regenerated']).read_bytes()
  alpha=1 if index==len(r['wall_diagnostic_frames'])-1 else 0
  fa,fb=(r['wall_diagnostic_frames'][index-1],f) if alpha else (f,r['wall_diagnostic_frames'][index+1])
  a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b)
  motion=PreparedMotionPair(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes());portal=PortalMotionPair(a.graph,b.graph,table,motion);pair=CompleteSupplementalCandidates(a,b,sa,sb,portal,rom)
  generated=endpoint_gpu_records(c,s,rom,pair.sample(alpha),table)
  restored,count=reconstruct(frame,c,s,table,supplemental_records=generated)
  reference,_=reconstruct(frame,c,s,table)
  if restored!=reference:
   from owned_motion_pairs import records
   left=records(restored)['records'];right=records(reference)['records']
   print('difference',c.refresh,[(i,j,len(x),len(y),next((k for k,(u,v) in enumerate(zip(x,y)) if u!=v),None)) for i,(la,rb) in enumerate(zip(left,right)) for j,(x,y) in enumerate(zip(la['blocks'],rb['blocks'])) if x!=y]);raise AssertionError('record mismatch')
  assert d.nf_owned_gpu_draw(frame,len(frame))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0;expected=rgb.raw
  assert d.nf_owned_gpu_draw(restored,len(restored))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0;assert rgb.raw==expected
  # Changing only discarded index0 must leave every4Kpixel unchanged.
  from owned_motion_pairs import records
  geometry=[]
  for row in records(restored)['records']:
   blocks=[bytes(x) for x in row['blocks']]
   if row['kind']==2:
    palette=bytearray(blocks[9]);palette[0]^=255;palette[1]^=127;blocks[9]=bytes(palette)
   geometry.append(struct.pack('<4I',0x3147534e,row['kind'],row['context'],12)+b''.join(struct.pack('<I',len(x))+x for x in blocks))
  header=list(struct.unpack_from('<6I2Q',restored));g=b''.join(geometry);assert len(g)==header[2]
  altered=restored[:40]+g+restored[40+header[2]:]
  assert d.nf_owned_gpu_draw(altered,len(altered))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==expected
  checks.append(dict(refresh=c.refresh,complete_supplemental_records=len(generated),walls=count,pixels_exact=8294400))
finally:assert d.nf_owned_gpu_close()
out=dict(result='PASS_COMPLETE_SUPPLEMENTAL_ENDPOINT_GPU',checks=checks,scope='Complete-source selection/regeneration with original cross-kind placement; endpoint pixels exact. Intermediate insertion/removal and independent cross-kind order pending.')
Path('work/camera/complete-supplemental-gpu-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],len(checks))



