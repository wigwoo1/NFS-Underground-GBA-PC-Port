#ifndef NF_INDEXED_COPY_GPU_H
#define NF_INDEXED_COPY_GPU_H
#include "indexed_copy.h"
/* Native2D source asset only. Destination row segmentation retains the tail
   and writes index0; no rendered GBA image is used. Caller owns GL context. */
static int indexed_copy_gpu_draw(const void*asset,size_t bytes){
 uint32_t kind,page,offset;const uint8_t*indices;size_t count;
 if(!preview_display_palette_valid||!preview_zero_valid||!nf_indexed_operation_view(asset,bytes,&kind,&page,&offset,&indices,&count))return 0;
 uint8_t*packed=calloc(240*160,1),*rgba=calloc(240*160,4);if(!packed||!rgba){free(packed);free(rgba);return 0;}
 memcpy(packed+offset,indices,count);GLuint skin=model_zero_texture(240,160,rgba,packed);free(rgba);
 if(!skin){free(packed);return 0;}
 glPushAttrib(GL_ENABLE_BIT|GL_TEXTURE_BIT|GL_CURRENT_BIT|GL_DEPTH_BUFFER_BIT|GL_COLOR_BUFFER_BIT|GL_VIEWPORT_BIT);
 glViewport(0,0,3840,2160);glDisable(GL_SCISSOR_TEST);glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);glDepthMask(GL_FALSE);glEnable(GL_TEXTURE_2D);
 glMatrixMode(GL_PROJECTION);glPushMatrix();glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);
 glMatrixMode(GL_MODELVIEW);glPushMatrix();glLoadIdentity();
 int ok=model_zero_begin(skin,packed);
 if(ok){glColor4f(1,1,1,1);glBegin(GL_QUADS);
  /* Pixel-center half-open coverage removes fractional13.5 boundary ties.
     Constant texel centers retain exact indexed2D source pixels. */
  for(size_t at=offset,end=offset+count;at<end;at++){unsigned x=at%240,y=at/240;
   double left=300+ceil(x*13.5-.5),right=300+ceil((x+1)*13.5-.5),top=ceil(y*13.5-.5),bottom=ceil((y+1)*13.5-.5);
   glTexCoord2d((x+.5)/240.,(y+.5)/160.);glVertex2d(left,top);glVertex2d(right,top);glVertex2d(right,bottom);glVertex2d(left,bottom);}
  glEnd();model_zero_end(packed);
 }
 glPopMatrix();glMatrixMode(GL_PROJECTION);glPopMatrix();glMatrixMode(GL_MODELVIEW);glPopAttrib();free(packed);return ok;
}
#endif
