#ifndef NF_ROAD_EDGE_GPU_H
#define NF_ROAD_EDGE_GPU_H
#include "road_polygon_clip.h"
/* Boundary UV quads sample owned source texture on GPU; no sampled RGB/index
   framebuffer is constructed. Continuous native interior remains intact. */
static int road_edge_gpu_draw(const NFRoadAssetView*v,unsigned right){
 if(!preview_display_palette_valid||!preview_road_reciprocal)return 0;
 unsigned w=1024,h=(v->header[8]+w-1)/w;size_t bytes=(size_t)w*h;uint8_t*indices=calloc(bytes,1),*rgba=calloc(bytes,4);if(!indices||!rgba){free(indices);free(rgba);return 0;}memcpy(indices,v->texture,v->header[8]);
 GLuint skin=model_zero_texture(w,h,rgba,indices);free(rgba);if(!skin){free(indices);return 0;}
 glPushAttrib(GL_ENABLE_BIT|GL_TEXTURE_BIT|GL_CURRENT_BIT|GL_DEPTH_BUFFER_BIT|GL_COLOR_BUFFER_BIT|GL_VIEWPORT_BIT);glViewport(0,0,3840,2160);glDisable(GL_SCISSOR_TEST);glDisable(GL_DEPTH_TEST);glDisable(GL_BLEND);glDepthMask(GL_FALSE);glEnable(GL_TEXTURE_2D);
 glMatrixMode(GL_PROJECTION);glPushMatrix();glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);glMatrixMode(GL_MODELVIEW);glPushMatrix();glLoadIdentity();int ok=model_zero_begin(skin,indices);
 if(ok){glColor4f(1,1,1,1);glBegin(GL_QUADS);
 for(unsigned i=0;i<v->header[5]&&ok;i++){uint32_t s[20],runs[512],final[16];unsigned n=0;memcpy(s,v->spans+i*80,80);
 if(s[2]==0x03003190)ok=nf_road_perspective_plan(s+4,preview_road_reciprocal,runs,32,&n,final);else{memcpy(runs,s+4,64);n=1;}unsigned at=0;
 for(unsigned r=0;r<n&&ok;r++){uint32_t*c=runs+r*16,u=c[8],vv=c[9];for(unsigned k=0;k<c[7];k++,at++){u&=c[1];vv&=c[2];size_t tex=2ull*((u>>16)+((uint64_t)(vv>>16)<<c[0]));
 for(unsigned duplicate=0;duplicate<=s[3];duplicate++)for(unsigned lane=0;lane<2;lane++){unsigned base=s[0]>=0x0600a000?0x0600a000:0x06000000,dest=s[0]-base+at*2+duplicate*240+lane,x=dest%240,y=dest/240;if(y>=160||x<right)continue;
 if(tex+lane>=v->header[8]){ok=0;continue;}double a=300+ceil(x*13.5-.5),b=300+ceil((x+1)*13.5-.5),t=ceil(y*13.5-.5),bottom=ceil((y+1)*13.5-.5);glTexCoord2d(((tex+lane)%w+.5)/w,((tex+lane)/w+.5)/h);glVertex2d(a,t);glVertex2d(b,t);glVertex2d(b,bottom);glVertex2d(a,bottom);
 }u+=c[10];vv+=c[11];}}
 }glEnd();model_zero_end(indices);}
 glPopMatrix();glMatrixMode(GL_PROJECTION);glPopMatrix();glMatrixMode(GL_MODELVIEW);glPopAttrib();free(indices);return ok;
}
#endif
