/* Included after preview_resources.h. Keep internal geometry at 3840x2160;
   copy into an aspect-preserving window back buffer, or clear on unavailable
   scenes. Call finish even if a caller only reads back for a diagnostic. */
static int preview_window_stage_to(int scene_ready,GLuint destination,int width,int height){
 if(!preview_window_output||!preview_context)return 0;
 void(APIENTRY*bind)(GLenum,GLuint)=(void*)wglGetProcAddress("glBindFramebuffer");
 void(APIENTRY*blit)(GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLbitfield,GLenum)=(void*)wglGetProcAddress("glBlitFramebuffer");
 if(!bind||!blit)return 0;
 if(width<=0||height<=0)return 0;
 int w=width,h=width*9/16;if(h>height){h=height;w=height*16/9;}
 bind(0x8ca8,preview_fbo);bind(0x8ca9,destination);glDrawBuffer(destination?0x8ce0:GL_BACK);glDisable(GL_SCISSOR_TEST);glClearColor(0,0,0,1);glClear(GL_COLOR_BUFFER_BIT);
 if(scene_ready)blit(0,0,3840,2160,(width-w)/2,(height-h)/2,(width+w)/2,(height+h)/2,GL_COLOR_BUFFER_BIT,GL_NEAREST);
 return glGetError()==GL_NO_ERROR;
}
static int preview_window_stage(int scene_ready){
 RECT client;if(!GetClientRect(preview_window,&client))return 0;
 return preview_window_stage_to(scene_ready,0,client.right,client.bottom);
}
static int preview_window_finish(void){
 int ok=SwapBuffers(preview_dc)!=0;
 void(APIENTRY*bind)(GLenum,GLuint)=(void*)wglGetProcAddress("glBindFramebuffer");
 if(bind)bind(0x8d40,preview_fbo);else ok=0;
 return ok;
}
