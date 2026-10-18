from pathlib import Path
p=Path('work/camera/threaded_preview.c');s=p.read_text();s=s.replace('#include "menu_renderer_gpu.h"','#include "menu_renderer_gpu.h"\n#include "gpu_frame_timer.h"')
s=s.replace(' while(!r->result&&WaitForSingleObject(r->stop,0)!=WAIT_OBJECT_0){',' NFGpuTimer gpu_timer;if(!nf_gpu_timer_open(&gpu_timer,r->args[4]))r->result=19;\n while(!r->result&&WaitForSingleObject(r->stop,0)!=WAIT_OBJECT_0){',1)
needle='uint64_t begin=elapsed_ns();if(ordered||stable||motion)'
assert needle in s
s=s.replace(needle,'uint64_t begin=elapsed_ns();int gpu_slot=nf_gpu_timer_begin(&gpu_timer,time->epoch,time->target,nf_render_submission_kind(frame));if(gpu_slot==-2){nf_render_submission_destroy(frame);r->result=19;break;}if(ordered||stable||motion)',1)
s=s.replace('  if(!r->result)fprintf(components,','  if(!nf_gpu_timer_end(&gpu_timer,gpu_slot))r->result=19;\n  if(!r->result)fprintf(components,',1)
s=s.replace(' if(dense_cost&&fclose(dense_cost))',' if(!nf_gpu_timer_close(&gpu_timer))r->result=19;\n if(dense_cost&&fclose(dense_cost))',1)
p.write_text(s)
p=Path('work/camera/audit_threaded_racing_motion.py');s=p.read_text().replace("for flag in ['NF_TEST_ABOVE_NORMAL_THREADS'","for flag in ['NF_TEST_GPU_TIMESTAMPS','NF_TEST_ABOVE_NORMAL_THREADS'");p.write_text(s)
