#ifndef NF_SOURCE_COMMAND_DEPTH_H
#define NF_SOURCE_COMMAND_DEPTH_H
/* Scene commands follow original painter order. Depth is local to one model,
   so an earlier road/model cannot reject a later original framebuffer write. */
static void preview_source_depth_command(unsigned command){
 const char*legacy=getenv("NF_PREVIEW_GLOBAL_DEPTH");if(legacy&&legacy[0]=='1'&&!legacy[1])return;
 if(command>=UINT32_MAX-15){glDepthMask(GL_TRUE);glClearDepth(0);glClear(GL_DEPTH_BUFFER_BIT);glEnable(GL_DEPTH_TEST);glDepthFunc(GL_GEQUAL);}
 else {glDisable(GL_DEPTH_TEST);glDepthMask(GL_FALSE);}
}
static void preview_source_depth_end(void){glDisable(GL_DEPTH_TEST);glDepthMask(GL_TRUE);}
#endif
