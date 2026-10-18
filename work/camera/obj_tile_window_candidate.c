#include "obj_tile.h"
#include <string.h>
int nf_obj_tile(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,unsigned tile,unsigned color8,unsigned bank,unsigned bitmap,uint32_t out[64]){
 if(!v||!p||!out||vn<0x18000||pn<1024||tile>=1024||color8>1||bank>15||bitmap>1||(bitmap&&tile<512))return 0;
 if(color8)tile&=~1u;
 size_t base=0x10000u+tile*32u,bytes=color8?64:32;if(base+bytes>vn||base+bytes>0x18000)return 0;
 uint32_t result[64];for(unsigned i=0;i<64;i++){
  unsigned index=color8?v[base+i]:(v[base+i/2]>>(4*(i&1)))&15u;
  if(!index){result[i]=0;continue;}
  unsigned offset=512+2*(index+(color8?0:bank*16));unsigned c=p[offset]|((unsigned)p[offset+1]<<8);
  unsigned r=c&31,g=(c>>5)&31,b=(c>>10)&31;result[i]=((r<<3)|(r>>2))|(((g<<3)|(g>>2))<<8)|(((b<<3)|(b>>2))<<16)|0xff000000u;
 }memcpy(out,result,sizeof(result));return 1;
}

/* Regular sprite asset only; affine/window/priority/blend composition is separate. */
__declspec(dllexport) int nf_obj_image(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,uint16_t a,uint16_t b,uint16_t c,uint16_t display,uint32_t*out,size_t capacity,unsigned dimensions[2]){
 static const unsigned sizes[3][4][2]={{{8,8},{16,16},{32,32},{64,64}},{{16,8},{32,8},{32,16},{64,32}},{{8,16},{8,32},{16,32},{32,64}}};
 unsigned shape=a>>14,size=b>>14,color8=(a>>13)&1,tile=c&1023,bitmap=(display&7)>=3;
 if(!v||!p||!out||!dimensions||vn<0x18000||pn<1024||shape>=3||(a&0x300)||((a>>10)&3)>=2||(bitmap&&tile<512))return 0;
 unsigned w=sizes[shape][size][0],h=sizes[shape][size][1];if(capacity<w*h)return 0;
 unsigned one=!!(display&64),charbase=(tile&~(unsigned)(color8&&!one))*32,masklo=one?0x7fff:0x3ff,maskhi=one?0:charbase&0x7c00,stride=one?(w>>(1-color8)):128;
 uint32_t result[4096];for(unsigned y=0;y<h;y++)for(unsigned x=0;x<w;x++){
  unsigned lx=(b&0x1000)?w-1-x:x,ly=(b&0x2000)?h-1-y:y;
  unsigned ybase=(ly&~7u)*stride+(ly&7u)*(color8?8:4)+maskhi;
  unsigned xbase=(lx&~7u)*(color8?8:4)+(lx&7u)/(color8?1:2);
  unsigned address=0x10000+((ybase+((xbase+charbase)&masklo))&0x7fff);
  unsigned index=color8?v[address]:(v[address]>>(4*(lx&1)))&15;
  if(!index){result[y*w+x]=0;continue;}unsigned off=512+2*(index+(color8?0:(c>>12)*16)),rgb=p[off]|((unsigned)p[off+1]<<8),r=rgb&31,g=(rgb>>5)&31,blue=(rgb>>10)&31;
  result[y*w+x]=((r<<3)|(r>>2))|(((g<<3)|(g>>2))<<8)|(((blue<<3)|(blue>>2))<<16)|0xff000000;
 }memcpy(out,result,w*h*4);dimensions[0]=w;dimensions[1]=h;return 1;
}

#include <stdlib.h>
__declspec(dllexport) int nf_obj_affine_image(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,uint16_t a,uint16_t b,uint16_t c,uint16_t display,const int16_t matrix[4],uint32_t*out,size_t capacity,unsigned dimensions[2]){
 if(!(a&256)||!matrix||!out||!dimensions)return 0;
 uint32_t source[4096];unsigned dims[2];if(!nf_obj_image(v,vn,p,pn,a&~0x300u,b&~0x3000u,c,display,source,4096,dims))return 0;
 unsigned w=dims[0],h=dims[1],dw=w*((a&512)?2:1),dh=h*((a&512)?2:1);if(capacity<dw*dh)return 0;
 uint32_t*result=malloc(dw*dh*4);if(!result)return 0;
 for(unsigned y=0;y<dh;y++)for(unsigned x=0;x<dw;x++){
  int xx=(int)x-(int)dw/2,yy=(int)y-(int)dh/2,u=matrix[0]*xx+matrix[1]*yy,z=matrix[2]*xx+matrix[3]*yy;
  int sx=(u>=0?u/256:-((-u+255)/256))+(int)w/2,sy=(z>=0?z/256:-((-z+255)/256))+(int)h/2;
  result[y*dw+x]=(sx>=0&&sy>=0&&sx<(int)w&&sy<(int)h)?source[sy*w+sx]:0;
 }memcpy(out,result,dw*dh*4);dimensions[0]=dw;dimensions[1]=dh;free(result);return 1;
}

static uint32_t obj_effect(uint32_t,unsigned,unsigned);
static uint16_t obj_half(const uint8_t*p){return p[0]|((uint16_t)p[1]<<8);}
static uint32_t obj_color(unsigned c){unsigned r=c&31,g=(c>>5)&31,b=(c>>10)&31;return 0xff000000u|((r<<3)|(r>>2))|(((g<<3)|(g>>2))<<8)|(((b<<3)|(b>>2))<<16);}
static int obj_scanline_impl(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,const uint8_t*o,size_t on,uint16_t display,unsigned row,unsigned blend,unsigned brightness,uint32_t out[240],uint32_t meta[240]){
 static const unsigned sizes[3][4][2]={{{8,8},{16,16},{32,32},{64,64}},{{16,8},{32,8},{32,16},{64,32}},{{8,16},{8,32},{16,32},{32,64}}};
 if(!v||!p||!o||!out||!meta||vn<0x18000||pn<1024||on<1024||row>=160||(display&0xe000))return 0;
 uint32_t colors[240]={0},tags[240];for(unsigned x=0;x<240;x++)tags[x]=UINT32_MAX;
 if(display&0x1000)for(unsigned i=0;i<128;i++){
  unsigned a=obj_half(o+i*8),b=obj_half(o+i*8+2),c=obj_half(o+i*8+4),tile=c&1023;
  if((!(a&256)&&(a&512))||(a>>14)==3||((display&7)>=3&&tile<512))continue;
  unsigned mode=a>>10&3;if(mode>=2||(a&4096))return 0;
  unsigned w=sizes[a>>14][b>>14][0],h=sizes[a>>14][b>>14][1],dw=w,dh=h;if((a&256)&&(a&512)){dw*=2;dh*=2;}
  int x0=b&511,y0=a&255;if(x0>=256)x0-=512;if(y0>=160)y0-=256;int yy=(int)row-y0;if(yy<0||yy>=(int)dh)continue;
  int16_t matrix[4]={0};if(a&256)for(unsigned j=0;j<4;j++)matrix[j]=(int16_t)obj_half(o+((b>>9)&31)*32+6+j*8);
  unsigned color8=a>>13&1,one=!!(display&64),base=(tile&~(unsigned)(color8&&!one))*32,mask=one?0x7fff:0x3ff,hi=one?0:base&0x7c00,stride=one?w>>(1-color8):128,priority=c>>10&3;
  for(unsigned x=0;x<dw;x++){
   int screen=x0+(int)x;if(screen<0||screen>=240||(tags[screen]!=UINT32_MAX&&(tags[screen]&3)<=priority))continue;
   int sx=x,sy=yy;if(a&256){int xx=(int)x-(int)dw/2,dy=yy-(int)dh/2,u=matrix[0]*xx+matrix[1]*dy,z=matrix[2]*xx+matrix[3]*dy;sx=(u>=0?u/256:-((-u+255)/256))+(int)w/2;sy=(z>=0?z/256:-((-z+255)/256))+(int)h/2;}else{if(b&0x1000)sx=w-1-x;if(b&0x2000)sy=h-1-yy;}
   uint32_t color=0;if(sx>=0&&sy>=0&&sx<(int)w&&sy<(int)h){unsigned lx=sx,ly=sy,ybase=(ly&~7u)*stride+(ly&7u)*(color8?8:4)+hi,xbase=(lx&~7u)*(color8?8:4)+(lx&7u)/(color8?1:2),address=0x10000+((ybase+((xbase+base)&mask))&0x7fff),index=color8?v[address]:(v[address]>>(4*(lx&1)))&15;if(index)color=obj_color(obj_half(p+512+2*(index+(color8?0:(c>>12)*16))));}
   unsigned effect=blend>>6&3,ey=brightness&31,variant=effect>=2&&(blend&16)&&!(mode==1&&(blend&0x2400));if(ey>16)ey=16;
   if(color){colors[screen]=variant?obj_effect(color,effect,ey):color;tags[screen]=priority|(mode<<2)|(i<<8)|(variant?0x10000:0);}else if(colors[screen])tags[screen]=(tags[screen]&0x10000)|priority|(mode<<2)|(i<<8);
  }
 }
 memcpy(out,colors,sizeof(colors));memcpy(meta,tags,sizeof(tags));return 1;
}
int nf_obj_scanline(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,const uint8_t*o,size_t on,uint16_t display,unsigned row,uint32_t out[240],uint32_t meta[240]){return obj_scanline_impl(v,vn,p,pn,o,on,display,row,0,0,out,meta);}
int nf_obj_scanline_prepared(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,const uint8_t*o,size_t on,uint16_t display,unsigned row,unsigned blend,unsigned brightness,uint32_t out[240],uint32_t meta[240]){return obj_scanline_impl(v,vn,p,pn,o,on,display,row,blend,brightness,out,meta);}
/* Unblended OBJ candidate plane. Metadata preserves priority and mode for later
   BG/window/blend composition; unsupported window/mosaic inputs reject. */
static int obj_layer_impl(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,const uint8_t*o,size_t on,uint16_t display,unsigned blend,unsigned brightness,uint32_t*out,uint32_t*meta){
 if(!v||!p||!o||!out||!meta||vn<0x18000||pn<1024||on<1024||(display&0xe000))return 0;
 uint32_t*colors=calloc(240*160,4),*tags=malloc(240*160*4),*image=malloc(16384*4);if(!colors||!tags||!image){free(colors);free(tags);free(image);return 0;}
 for(unsigned i=0;i<240*160;i++)tags[i]=UINT32_MAX;
 if(display&0x1000)for(unsigned i=0;i<128;i++){
  uint16_t a=obj_half(o+i*8),b=obj_half(o+i*8+2),c=obj_half(o+i*8+4);if(!(a&256)&&(a&512))continue;
  if((a>>14)==3||((display&7)>=3&&(c&1023)<512))continue;
  unsigned dims[2];int ok;
  if(a&256){int16_t matrix[4];unsigned m=(b>>9)&31;for(unsigned j=0;j<4;j++)matrix[j]=(int16_t)obj_half(o+m*32+6+j*8);ok=nf_obj_affine_image(v,vn,p,pn,a,b,c,display,matrix,image,16384,dims);}
  else ok=nf_obj_image(v,vn,p,pn,a,b,c,display,image,16384,dims);
  if(!ok||(a&4096)){free(colors);free(tags);free(image);return 0;}
  int x0=b&511;if(x0>=256)x0-=512;int y0=a&255;if(y0>=160)y0-=256;
  unsigned priority=(c>>10)&3,mode=(a>>10)&3,effect=(blend>>6)&3,ey=brightness&31;if(ey>16)ey=16;
  unsigned variant=effect>=2&&(blend&16)&&!(mode==1&&(blend&0x2400));
  if(variant)for(unsigned j=0;j<dims[0]*dims[1];j++)if(image[j])image[j]=obj_effect(image[j],effect,ey);
  for(unsigned y=0;y<dims[1];y++)for(unsigned x=0;x<dims[0];x++){
   int xx=x0+(int)x,yy=y0+(int)y;if(xx<0||xx>=240||yy<0||yy>=160)continue;unsigned pos=yy*240+xx;
   if(tags[pos]!=UINT32_MAX&&(tags[pos]&3)<=priority)continue;
   if(image[y*dims[0]+x]){colors[pos]=image[y*dims[0]+x];tags[pos]=priority|(mode<<2)|(i<<8)|(variant?0x10000:0);}
   else if(colors[pos])tags[pos]=(tags[pos]&0x10000)|priority|(mode<<2)|(i<<8);
  }
 }
 memcpy(out,colors,240*160*4);memcpy(meta,tags,240*160*4);free(colors);free(tags);free(image);return 1;
}
__declspec(dllexport) int nf_obj_layer(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,const uint8_t*o,size_t on,uint16_t display,uint32_t*out,uint32_t*meta){return obj_layer_impl(v,vn,p,pn,o,on,display,0,0,out,meta);}
int nf_obj_layer_prepared(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,const uint8_t*o,size_t on,uint16_t display,unsigned blend,unsigned brightness,uint32_t*out,uint32_t*meta){return obj_layer_impl(v,vn,p,pn,o,on,display,blend,brightness,out,meta);}
static uint32_t obj_effect(uint32_t color,unsigned effect,unsigned amount){uint32_t result=0xff000000;for(unsigned k=0;k<3;k++){unsigned mask=255u<<(k*8),c=color&mask;if(effect==2)c+=((mask-c)*amount)/16;else if(effect==3)c-=(c*amount)/16;result|=c&mask;}return result;}
__declspec(dllexport) uint32_t nf_obj_bg_backdrop_pixel(uint32_t obj,uint32_t tag,uint32_t bg,unsigned priority,uint32_t backdrop,unsigned blend,unsigned alpha,unsigned brightness){
 uint32_t colors[3];unsigned bits[3],count=0,mode=(tag>>2)&3,effect=(blend>>6)&3,ey=brightness&31;if(ey>16)ey=16;
 if(obj&&(!bg||(tag&3)<=priority)){colors[count]=obj;bits[count++]=4;}
 if(bg){colors[count]=bg;bits[count++]=2;}
 if(obj&&bg&&(tag&3)>priority){colors[count]=obj;bits[count++]=4;}
 colors[count]=backdrop;bits[count++]=5;
 if(effect>=2)for(unsigned i=0;i<count;i++)if((blend&(1u<<bits[i]))&&!(bits[i]==4&&(mode==1||(tag&0x30000))))colors[i]=obj_effect(colors[i],effect,ey);
 unsigned semi=bits[0]==4&&mode==1,mix=count>1&&(blend&(1u<<(bits[1]+8)))&&(semi||(effect==1&&(blend&(1u<<bits[0]))));
 if(semi&&!mix&&effect>=2&&(blend&((tag&0x20000)?0x2400:0x2410)))colors[0]=obj_effect(colors[0],effect,ey);
 unsigned ea=alpha&31,eb=(alpha>>8)&31;if(ea>16)ea=16;if(eb>16)eb=16;
 uint32_t result=0xff000000;for(unsigned k=0;k<3;k++){unsigned mask=255u<<(k*8),c=colors[0]&mask;if(mix){c=(c*ea+(colors[1]&mask)*eb)/16;if((c>>(k*8))>255)c=mask;}result|=c&mask;}return result;
}
/* Two visible candidates OBJ and BG2; backdrop/window selection is caller-owned. */
__declspec(dllexport) int nf_obj_mode4_affine_layer(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,const uint8_t*o,size_t on,uint16_t display,uint16_t bgcnt,uint16_t blend,uint16_t alpha,uint16_t brightness,const int32_t matrix[6],uint32_t*out){
 if(!matrix||!out||!v||!p||!o||vn<0x18000||pn<1024||on<1024||(display&7)!=4||(display&0xe080)||(bgcnt&64))return 0;
 for(unsigned j=0;j<4;j++)if(matrix[j]<-32768||matrix[j]>32767)return 0;
 if(matrix[4]<-134217728||matrix[4]>134217727||matrix[5]<-134217728||matrix[5]>134217727)return 0;
 uint32_t*colors=malloc(240*160*4),*tags=malloc(240*160*4),*result=malloc(240*160*4);if(!colors||!tags||!result){free(colors);free(tags);free(result);return 0;}
 if(!obj_layer_impl(v,vn,p,pn,o,on,display,blend,brightness,colors,tags)){free(colors);free(tags);free(result);return 0;}
 uint32_t bd=obj_color(obj_half(p));unsigned page=(display&16)?0xa000:0;
 for(unsigned i=0;i<240*160;i++){int64_t x=(int64_t)matrix[4]+(int64_t)matrix[0]*(i%240)+(int64_t)matrix[1]*(i/240),y=(int64_t)matrix[5]+(int64_t)matrix[2]*(i%240)+(int64_t)matrix[3]*(i/240);unsigned index=(display&0x400)&&x>=0&&y>=0&&x<240*256&&y<160*256?v[page+(unsigned)(y/256)*240+(unsigned)(x/256)]:0;uint32_t bg=index?obj_color(obj_half(p+index*2)):0;result[i]=nf_obj_bg_backdrop_pixel(colors[i],tags[i]|0x20000,bg,bgcnt&3,bd,blend,alpha,brightness);}
 memcpy(out,result,240*160*4);free(colors);free(tags);free(result);return 1;
}
__declspec(dllexport) uint32_t nf_obj_bg_pixel(uint32_t obj,uint32_t tag,uint32_t bg,unsigned bg_priority,unsigned blend,unsigned alpha,unsigned brightness){
 unsigned has=obj!=0,front=has&&(tag&3)<=bg_priority,mode=(tag>>2)&3,effect=(blend>>6)&3;uint32_t top=front?obj:bg,under=front?bg:obj;unsigned topbit=front?4:2,underbit=front?2:4;
 unsigned first=(blend>>topbit)&1,second=(blend>>(underbit+8))&1;
 unsigned semi=front&&mode==1;
 unsigned mix=has&&second&&(semi||(effect==1&&first));unsigned ea=alpha&31,eb=(alpha>>8)&31,ey=brightness&31;if(ea>16)ea=16;if(eb>16)eb=16;if(ey>16)ey=16;
 if(effect>=2){if(blend&4)bg=obj_effect(bg,effect,ey);if((blend&16)&&mode!=1)obj=obj_effect(obj,effect,ey);top=front?obj:bg;under=front?bg:obj;}
 uint32_t result=0xff000000;for(unsigned k=0;k<3;k++){
  unsigned mask=255u<<(k*8),c=top&mask,d=under&mask;
  if(mix){c=(c*ea+d*eb)/16;if((c>>(k*8))>255)c=mask;}
  result|=c&mask;
 }return result;
}





__declspec(dllexport) int nf_obj_mode4_layer(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,const uint8_t*o,size_t on,uint16_t display,uint16_t bgcnt,uint16_t blend,uint16_t alpha,uint16_t brightness,uint32_t*out){const int32_t m[6]={256,0,0,256,0,0};return nf_obj_mode4_affine_layer(v,vn,p,pn,o,on,display,bgcnt,blend,alpha,brightness,m,out);}


static int obj_window_axis(unsigned value,unsigned pos,unsigned limit){unsigned start=value>>8,end=value&255;if(start>limit&&start>end)start=0;if(end>limit){end=limit;if(start>limit)start=limit;}return start<=end?(pos>=start&&pos<end):(pos>=start||pos<end);}
__declspec(dllexport) int nf_rect_window_layer(unsigned display,const uint16_t regs[6],uint8_t*out){
 if(!regs||!out||(display&0x8000))return 0;
 uint8_t result[240*160];for(unsigned y=0;y<160;y++)for(unsigned x=0;x<240;x++){
 unsigned control=63;if(display&0x6000){control=regs[5]&63;for(int w=1;w>=0;w--)if((display&(0x2000u<<w))&&obj_window_axis(regs[w],x,240)&&obj_window_axis(regs[w+2],y,160))control=(regs[4]>>(w*8))&63;}result[y*240+x]=(uint8_t)control;}
 memcpy(out,result,sizeof(result));return 1;
}

typedef struct {unsigned end,control;} NFObjWindowSpan;
/* Preserve zero-length spans: original backdrop initialization aligns its
   write cursor even when that span has no visible window pixels. Two windows
   split into at most four intervals, so sixteen span slots are sufficient. */
static void obj_window_bounds(unsigned value,unsigned limit,unsigned*start,unsigned*end){*start=value>>8;*end=value&255;if(*start>limit&&*start>*end)*start=0;if(*end>limit){*end=limit;if(*start>limit)*start=limit;}}
static void obj_window_insert(NFObjWindowSpan spans[16],unsigned*n,unsigned start,unsigned end,unsigned control){
 if(!end)return;
 NFObjWindowSpan result[16];unsigned count=0,left=0,i=0;
 for(;i<*n;i++){unsigned right=spans[i].end;if(start<right){if(start>left)result[count++]=(NFObjWindowSpan){start,spans[i].control};result[count++]=(NFObjWindowSpan){end,control};if(end<right)result[count++]=spans[i++];else {i++;while(i<*n&&end>=spans[i].end)i++;}break;}result[count++]=spans[i];left=right;}
 for(;i<*n;i++){result[count++]=spans[i];}memcpy(spans,result,count*sizeof(*spans));*n=count;
}
static void obj_backdrop_control_row(unsigned display,const uint16_t regs[6],unsigned y,uint8_t*out){
 NFObjWindowSpan spans[16]={{240,(display&0x6000)?regs[5]&63:63}};unsigned n=1;
 for(int w=1;w>=0;w--)if((display&(0x2000u<<w))&&obj_window_axis(regs[w+2],y,160)){unsigned start,end;obj_window_bounds(regs[w],240,&start,&end);unsigned c=(regs[4]>>(w*8))&63;if(start>end){obj_window_insert(spans,&n,0,end,c);obj_window_insert(spans,&n,start,240,c);}else obj_window_insert(spans,&n,start,end,c);}
 unsigned x=0;for(unsigned w=0;w<n;w++){unsigned stop=spans[w].end,aligned=(x+3)&~3u;if(aligned>stop)stop=aligned;if(stop>240)stop=240;for(;x<stop;x++)out[x]=(uint8_t)spans[w].control;}
}
static void obj_backdrop_controls(unsigned display,const uint16_t regs[6],uint8_t*out){for(unsigned y=0;y<160;y++)obj_backdrop_control_row(display,regs,y,out+y*240);}
int nf_obj_window_scanline_prepared(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,const uint8_t*o,size_t on,uint16_t display,unsigned row,const uint16_t window[6],unsigned blend,unsigned brightness,uint32_t out[240],uint32_t meta[240],uint8_t controls[240],uint8_t backdrop_controls[240]){
 if(!v||!p||!o||!window||!out||!meta||!controls||!backdrop_controls||vn<0x18000||pn<1024||on<1024||row>=160||(display&0x8080))return 0;
 uint8_t visible[240],backdrop[240];uint32_t colors[2][240],tags[2][240],result[240],metadata[240];unsigned needed=0;
 memset(visible,(display&0x6000)?window[5]&63:63,sizeof(visible));
 for(int w=1;w>=0;w--)if((display&(0x2000u<<w))&&obj_window_axis(window[w+2],row,160)){
  unsigned start,end;obj_window_bounds(window[w],240,&start,&end);unsigned control=(window[4]>>(w*8))&63;
  if(start<=end)memset(visible+start,control,end-start);
  else{memset(visible,control,end);memset(visible+start,control,240-start);}
 }
 if(display&0x1000)for(unsigned x=0;x<240;x++)if(visible[x]&16)needed|=1u<<!!(visible[x]&32);
 for(unsigned i=0;i<2;i++)if(needed&(1u<<i))if(!obj_scanline_impl(v,vn,p,pn,o,on,display&~0xe000u,row,i?blend:blend&0x3f00,brightness,colors[i],tags[i]))return 0;
 for(unsigned x=0;x<240;x++){if((display&0x1000)&&(visible[x]&16)){unsigned i=!!(visible[x]&32);result[x]=colors[i][x];metadata[x]=tags[i][x];}else{result[x]=0;metadata[x]=UINT32_MAX;}}
 obj_backdrop_control_row(display,window,row,backdrop);memcpy(out,result,sizeof(result));memcpy(meta,metadata,sizeof(metadata));memcpy(controls,visible,sizeof(visible));memcpy(backdrop_controls,backdrop,sizeof(backdrop));return 1;
}
__declspec(dllexport) int nf_obj_mode4_window_scanline(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,const uint8_t*o,size_t on,uint16_t display,uint16_t bgcnt,uint16_t blend,uint16_t alpha,uint16_t brightness,const int32_t matrix[6],const uint16_t window[6],unsigned row,uint32_t out[240]){
 if(!v||!p||!o||!matrix||!window||!out||vn<0x18000||pn<1024||on<1024||row>=160||(display&7)!=4||(display&0x8080)||(bgcnt&64))return 0;
 for(unsigned j=0;j<4;j++)if(matrix[j]<-32768||matrix[j]>32767)return 0;
 if(matrix[4]<-134217728||matrix[4]>134217727||matrix[5]<-134217728||matrix[5]>134217727)return 0;
 uint32_t colors[240],tags[240],result[240];uint8_t controls[240],backdrop[240];
 if(!nf_obj_window_scanline_prepared(v,vn,p,pn,o,on,display,row,window,blend,brightness,colors,tags,controls,backdrop))return 0;
 unsigned page=(display&16)?0xa000:0,ey=brightness&31;if(ey>16)ey=16;uint32_t bd=obj_color(obj_half(p));
 for(unsigned i=0;i<240;i++){
  int64_t x=(int64_t)matrix[4]+(int64_t)matrix[0]*i,y=(int64_t)matrix[5]+(int64_t)matrix[2]*i;
  unsigned index=(controls[i]&4)&&(display&0x400)&&x>=0&&y>=0&&x<240*256&&y<160*256?v[page+(unsigned)(y/256)*240+(unsigned)(x/256)]:0;
  uint32_t bg=index?obj_color(obj_half(p+index*2)):0;unsigned b=(controls[i]&32)?blend:blend&0x3f00;
  result[i]=nf_obj_bg_backdrop_pixel(colors[i],tags[i]|0x20000,bg,bgcnt&3,bd,b,alpha,brightness);
  if(!bg&&!colors[i]&&((controls[i]^backdrop[i])&32)&&((blend>>6)&3)>=2&&(blend&32))result[i]=(backdrop[i]&32)?obj_effect(bd,(blend>>6)&3,ey):bd;
 }
 memcpy(out,result,sizeof(result));return 1;
}
__declspec(dllexport) int nf_obj_mode4_window_layer(const uint8_t*v,size_t vn,const uint8_t*p,size_t pn,const uint8_t*o,size_t on,uint16_t display,uint16_t bgcnt,uint16_t blend,uint16_t alpha,uint16_t brightness,const int32_t matrix[6],const uint16_t window[6],uint32_t*out){
 if(!out||!window||(display&0x8000))return 0;
 uint8_t*controls=malloc(38400);uint32_t*result=malloc(38400*4),*image=malloc(38400*4);if(!controls||!result||!image){free(controls);free(result);free(image);return 0;}
 int ok=nf_rect_window_layer(display,window,controls);unsigned seen=0;
 for(unsigned i=0;ok&&i<38400;i++){unsigned key=((controls[i]>>2)&1)|(((controls[i]>>4)&3)<<1);if(seen&(1u<<key))continue;seen|=1u<<key;
 uint16_t d=display&~0xe000u;if(!(key&1))d&=~0x400u;if(!(key&2))d&=~0x1000u;unsigned b=(key&4)?blend:(blend&0x3f00);
 ok=nf_obj_mode4_affine_layer(v,vn,p,pn,o,on,d,bgcnt,(uint16_t)b,alpha,brightness,matrix,image);
 if(ok)for(unsigned j=0;j<38400;j++)if((((controls[j]>>2)&1)|(((controls[j]>>4)&3)<<1))==key)result[j]=image[j];
 }
 /* Only untouched backdrop pixels retain the span-alignment artifact;
    foreground composition and postprocess blending use visible controls. */
 if(ok&&((blend>>6)&3)>=2&&(blend&32)){
 uint32_t*obj=malloc(38400*4),*tags=malloc(38400*4);uint8_t*bdcontrols=malloc(38400);if(!obj||!tags||!bdcontrols)ok=0;
 if(ok)ok=nf_obj_layer(v,vn,p,pn,o,on,display&~0xe000u,obj,tags);
 if(ok){obj_backdrop_controls(display,window,bdcontrols);unsigned page=(display&16)?0xa000:0,ey=brightness&31;if(ey>16)ey=16;uint32_t bd=obj_color(obj_half(p));
 for(unsigned i=0;i<38400;i++)if((controls[i]^bdcontrols[i])&32){int64_t x=(int64_t)matrix[4]+(int64_t)matrix[0]*(i%240)+(int64_t)matrix[1]*(i/240),y=(int64_t)matrix[5]+(int64_t)matrix[2]*(i%240)+(int64_t)matrix[3]*(i/240);unsigned bg=(controls[i]&4)&&(display&0x400)&&x>=0&&y>=0&&x<240*256&&y<160*256?v[page+(unsigned)(y/256)*240+(unsigned)(x/256)]:0;if(!bg&&(!(controls[i]&16)||!obj[i]))result[i]=(bdcontrols[i]&32)?obj_effect(bd,(blend>>6)&3,ey):bd;}
 }free(obj);free(tags);free(bdcontrols);
 }
 if(ok){memcpy(out,result,38400*4);}free(controls);free(result);free(image);return ok;
}


