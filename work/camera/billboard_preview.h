#ifndef NF_BILLBOARD_PREVIEW_H
#define NF_BILLBOARD_PREVIEW_H
/* Reusable captured-pose draw, caller supplies projection and ordering. */
static int draw_billboard(const void*record,size_t size){
 NFBillboardView view;double quad[16];
 int visible=nf_billboard_quad(record,size,3840,2160,quad);
 if(visible!=1)return visible;
 if(!nf_billboard_view(record,size,&view))return -1;
 glPushAttrib(GL_ENABLE_BIT|GL_TEXTURE_BIT|GL_COLOR_BUFFER_BIT|GL_CURRENT_BIT|GL_POLYGON_BIT);
 GLuint texture=preview_texture(view.width,view.height,view.rgba);if(!texture){glPopAttrib();return -1;}
 glEnable(GL_TEXTURE_2D);glBindTexture(GL_TEXTURE_2D,texture);glEnable(GL_ALPHA_TEST);glAlphaFunc(GL_GREATER,0);glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);glColor4ub(255,255,255,255);
 glDisable(GL_CULL_FACE);glDisable(GL_SCISSOR_TEST);glDisable(GL_STENCIL_TEST);glDisable(GL_FOG);glDisable(GL_LIGHTING);glDisable(GL_COLOR_LOGIC_OP);glDisable(GL_TEXTURE_GEN_S);glDisable(GL_TEXTURE_GEN_T);
 glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE);glPolygonMode(GL_FRONT_AND_BACK,GL_FILL);
 glTexEnvi(GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE,GL_REPLACE);
 glBegin(GL_QUADS);for(unsigned i=0;i<4;i++){glTexCoord2d(quad[i*4+2],quad[i*4+3]);glVertex2d(quad[i*4],quad[i*4+1]);}glEnd();glPopAttrib();return 1;
}
#endif
