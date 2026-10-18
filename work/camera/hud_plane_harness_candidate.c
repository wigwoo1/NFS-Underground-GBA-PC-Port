#include "obj_tile_plane_candidate.h"
#include "layer_snapshot.h"
#include <string.h>
__declspec(dllexport) int nf_hud_rows(const void*data,size_t n,void*out,unsigned repeats){
 if(!data||n!=160*sizeof(NFHudLayerRow)||!out||!repeats||repeats>100)return 0;
 const NFHudLayerRow*r=data;uint8_t vram[0x18000]={0};uint8_t*dst=out;
 for(unsigned k=0;k<repeats;k++)for(unsigned y=0;y<160;y++){
  if(r[y].row!=y||r[y].refresh!=r[0].refresh)return 0;
  unsigned display=r[y].registers[0]|r[y].registers[1]<<8;
  unsigned blend=r[y].registers[0x50]|r[y].registers[0x51]<<8,brightness=r[y].registers[0x54]|r[y].registers[0x55]<<8;
  uint16_t window[6];for(unsigned j=0;j<6;j++)window[j]=r[y].registers[64+2*j]|r[y].registers[65+2*j]<<8;

  uint32_t colors[240],tags[240];uint8_t controls[240],backdrop[240];
  if(!nf_obj_plane_window_scanline_prepared(r[y].obj_vram,sizeof(r[y].obj_vram),r[y].palette,1024,r[y].oam,1024,display,y,window,blend,brightness,colors,tags,controls,backdrop))return 0;
  uint8_t*d=dst+y*2400;memcpy(d,colors,960);memcpy(d+960,tags,960);memcpy(d+1920,controls,240);memcpy(d+2160,backdrop,240);
 }return 1;
}
