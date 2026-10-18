/* Diagnostic oracle ONLY: independent native retained index images sampled
   with the established integer pixel-center rule. Production route above fetches
   raw command texture bytes, not these index images. */
static int retained_integer_reference(NFPCSceneGPU*g,const NFPCScene*s,unsigned aw,unsigned ah){
 if(!g->retention_integer_reference){
  const char*v="#version 120\nvoid main(){gl_Position=vec4(gl_Vertex.x/120.0-1.0,1.0-gl_Vertex.y/80.0,0.0,1.0);}";
  const char*f="#version 120\nuniform sampler2D image;uniform sampler2D rows;uniform vec2 viewport;void main(){int px=int(gl_FragCoord.x),py=int(gl_FragCoord.y),w=int(viewport.x),h=int(viewport.y);int x=((px*2+1)*120)/w,y=(((h-py)*2-1)*80)/h;vec4 c=texture2D(image,(vec2(float(x),float(y))+vec2(0.5))/vec2(240.0,160.0));if(c.a<0.5)discard;float index=floor(c.r*255.0+0.5);gl_FragColor=vec4(texture2D(rows,vec2((index+0.5)/256.0,(float(y)+0.5)/160.0)).rgb,1.0);}";
  GLuint a=shader(g,VERTEX_SHADER,v),b=shader(g,FRAGMENT_SHADER,f);if(!a||!b){if(a)g->delete_shader(a);if(b)g->delete_shader(b);return 0;}GLuint program=g->create_program();g->attach_shader(program,a);g->attach_shader(program,b);g->link_program(program);g->delete_shader(a);g->delete_shader(b);GLint ok=0;g->get_program(program,LINK_STATUS,&ok);if(!ok){g->delete_program(program);return 0;}g->retention_integer_reference=program;
 }
 g->use_program(g->retention_integer_reference);g->uniform1i(g->uniform(g->retention_integer_reference,"image"),0);g->uniform1i(g->uniform(g->retention_integer_reference,"rows"),1);g->uniform2f(g->uniform(g->retention_integer_reference,"viewport"),(float)aw,(float)ah);glDisable(GL_SCISSOR_TEST);
 for(unsigned layer=0;layer<2;layer++)for(unsigned owner=0;owner<s->info[2];owner++){const void*p;size_t n;if(!nf_pc_scene_retention_buffer(s,owner,NFPC_ROAD+layer,0,&p,&n)||n!=153600)return 0;g->active(TEXTURE0);glBindTexture(GL_TEXTURE_2D,g->input);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,240,160,0,GL_RGBA,GL_UNSIGNED_BYTE,p);glBegin(GL_QUADS);glVertex2f(0,0);glVertex2f(240,0);glVertex2f(240,160);glVertex2f(0,160);glEnd();}
 return glGetError()==GL_NO_ERROR;
}
NFPC_API int nf_pc_scene_gpu_draw_integer_retention_reference(NFPCSceneGPU*g,NFPCScene*s,unsigned w,unsigned h,unsigned aw,unsigned ah,void*out,size_t bytes){
 if(!g||g->owner!=GetCurrentThreadId()||g->use_scene_writer_draws)return 0;
 g->use_scene_writer_draws=2;int ok=render(g,s,w,h,aw,ah,15,out,bytes,1);g->use_scene_writer_draws=0;return ok;
}
