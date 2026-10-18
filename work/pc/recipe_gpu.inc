/* Isolated recipe submission: caller supplies coverage/order; no core access. */
#include "recipe_gpu.h"
int nf_pc_scene_gpu_render_recipe(NFPCSceneGPU*g,const NFPCRecipeMesh*m,const NFPCRecipeMaterial*material,const void*palette,size_t pn,unsigned aw,unsigned ah,const unsigned clip[4]){
 uint64_t mi[3],mti[5];const void*raw,*image;size_t vn,in;float planes[62][11];
 if(!g||g->owner!=GetCurrentThreadId()||!g->target||!palette||pn!=163840||!clip||!aw||!ah||aw>g->width||ah>g->height||clip[0]>clip[1]||clip[1]>240||clip[2]>clip[3]||clip[3]>160||!nf_pc_recipe_mesh_info(m,mi)||mi[1]>186||mi[1]%3||!nf_pc_recipe_mesh_vertices(m,&raw,&vn)||vn!=mi[1]*20||!nf_pc_recipe_material_info(material,mti)||!nf_pc_recipe_material_buffer(material,2,&image,&in)||in!=mti[1]*mti[2]*4){error("Recipe input/target/thread");return 0;}
 for(unsigned i=0;i<mi[1]/3;i++)if(!nf_pc_recipe_mesh_plane(m,i,planes[i])){error("Recipe plane preparation");return 0;}
 int l=clip_edge(clip[0],aw,240),r=clip_edge(clip[1],aw,240),t=clip_edge(clip[2],ah,160),b=clip_edge(clip[3],ah,160);
 if(l>=r||t>=b||!mi[1])return 1;
 HDC dc=wglGetCurrentDC();HGLRC old=wglGetCurrentContext();if(!wglMakeCurrent(g->dc,g->context)){error("Recipe make current");return 0;}
 g->bind(FRAMEBUFFER,g->fbo);glViewport(0,0,aw,ah);glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);glDisable(GL_CULL_FACE);glDisable(GL_DITHER);glDisable(GL_ALPHA_TEST);glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE);glPixelStorei(GL_UNPACK_ALIGNMENT,1);
 g->use_program(g->program);g->active(TEXTURE0+1);sky_texture(g->palette,GL_RGBA,256,160,palette);g->active(TEXTURE0);sky_texture(g->input,GL_RGBA,(unsigned)mti[1],(unsigned)mti[2],image);
 g->uniform1i(g->uniform(g->program,"image"),0);g->uniform1i(g->uniform(g->program,"rows"),1);g->uniform1i(g->uniform(g->program,"indexed"),1);g->uniform1i(g->uniform(g->program,"wall"),mti[0]==2);g->uniform2f(g->uniform(g->program,"viewport"),(float)aw,(float)ah);
 glEnable(GL_SCISSOR_TEST);glScissor(l,(int)ah-b,r-l,b-t);const float*v=raw;
 for(unsigned i=0;i<mi[1]/3;i++){const float*p=planes[i];g->uniform2f(g->uniform(g->program,"origin"),p[0],p[1]);g->uniform3fv(g->uniform(g->program,"planeBase"),1,p+2);g->uniform3fv(g->uniform(g->program,"planeX"),1,p+5);g->uniform3fv(g->uniform(g->program,"planeY"),1,p+8);glBegin(GL_TRIANGLES);for(unsigned k=0;k<3;k++)glVertex2f(v[(i*3+k)*5],v[(i*3+k)*5+1]);glEnd();}
 glDisable(GL_SCISSOR_TEST);int ok=glGetError()==GL_NO_ERROR;if(!ok)error("Recipe draw");g->use_program(0);g->bind(FRAMEBUFFER,0);wglMakeCurrent(dc,old);return ok;
}
