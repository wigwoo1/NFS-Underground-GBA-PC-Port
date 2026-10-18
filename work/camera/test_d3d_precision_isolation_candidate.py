from pathlib import Path
import subprocess,json
p=Path('work/camera');base=(p/'owned_d3d_texel_load_candidate.c').read_text();test=(p/'test_d3d_texel_load_candidate.py').read_text();gcc='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin/gcc.exe';prefix='-BC:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin/'
variants={
 'precise':base.replace('o.p=float4','precise float2 pos=float2').replace(',.5,1);o.uv',');o.p=float4(pos,.5,1);o.uv').replace('float2 uv=i.uv.xy/i.uv.w','precise float2 uv=i.uv.xy/i.uv.w'),
 'matrix_load':base.replace('(i.p.x-ortho.x)/(ortho.y-ortho.x)*2-1,(i.p.y-ortho.z)/(ortho.w-ortho.z)*2-1','i.p.x*ortho.x+ortho.y,i.p.y*ortho.z+ortho.w').replace('load_config[7]=(float)sampling;','load_config[7]=(float)sampling;load_config[0]=(float)(2.0/((double)config[1]-config[0]));load_config[1]=(float)(-((double)config[1]+config[0])/((double)config[1]-config[0]));load_config[2]=(float)(2.0/((double)config[3]-config[2]));load_config[3]=(float)(-((double)config[3]+config[2])/((double)config[3]-config[2]));')
}
results=[]
for name,s in variants.items():
 stem='owned-d3d-'+name.replace('_','-')+'-candidate';src=p/(stem+'.c');dll=p/(stem+'.dll');src.write_text(s)
 subprocess.run([gcc,prefix,'-O2','-shared',str(src),'-o',str(dll),'-ld3d11','-ldxgi','-ld3dcompiler','-luuid'],check=True)
 t=p/('test_d3d_'+name+'_candidate.py');t.write_text(test.replace('owned-d3d-texel-load-candidate.dll',stem+'.dll').replace('d3d-texel-load-world-','d3d-'+name+'-world-'))
 subprocess.run([__import__('sys').executable,str(t)],check=True,capture_output=True)
 r=json.loads((p/'prototype-runs'/('d3d-'+name+'-world-component.json')).read_text());results.append(dict(variant=name,different_pixels=[f['different_pixels'] for f in r['frames']],cleanup=r['stats_after_close']))
(p/'prototype-runs/d3d-precision-isolation.json').write_text(json.dumps(results,indent=2));print(results)
