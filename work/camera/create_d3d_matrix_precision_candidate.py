from pathlib import Path
p=Path('work/camera')
s=(p/'owned_d3d_source_gpu_candidate.c').read_text()
s=s.replace('(i.p.x-ortho.x)/(ortho.y-ortho.x)*2-1,(i.p.y-ortho.z)/(ortho.w-ortho.z)*2-1','i.p.x*ortho.x+ortho.y,i.p.y*ortho.z+ortho.w')
s=s.replace('ID3D11DeviceContext_UpdateSubresource(ctx,(ID3D11Resource*)constants,0,NULL,config,0,0);','float matrix_config[8];memcpy(matrix_config,config,32);matrix_config[0]=(float)(2.0/((double)config[1]-config[0]));matrix_config[1]=(float)(-((double)config[1]+config[0])/((double)config[1]-config[0]));matrix_config[2]=(float)(2.0/((double)config[3]-config[2]));matrix_config[3]=(float)(-((double)config[3]+config[2])/((double)config[3]-config[2]));ID3D11DeviceContext_UpdateSubresource(ctx,(ID3D11Resource*)constants,0,NULL,matrix_config,0,0);')
(p/'owned_d3d_matrix_precision_candidate.c').write_text(s)
s=(p/'test_d3d_source_world_candidate.py').read_text().replace('owned-d3d-source-gpu-candidate.dll','owned-d3d-matrix-precision-candidate.dll').replace('d3d-source-world-','d3d-matrix-world-').replace('d3d-source-world-component.json','d3d-matrix-world-component.json')
(p/'test_d3d_matrix_precision_candidate.py').write_text(s)
s=(p/'capture_gl_source_world_reference_candidate.py').read_text();s=s.replace("expected=images[:]", "expected=None")
a=s.index(" result=dict(result='PASS_WORLD_ONLY_REFERENCE_CAPTURE'");b=s.index('\nfinally:',a)
s=s[:a]+" result=dict(result='WORLD_ONLY_REFERENCE_CAPTURE',captured_frames=len(images),images=images,scope='Captured GL world/sky images with HUD draws excluded; this creates reference data and is not a parity test.');(run/'gl-source-world-reference.json').write_text(json.dumps(result,indent=2));print(result);assert len(images)==5"+s[b:]
(p/'capture_gl_source_world_reference_candidate.py').write_text(s)
