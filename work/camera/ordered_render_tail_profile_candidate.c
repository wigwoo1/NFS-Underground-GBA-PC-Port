#include <windows.h>
#include <stdint.h>
#include <stddef.h>
typedef int(*Sky)(void*,void*);
typedef int(*World)(void*,unsigned,size_t,void*,size_t,void*,size_t,void*,unsigned,size_t);
typedef int(*Hud)(void*,void*,void*,void*);
typedef struct{void*sky;void*world;void*hud;void*sky_info;void*sky_copy;void*hud_info;void*hud_copy;void*hud_count;void*hud_batches;void*vertices;unsigned nv;size_t vb;void*offsets;size_t ob;void*ids;size_t ib;void*states;unsigned nd;size_t sb;} Tail;
__declspec(dllexport) int nf_ordered_render_tail_profile(const Tail*j,size_t bytes,unsigned*failed,uint64_t*clocks){
 if(!j||bytes!=sizeof(*j)||!failed||!clocks)return 37;
 for(unsigned i=0;i<7;i++)clocks[i]=0;
 if(!j->sky||!j->world||!j->hud||!j->sky_info||!j->sky_copy||!j->hud_info||!j->hud_copy||!j->hud_count||!j->hud_batches||!j->vertices||!j->offsets||!j->ids||!j->states||j->nv>65536||j->nd>4096||j->vb!=(size_t)j->nv*40||j->ob!=((size_t)j->nd+1)*4||j->ib!=(size_t)j->nd*4||j->sb!=(size_t)j->nd*72)return 37;
 LARGE_INTEGER frequency,t;QueryPerformanceFrequency(&frequency);clocks[0]=(uint64_t)frequency.QuadPart;
 QueryPerformanceCounter(&t);clocks[1]=(uint64_t)t.QuadPart;
 *failed=1;int r=((Sky)j->sky)(j->sky_info,j->sky_copy);QueryPerformanceCounter(&t);clocks[2]=(uint64_t)t.QuadPart;if(r)return r;
 QueryPerformanceCounter(&t);clocks[3]=(uint64_t)t.QuadPart;
 *failed=2;r=((World)j->world)(j->vertices,j->nv,j->vb,j->offsets,j->ob,j->ids,j->ib,j->states,j->nd,j->sb);QueryPerformanceCounter(&t);clocks[4]=(uint64_t)t.QuadPart;if(r)return r;
 QueryPerformanceCounter(&t);clocks[5]=(uint64_t)t.QuadPart;
 *failed=3;r=((Hud)j->hud)(j->hud_info,j->hud_copy,j->hud_count,j->hud_batches);QueryPerformanceCounter(&t);clocks[6]=(uint64_t)t.QuadPart;if(r)return r;
 *failed=0;return 0;
}
