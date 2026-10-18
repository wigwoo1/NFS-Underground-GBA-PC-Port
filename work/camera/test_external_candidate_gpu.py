"""4K GPU boundary test for complete external car candidates, not gameplay."""
import runpy,sys,ctypes as C,struct,hashlib,json
from pathlib import Path
v=runpy.run_path('work/camera/test_external_record_candidate.py')
from owned_external_source_motion import PreparedExternalSourceMotion
from owned_model_sources import OwnedModelSources
from owned_sampled_supplemental_frame import encode
scenes=v['scenes'];captures=v['captures'];frames=v['frames'];blocks=v['blocks'];portal=v['portal']
sources=[OwnedModelSources.decode(Path(c['current-sources']).read_bytes(),s) for c,s in zip(captures,scenes)]
motion=PreparedExternalSourceMotion(scenes,sources,1)
d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()))
d.nf_owned_gpu_draw_surface_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint]
d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t]
rgb=C.create_string_buffer(3840*2160*3);fingerprints=[]
try:
 for i in range(101):
  alpha=i/100;region=next(q for q in portal.sample(alpha) if q[0]==23 and not q[5]&0x88)
  selected=list(blocks[0]);selected[9]=struct.pack('<4i',*(round(region[k]) for k in (1,3,2,4)))
  geometry=encode(dict(kind=3,context=0,blocks=selected));header=list(struct.unpack_from('<6I2Q',frames[0]));tail=frames[0][40+header[2]:];header[2]=len(geometry);frame=struct.pack('<6I2Q',*header)+geometry+tail
  from owned_scenery_motion import normalized_matrix
  sampled_camera=portal.motion.sample(alpha)[1]
  camera=(C.c_double*12)(*normalized_matrix(scenes[int(alpha)].graph.context[256:304])) if alpha in (0,1) else sampled_camera
  models=(C.c_double*12)(*motion.matrix(alpha));bounds=(C.c_double*4)()
  result=d.nf_owned_gpu_draw_surface_clips(frame,len(frame),camera,models,bounds,1)
  assert result==0,(alpha,result)
  assert d.nf_owned_gpu_read(rgb,len(rgb))==0
  fingerprints.append(hashlib.sha256(rgb.raw).hexdigest())
 Path(sys.argv[1]).with_suffix('.external-candidate-gpu.json').write_text(json.dumps(dict(samples=101,width=3840,height=2160,distinct_images=len(set(fingerprints)),limitation='Isolated complete opponent record with sampled parent portal; Rounded integer model clip bounds; no original activation gate or full-scene gameplay/timing claim.'),indent=2))
 assert len(set(fingerprints))>1,'No GPU pixel motion: evidence saved; birth interval may remain fully clipped'
 print('PASS101 isolated complete external car 4K GPU samples;',len(set(fingerprints)),'distinct images')
finally:d.nf_owned_gpu_close()
