from pathlib import Path
p=Path('work/camera/owned_gpu_sky_stage_candidate.c');s=p.read_text();lines=s.splitlines();exports=[x for x in lines if x.startswith('__declspec(dllexport) int nf_sky_stage_')];assert len(exports)==2
s='\n'.join(x for x in lines if x not in exports)+'\n'
exports=[x.replace('if(enabled<0||enabled>1)','if(gpu_owner!=GetCurrentThreadId()||wglGetCurrentContext()!=preview_context||enabled<0||enabled>1)').replace('||!wglGetCurrentContext()','||gpu_owner!=GetCurrentThreadId()||wglGetCurrentContext()!=preview_context') for x in exports];p.write_text(s+'\n'.join(exports)+'\n')
