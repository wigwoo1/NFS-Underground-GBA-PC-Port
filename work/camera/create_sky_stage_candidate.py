from pathlib import Path
p=Path('work/camera');s=(p/'owned_gpu_source_context_candidate.c').read_text();marker='static const uint8_t*sky_lower,*sky_upper;static double sky_weight;'
assert s.count(marker)==1
s=s.replace(marker,marker+'\nstatic uint8_t sky_stage_pixels[3][304*3];static int sky_stage_enabled;\n__declspec(dllexport) int nf_sky_stage_mode(int enabled){if(enabled<0||enabled>1)return 37;sky_stage_enabled=enabled;return 0;}\n__declspec(dllexport) int nf_sky_stage_read(uint64_t token,uint64_t epoch,void*out,size_t bytes){if(!out||bytes!=304*3||gpu_owner!=GetCurrentThreadId())return 31;for(unsigned i=0;i<3;i++)if(pool_tokens[i]==token&&pool_pinned[i]&&pool_epochs[i]==epoch){memcpy(out,sky_stage_pixels[i],bytes);return 0;}return 32;}')
# gpu_owner declared later: use current context ownership check via thread id declaration earlier.
s=s.replace('bytes!=304*3||gpu_owner!=GetCurrentThreadId()','bytes!=304*3||!wglGetCurrentContext()')
needle=' if(sky_stage_profile)sky_stage_ticks[1]=sky_stage_now();';assert s.count(needle)==1
s=s.replace(needle,''' if(sky_stage_enabled){unsigned at=0;glPixelStorei(GL_PACK_ALIGNMENT,1);for(unsigned sy=44;sy<107;sy+=4)for(unsigned sx=8;sx<232;sx+=12){unsigned x=(unsigned)(300+(sx+.5)*13.5),y=2159-(unsigned)((sy+.5)*13.5);glReadPixels(x,y,1,1,GL_RGB,GL_UNSIGNED_BYTE,sky_stage_pixels[owned_pool_slot]+at);at+=3;}if(at!=304*3||glGetError())return 8;}
'''+needle)
(p/'owned_gpu_sky_stage_candidate.c').write_text(s)
b=(p/'build-sky-gpu-candidate.ps1').read_text().replace('owned_gpu_sky_candidate.c','owned_gpu_sky_stage_candidate.c').replace('owned-sky-gpu.dll','owned-sky-stage-candidate.dll');(p/'build-sky-stage-candidate.ps1').write_text(b)
