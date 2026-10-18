/* Separate translation unit: measure repeated native calls without Python dispatch. */
#include "obj_tile.h"
__declspec(dllexport) int nf_obj_scanline_repeat(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,const uint8_t*o,size_t on,uint16_t display,unsigned row,const uint16_t window[6],unsigned blend,unsigned brightness,uint32_t*out,uint32_t*meta,uint8_t*controls,uint8_t*backdrop,unsigned repeats){
 if(!repeats||repeats>4096)return 0;
 for(unsigned i=0;i<repeats;i++)if(!nf_obj_window_scanline_prepared(v,vn,p,pn,o,on,display,row,window,blend,brightness,out,meta,controls,backdrop))return 0;
 return 1;
}
