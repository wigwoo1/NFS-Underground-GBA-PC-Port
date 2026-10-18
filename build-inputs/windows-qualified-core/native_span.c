#include "native_span.h"
#ifdef _WIN32
__declspec(dllexport)
#endif
int nfs_draw_span(uint8_t* dst,size_t dst_size,const uint8_t* tex,size_t tex_size,NfsSpan* s){
 if(!dst || !tex || !s || s->width_shift>15 || s->count>120)return 0;
 size_t bytes=s->count*2;
 if(s->count && dst_size<bytes+(s->duplicate_row?240:0))return 0;
 uint32_t u=s->u,v=s->v;
 /* Use unsigned arithmetic: ARM's wraparound is intentional. Validate the
    whole span first so a rejected input cannot partially modify the output. */
 for(uint32_t i=0;i<s->count;i++){
  u&=s->u_mask;v&=s->v_mask;
  uint32_t off=((u>>16)+((v>>16)<<s->width_shift))*2;
  if((uint64_t)off+2>tex_size)return 0;
  u+=s->du;v+=s->dv;
 }
 u=s->u;v=s->v;
 for(uint32_t i=0;i<s->count;i++){
  u&=s->u_mask;v&=s->v_mask;
  uint32_t off=((u>>16)+((v>>16)<<s->width_shift))*2;
  dst[i*2]=tex[off];dst[i*2+1]=tex[off+1];
  if(s->duplicate_row){dst[i*2+240]=tex[off];dst[i*2+241]=tex[off+1];}
  u+=s->du;v+=s->dv;
 }
 s->u=u;s->v=v;return 1;
}
