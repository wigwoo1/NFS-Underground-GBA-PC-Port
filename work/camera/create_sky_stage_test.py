from pathlib import Path
p=Path('work/camera');s=(p/'test_source_sky_target_selection.py').read_text().replace('owned-sky-source-context-candidate.dll','owned-sky-stage-candidate.dll').replace('source-sky-target-selection-20261007','sky-stage-reference-20261007')
s=s.replace('assert d.nf_owned_gpu_window(0)==0','assert d.nf_owned_gpu_window(0)==0\n assert d.nf_sky_stage_mode(1)==0\n d.nf_sky_stage_read.argtypes=[C.c_uint64,C.c_uint64,C.c_void_p,C.c_size_t]')
s=s.replace('retained.append((token.value,pixels))','''from owned_sky_sampler import SkySamples
  from owned_sky_color import sky_rgba
  palettes=b''.join(frame[40+gn+y*34944+32896:40+gn+y*34944+32896+512] for y in range(160))
  reference=sky_rgba(SkySamples(lower,upper,weight,0x06002940),palettes)
  stage=C.create_string_buffer(912);assert d.nf_sky_stage_read(token.value,epoch,stage,len(stage))==0
  at=0;maximum=0
  for sy in range(44,107,4):
   for sx in range(8,232,12):
    ref=((sy-44)*240+sx)*4
    error=max(abs(a-b) for a,b in zip(stage.raw[at:at+3],reference[ref:ref+3]));maximum=max(maximum,error);at+=3
  assert maximum<=1,(weight,maximum)
  checks.append(dict(weight=weight,sky_stage_points=304,max_channel_error=maximum))
  retained.append((token.value,pixels))''')
(p/'test_sky_stage_reference.py').write_text(s)
