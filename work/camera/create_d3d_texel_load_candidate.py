from pathlib import Path
p=Path('work/camera');s=(p/'owned_d3d_source_gpu_candidate.c').read_text()
s=s.replace('if(flags.x>0)c*=asset.SampleLevel(sampling,i.uv.xy/i.uv.w,0);','if(flags.x>0){uint w,h;asset.GetDimensions(w,h);float2 uv=i.uv.xy/i.uv.w;int2 t=(int2)floor(uv*float2(w,h));int mode=(int)flags.w;t.x=(mode&1)?((t.x%(int)w+(int)w)%(int)w):clamp(t.x,0,(int)w-1);t.y=(mode&2)?((t.y%(int)h+(int)h)%(int)h):clamp(t.y,0,(int)h-1);c*=asset.Load(int3(t,0));}')
s=s.replace('ID3D11DeviceContext_UpdateSubresource(ctx,(ID3D11Resource*)constants,0,NULL,config,0,0);','float load_config[8];memcpy(load_config,config,32);load_config[7]=(float)sampling;ID3D11DeviceContext_UpdateSubresource(ctx,(ID3D11Resource*)constants,0,NULL,load_config,0,0);')
(p/'owned_d3d_texel_load_candidate.c').write_text(s)
s=(p/'test_d3d_source_world_candidate.py').read_text().replace('owned-d3d-source-gpu-candidate.dll','owned-d3d-texel-load-candidate.dll').replace('d3d-source-world-','d3d-texel-load-world-')
(p/'test_d3d_texel_load_candidate.py').write_text(s)
