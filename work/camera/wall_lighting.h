#include <math.h>
#include "narrow_wall_shading.h"
int nfs_wall_shade_column(const uint8_t*,int,const uint32_t*);
static uint32_t wall_reciprocal[32768];
static unsigned lighting_applied,lighting_fallback;
static unsigned lighting_range_fallback,lighting_narrow_fallback,lighting_sample_fallback;
static unsigned lighting_native_narrow;
static unsigned lighting_native_wide;
static int lighting_native_resolution=1; /* Set to zero only for reference comparisons. */
static int load_wall_lighting(const char*path){
 PreviewInput*f=preview_input(4,path);uint32_t header[2];if(!f||!read_bytes(f,header,8)||header[0]!=0x314c464e||header[1]!=road_count)return 0;
 for(unsigned i=0;i<road_count;i++){
  RoadPreview*r=roads+i;uint32_t enabled;if(!read_bytes(f,&enabled,4)||enabled>1)return 0;r->lit=enabled;if(enabled&&preview_world_indices[i])return 0;if(preview_wall_states[i]&&preview_wall_planes[i]!=(enabled?17u:1u))return 0;if(!enabled)continue;
  uint32_t info[4];if(!read_bytes(f,info,16)||info[0]>15||info[1]>15||!info[2]||info[2]>1024||!info[3]||info[3]>1024||r->count!=4)return 0;
  if(info[2]!=r->width||info[3]!=r->height)return 0;
  r->intensity[0]=info[0];r->intensity[1]=info[1];unsigned bytes=info[2]*info[3]*4;uint8_t*p=malloc(bytes);if(!p)return 0;
  for(unsigned level=0;level<16;level++){
   if(!read_bytes(f,p,bytes)){free(p);return 0;}
   size_t plane=(size_t)(level+1)*info[2]*info[3];r->variants[level]=preview_wall_states[i]?wall_indexed_texture(info[2],info[3],p,preview_wall_states[i]+plane,preview_wall_indices[i]?preview_wall_indices[i]+plane:NULL):preview_texture(info[2],info[3],p);if(!r->variants[level]){free(p);return 0;}
  }free(p);
 }
 int ok=read_bytes(f,wall_reciprocal,sizeof(wall_reciprocal))&&preview_end(f);preview_close(f);return ok;
}
static void wall_half(uint8_t*p,int value){uint16_t v=(uint16_t)value;p[0]=v;p[1]=v>>8;}
/* Geometry remains the shared-camera polygon. Scissors select only palette
   variants; they do not interpolate or displace individual screen polygons.
   out must hold 3240 entries. Returns 0 unavailable, 1 original 120 columns,
   or 2 native 3240 columns. Native shading across all spans avoids a visible
   intensity discontinuity at the original column-width threshold. */
static int wall_shades(const RoadPreview*r,const NFPoint3*camera,const double*projection,int*out){
 double x[2]={camera[0].x,camera[1].x},z[2]={camera[0].z,camera[1].z};
 double intensity[2]={r->intensity[0]*256.,r->intensity[1]*256.};
 if(z[0]<64&&z[1]<64)return 0;
 for(unsigned i=0;i<2;i++)if(z[i]<64){unsigned j=1-i;double t=(64-z[i])/(z[j]-z[i]);x[i]+=(x[j]-x[i])*t;intensity[i]+=(intensity[j]-intensity[i])*t;z[i]=64;}
 uint8_t edge[52]={0};int screen[2];double projected[2];
 for(unsigned i=0;i<2;i++){
  double p=projection[0]+projection[2]*x[i]/z[i];
  projected[i]=p;
  if(!isfinite(p)||p<-32760||p>32760||z[i]>32767){lighting_fallback++;lighting_range_fallback++;return 0;}
  screen[i]=(int)floor(p);wall_half(edge+4+i*2,(int)z[i]);wall_half(edge+40+i*2,(int)intensity[i]);
 }
 if(screen[0]>screen[1]){int t=screen[0];screen[0]=screen[1];screen[1]=t;wall_half(edge+48,2);}
 wall_half(edge,screen[0]);wall_half(edge+2,screen[1]);int left=screen[0]>>1,right=(screen[1]+1)>>1;
 if(lighting_native_resolution||right-left<=1){
  double levels[2]={intensity[0]/256.,intensity[1]/256.};
  if(nf_narrow_wall_shades(projected,z,levels,out,3240)){lighting_applied++;if(right-left<=1)lighting_native_narrow++;else lighting_native_wide++;return 2;}
  lighting_fallback++;lighting_narrow_fallback++;return 0;
 }
 for(int i=0;i<120;i++){
  int sample=i<left?left:i>=right?right-1:i;out[i]=nfs_wall_shade_column(edge,sample,wall_reciprocal);
  if(out[i]<0||out[i]>15){lighting_fallback++;lighting_sample_fallback++;return 0;}
 }lighting_applied++;return 1;
}

