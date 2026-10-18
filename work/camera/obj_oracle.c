#include <mgba/internal/gba/renderers/video-software.h>
#include <stdlib.h>
#include <string.h>
static int obj_oracle_impl(const void*vram,const void*palette,const void*oam,unsigned display,unsigned bg,unsigned blend,unsigned alpha,unsigned brightness,const int32_t*matrix,const uint16_t*window,uint8_t*controls,void*out){
 if(!vram||!palette||!oam||!out)return 0;
 struct GBAVideoSoftwareRenderer*r=calloc(1,sizeof(*r));uint16_t*v=malloc(0x18000),*p=malloc(1024);union GBAOAM*o=malloc(1024);color_t*image=malloc(240*160*sizeof(color_t));
 if(!r||!v||!p||!o||!image){free(r);free(v);free(p);free(o);free(image);return 0;}
 memcpy(v,vram,0x18000);memcpy(p,palette,1024);memcpy(o,oam,1024);GBAVideoSoftwareRendererCreate(r);r->d.vram=v;r->d.palette=p;r->d.oam=o;r->outputBuffer=image;r->outputBufferStride=240;r->d.init(&r->d);
 for(unsigned i=0;i<512;i++)r->d.writePalette(&r->d,i*2,p[i]);for(unsigned i=0;i<512;i++)r->d.writeOAM(&r->d,i);r->d.writeVideoRegister(&r->d,0,display);r->d.writeVideoRegister(&r->d,0x0c,bg);r->d.writeVideoRegister(&r->d,0x20,256);r->d.writeVideoRegister(&r->d,0x26,256);r->d.writeVideoRegister(&r->d,0x50,blend);r->d.writeVideoRegister(&r->d,0x52,alpha);r->d.writeVideoRegister(&r->d,0x54,brightness);
 if(matrix){r->d.writeVideoRegister(&r->d,0x20,matrix[0]);r->d.writeVideoRegister(&r->d,0x22,matrix[1]);r->d.writeVideoRegister(&r->d,0x24,matrix[2]);r->d.writeVideoRegister(&r->d,0x26,matrix[3]);r->d.writeVideoRegister(&r->d,0x28,matrix[4]);r->d.writeVideoRegister(&r->d,0x2a,(uint32_t)matrix[4]>>16);r->d.writeVideoRegister(&r->d,0x2c,matrix[5]);r->d.writeVideoRegister(&r->d,0x2e,(uint32_t)matrix[5]>>16);}
 if(window)for(unsigned i=0;i<6;i++)r->d.writeVideoRegister(&r->d,0x40+i*2,window[i]);
 for(int y=0;y<160;y++){r->d.drawScanline(&r->d,y);if(controls){int x=0;for(int w=0;w<r->nWindows;w++)for(;x<r->windows[w].endX;x++)controls[y*240+x]=r->windows[w].control.packed&63;}}memcpy(out,image,240*160*sizeof(color_t));r->d.deinit(&r->d);free(image);free(o);free(p);free(v);free(r);return 1;
}

__declspec(dllexport) int nf_obj_oracle(const void*v,const void*p,const void*o,unsigned display,void*out){return obj_oracle_impl(v,p,o,display,0,0,0,0,NULL,NULL,NULL,out);}
__declspec(dllexport) int nf_obj_bg_oracle(const void*v,const void*p,const void*o,unsigned display,unsigned bg,unsigned blend,unsigned alpha,unsigned brightness,void*out){return obj_oracle_impl(v,p,o,display,bg,blend,alpha,brightness,NULL,NULL,NULL,out);}

__declspec(dllexport) int nf_obj_affine_oracle(const void*v,const void*p,const void*o,unsigned display,unsigned bg,unsigned blend,unsigned alpha,unsigned brightness,const int32_t*matrix,void*out){return obj_oracle_impl(v,p,o,display,bg,blend,alpha,brightness,matrix,NULL,NULL,out);}

__declspec(dllexport) int nf_window_oracle(const void*v,const void*p,const void*o,unsigned display,const uint16_t*window,uint8_t*controls,void*out){return obj_oracle_impl(v,p,o,display,0,0,0,0,NULL,window,controls,out);}

__declspec(dllexport) int nf_window_composite_oracle(const void*v,const void*p,const void*o,unsigned display,unsigned bg,unsigned blend,unsigned alpha,unsigned brightness,const int32_t*matrix,const uint16_t*window,void*out){return obj_oracle_impl(v,p,o,display,bg,blend,alpha,brightness,matrix,window,NULL,out);}
