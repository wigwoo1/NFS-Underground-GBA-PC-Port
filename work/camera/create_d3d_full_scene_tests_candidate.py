from pathlib import Path
p=Path('work/camera');s=(p/'capture_gl_source_world_reference_candidate.py').read_text().replace("   if op['program']:continue\n",'').replace('gl-source-world-','gl-source-full-').replace('gl-source-world-reference.json','gl-source-full-reference.json').replace('WORLD_ONLY_REFERENCE_CAPTURE','FULL_SCENE_REFERENCE_CAPTURE').replace('with HUD draws excluded','including HUD draws')
(p/'capture_gl_source_full_reference_candidate.py').write_text(s)
s=(p/'test_d3d_hud_copy_world_candidate.py').read_text().replace('owned-d3d-hud-copy-candidate.dll','owned-d3d-full-scene-candidate.dll').replace("   if op['program']:skipped_hud+=1;continue\n",'')
s=s.replace('textures={};frames=[];',"d.nf_d3d_hud_shader.argtypes=[P,C.c_size_t];d.nf_d3d_hud_draw.argtypes=[P,C.c_uint,P,P,P,P];code=(p/'owned-d3d-hud-effect-candidate.cso').read_bytes();assert d.nf_d3d_hud_shader(code,len(code))==0\ntextures={};frames=[];")
s=s.replace("  elif kind=='clear':", "  elif kind=='copy_render_target':\n   assert list(map(int,op['args']))==[3553,0,0,0,0,0,3840,2160];assert d.nf_d3d_copy_target(op['target'][0])==0\n  elif kind=='clear':")
old='   assert d.nf_d3d_draw(vertices.ctypes.data,len(vertices),tid,mode,int(0x0be2 in enabled),config,rect)==0'
new='''   if op['program']:
    u=op['uniforms'];ids=(C.c_uint*4)(*[op['textures'][str(int(u[n][0]))]['resource'][0] for n in ('candidateColor','candidateMetadata','nativeBackground','ownedText')]);values=[]
    for n in ('backdropColor','effectParameters','firstTargets','secondTargets','coefficients'):values.extend(u[n])
    import struct
    params=C.create_string_buffer(struct.pack('<20fi3f',*values,int(u['ownedTextEnabled'][0]),0,0,0));config[4]=0
    assert d.nf_d3d_hud_draw(vertices.ctypes.data,len(vertices),ids,params,config,rect)==0;skipped_hud+=1
   else:assert d.nf_d3d_draw(vertices.ctypes.data,len(vertices),tid,mode,int(0x0be2 in enabled),config,rect)==0'''
s=s.replace(old,new).replace('gl-source-world-','gl-source-full-').replace('d3d-hud-copy-world-','d3d-full-scene-').replace('skipped_hud_draws=skipped_hud','executed_hud_draws=skipped_hud').replace('Source-world/sky component only; full-scene HUD, live presentation, 60fps, physical4K and Xbox not verified.','Full-scene offscreen component including HUD; live presentation, 60fps, physical4K and Xbox not verified.')
(p/'test_d3d_full_scene_candidate.py').write_text(s)
