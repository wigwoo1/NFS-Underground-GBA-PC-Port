import json,struct,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_complete_supplemental_candidates import CompleteSupplementalCandidates
from owned_complete_supplemental_gpu import sampled_gpu_records
from owned_complete_supplemental_sources import complete_wall_sources
from owned_motion_pairs import records
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_draw_wall_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);checks=[];draws=0;endpoint_pixels=0

def frame_with(frame,geometry):
 h=list(struct.unpack_from('<6I2Q',frame));tail=frame[40+h[2]:];g=b''.join(geometry);h[2]=len(g);return struct.pack('<6I2Q',*h)+g+tail

def encode(row):return struct.pack('<4I',0x3147534e,row['kind'],row['context'],12)+b''.join(struct.pack('<I',len(b))+bytes(b) for b in row['blocks'])
try:
 for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
  a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b);old=Path(fa['regenerated']).read_bytes();new=Path(fb['regenerated']).read_bytes();motion=PreparedMotionPair(old,new);portal=PortalMotionPair(a.graph,b.graph,table,motion);pair=CompleteSupplementalCandidates(a,b,sa,sb,portal,rom);samples=[]
  for alpha in (0,.25,.5,.75,1):
   selected=sampled_gpu_records(pair,alpha,rom);base=new if alpha==1 else old;frame=frame_with(base,[x['record'] for x in selected]);assert len(records(frame)['records'])==len(selected)
   if alpha in (0,1):
    c,s=(b,sb) if alpha==1 else (a,sa);keys={w.vertices for w in complete_wall_sources(c,s,rom)};reference=frame_with(base,[encode(row) for row in records(base)['records'] if row['kind']==2 and bytes(row['blocks'][0]) in keys])
    assert len(records(reference)['records'])==len(selected)
    if selected:
     code=d.nf_owned_gpu_draw(reference,len(reference));assert code==0,(a.refresh,alpha,len(selected),code);assert d.nf_owned_gpu_read(rgb,len(rgb))==0;expected=rgb.raw
     assert d.nf_owned_gpu_draw(frame,len(frame))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==expected;endpoint_pixels+=1
   elif alpha not in (0,1) and selected:
    _,camera,_=motion.sample(alpha);cam=(C.c_double*12)(*camera);models=(C.c_double*(12*len(selected)))();bounds=(C.c_double*(4*len(selected)))(*(v for x in selected for v in x['bounds']))
    assert d.nf_owned_gpu_draw_wall_clips(frame,len(frame),cam,models,bounds,len(selected))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0;draws+=1
   samples.append(dict(alpha=alpha,wall_records=len(selected),descriptors=[x['descriptor'] for x in selected]))
  checks.append(dict(older=a.refresh,newer=b.refresh,samples=samples))
finally:assert d.nf_owned_gpu_close()
out=dict(result='PASS_SAMPLED_SUPPLEMENTAL_GPU_REPLAY',endpoint_wall_only_frames_exact=endpoint_pixels,intermediate_gpu_draws=draws,checks=checks,scope='Supplemental-only diagnostic GPU replay with background/HUD retained; full-scene cross-kind ordering and live integration pending.')
Path('work/camera/sampled-supplemental-gpu-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],endpoint_pixels,draws)


