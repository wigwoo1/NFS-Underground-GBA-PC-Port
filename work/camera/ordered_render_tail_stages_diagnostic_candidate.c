#include <stdint.h>
#include <stddef.h>
typedef int(*Sky)(void*,void*);
typedef int(*World)(void*,unsigned,size_t,void*,size_t,void*,size_t,void*,unsigned,size_t);
typedef int(*Hud)(void*,void*,void*,void*);
typedef struct{void*sky;void*world;void*hud;void*sky_info;void*sky_copy;void*hud_info;void*hud_copy;void*hud_count;void*hud_batches;void*vertices;unsigned nv;size_t vb;void*offsets;size_t ob;void*ids;size_t ib;void*states;unsigned nd;size_t sb;} Tail;
__declspec(dllexport) int nf_ordered_render_tail_stages(const Tail*j,size_t bytes,unsigned*failed,int(*read)(void*,size_t),void*a,void*b,void*c){
 if(!j||bytes!=sizeof(*j)||!failed||!read||!a||!b||!c)return 37;
 if(!j->sky||!j->world||!j->hud||!j->sky_info||!j->sky_copy||!j->hud_info||!j->hud_copy||!j->hud_count||!j->hud_batches||!j->vertices||!j->offsets||!j->ids||!j->states||j->nv>65536||j->nd>4096||j->vb!=(size_t)j->nv*40||j->ob!=((size_t)j->nd+1)*4||j->ib!=(size_t)j->nd*4||j->sb!=(size_t)j->nd*72)return 37;
 *failed=1;int r=((Sky)j->sky)(j->sky_info,j->sky_copy);if(r)return r;
 if(read(a,3840u*2160u*4u))return 90;
 *failed=2;r=((World)j->world)(j->vertices,j->nv,j->vb,j->offsets,j->ob,j->ids,j->ib,j->states,j->nd,j->sb);if(r)return r;
 if(read(b,3840u*2160u*4u))return 91;
 *failed=3;r=((Hud)j->hud)(j->hud_info,j->hud_copy,j->hud_count,j->hud_batches);if(r)return r;
 if(read(c,3840u*2160u*4u))return 92;
 *failed=0;return 0;
}
