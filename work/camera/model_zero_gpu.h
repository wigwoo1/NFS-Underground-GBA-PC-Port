/* Mode4 index0 overwrites the framebuffer but has no BG2 display coverage. */
static const uint8_t*preview_model_indices[16];
static const uint8_t*preview_world_indices[128];
static unsigned preview_world_affine[128];
static const uint8_t*preview_wall_states[128];
static const uint8_t*preview_wall_indices[128];
static unsigned preview_wall_planes[128];
static unsigned world_zero_draws,wall_zero_draws;
static uint16_t preview_zero_colors[160];
static uint16_t preview_display_palette[160][256];
static int preview_display_palette_valid;
#include "display_palette_gpu.h"
static int preview_zero_valid;
static int preview_zero_background;
static unsigned model_zero_draws;
static GLboolean model_zero_alpha_test;
static GLuint model_zero_program;
static GLint model_zero_asset_location,model_zero_rows_location,model_zero_writer_location;
static GLint model_zero_indexed_location,model_zero_full_palette_location;
static HGLRC model_zero_context;
/* Same-generation cache: preview_texture cannot evict a texture used in this
   generation. Revalidate each new generation and every scanline color change. */
static GLuint model_zero_row_texture;
static uint64_t model_zero_row_generation;
static HGLRC model_zero_row_context;
static uint16_t model_zero_row_source[160];
static void(APIENTRY*model_zero_use)(GLuint);
static void(APIENTRY*model_zero_active)(GLenum);
static GLint(APIENTRY*model_zero_location)(GLuint,const char*);
static void(APIENTRY*model_zero_uniform)(GLint,GLint);
static int model_zero_shader(void){
 if(model_zero_program&&model_zero_context==preview_context)return 1;
 GLuint(APIENTRY*create)(GLenum)=(void*)wglGetProcAddress("glCreateShader");
 void(APIENTRY*source)(GLuint,GLsizei,const char*const*,const GLint*)=(void*)wglGetProcAddress("glShaderSource");
 void(APIENTRY*compile)(GLuint)=(void*)wglGetProcAddress("glCompileShader");
 void(APIENTRY*get)(GLuint,GLenum,GLint*)=(void*)wglGetProcAddress("glGetShaderiv");
 GLuint(APIENTRY*program)(void)=(void*)wglGetProcAddress("glCreateProgram");
 void(APIENTRY*attach)(GLuint,GLuint)=(void*)wglGetProcAddress("glAttachShader");
 void(APIENTRY*link)(GLuint)=(void*)wglGetProcAddress("glLinkProgram");
 void(APIENTRY*check)(GLuint,GLenum,GLint*)=(void*)wglGetProcAddress("glGetProgramiv");
 void(APIENTRY*remove)(GLuint)=(void*)wglGetProcAddress("glDeleteShader");
 model_zero_use=(void*)wglGetProcAddress("glUseProgram");model_zero_active=(void*)wglGetProcAddress("glActiveTexture");model_zero_location=(void*)wglGetProcAddress("glGetUniformLocation");model_zero_uniform=(void*)wglGetProcAddress("glUniform1i");
 if(!create||!source||!compile||!get||!program||!attach||!link||!check||!remove||!model_zero_use||!model_zero_active||!model_zero_location||!model_zero_uniform)return 0;
 const char*vs="#version 120\nvoid main(){gl_Position=gl_ModelViewProjectionMatrix*gl_Vertex;gl_TexCoord[0]=gl_MultiTexCoord0;}";
#ifdef NF_DIAGNOSTIC_TEXEL_COORDINATES
 const char*fs="#version 120\nuniform sampler2D asset,rowColors;uniform int wallWriter;void main(){vec2 uv=gl_TexCoord[0].xy/gl_TexCoord[0].w;vec4 c=texture2D(asset,uv);if(wallWriter!=0&&c.a<0.25)discard;if(c.a<0.75){gl_FragColor=texture2D(rowColors,vec2(0.5,0.5));}else gl_FragColor=vec4(mod(floor(uv*64.0),64.0)/255.0,1.0,1.0);}";
#else
 const char*fs="#version 120\nuniform sampler2D asset,rowColors;uniform int wallWriter,indexedDisplay,fullPalette;void main(){vec4 c=texture2D(asset,gl_TexCoord[0].xy/gl_TexCoord[0].w);if(wallWriter!=0&&c.a<0.25)discard;float row=clamp(floor((2160.0-gl_FragCoord.y)/13.5),0.0,159.0);if(indexedDisplay!=0){float index=floor(c.r*255.0+0.5);c=vec4(texture2D(rowColors,vec2((index+0.5)/256.0,(row+0.5)/160.0)).rgb,c.a);}else if(c.a<(wallWriter!=0?0.75:0.5)){c=vec4(texture2D(rowColors,vec2(fullPalette!=0?0.5/256.0:0.5,(row+0.5)/160.0)).rgb,0.0);}if(wallWriter!=0&&c.a<0.75)c.a=0.0;gl_FragColor=c;}";
#endif
 GLuint v=create(0x8b31),f=create(0x8b30);source(v,1,&vs,NULL);source(f,1,&fs,NULL);compile(v);compile(f);GLint a,b;get(v,0x8b81,&a);get(f,0x8b81,&b);
 if(!a||!b){remove(v);remove(f);return 0;}
 model_zero_program=program();attach(model_zero_program,v);attach(model_zero_program,f);link(model_zero_program);check(model_zero_program,0x8b82,&a);remove(v);remove(f);if(!a){model_zero_program=0;return 0;}model_zero_context=preview_context;
 model_zero_asset_location=model_zero_location(model_zero_program,"asset");model_zero_rows_location=model_zero_location(model_zero_program,"rowColors");model_zero_writer_location=model_zero_location(model_zero_program,"wallWriter");return model_zero_asset_location>=0&&model_zero_rows_location>=0&&model_zero_writer_location>=0;
}
static GLuint model_zero_texture(unsigned width,unsigned height,const uint8_t*rgba,const uint8_t*indices){
 if(!indices)return preview_texture(width,height,rgba);
 if(!preview_zero_valid)return 0;
 size_t pixels=(size_t)width*height;uint8_t*copy=malloc(pixels*4);if(!copy)return 0;
 memcpy(copy,rgba,pixels*4);for(size_t i=0;i<pixels;i++){copy[i*4+3]=indices[i]?255:0;if(preview_display_palette_valid){copy[i*4]=indices[i];copy[i*4+1]=copy[i*4+2]=0;}}
 GLuint result=preview_texture(width,height,copy);free(copy);return result;
}
static int model_zero_begin(GLuint skin,const uint8_t*indices){
 if(!indices){glBindTexture(GL_TEXTURE_2D,skin);return 1;}
 if(!preview_zero_valid||!model_zero_shader())return 0;
 model_zero_indexed_location=model_zero_location(model_zero_program,"indexedDisplay");model_zero_full_palette_location=model_zero_location(model_zero_program,"fullPalette");
 model_zero_active(0x84c1);GLuint rows=model_zero_row_texture;
 if(preview_display_palette_valid){rows=display_palette_texture(preview_display_palette);if(!rows){model_zero_active(0x84c0);return 0;}}
 else if(!rows||model_zero_row_generation!=preview_generation||model_zero_row_context!=preview_context||memcmp(model_zero_row_source,preview_zero_colors,sizeof(model_zero_row_source))){
  uint8_t colors[160*4];for(unsigned y=0;y<160;y++){unsigned c=preview_zero_colors[y];for(unsigned k=0;k<3;k++){unsigned channel=(c>>(k*5))&31;colors[y*4+k]=(channel<<3)|(channel>>2);}colors[y*4+3]=255;}
  rows=preview_texture(1,160,colors);if(!rows){model_zero_active(0x84c0);return 0;}
  model_zero_row_texture=rows;model_zero_row_generation=preview_generation;model_zero_row_context=preview_context;memcpy(model_zero_row_source,preview_zero_colors,sizeof(model_zero_row_source));
 }
 glBindTexture(GL_TEXTURE_2D,rows);model_zero_active(0x84c0);glBindTexture(GL_TEXTURE_2D,skin);model_zero_use(model_zero_program);model_zero_uniform(model_zero_asset_location,0);model_zero_uniform(model_zero_rows_location,1);model_zero_uniform(model_zero_writer_location,0);model_zero_uniform(model_zero_indexed_location,preview_display_palette_valid);model_zero_uniform(model_zero_full_palette_location,preview_display_palette_valid);model_zero_alpha_test=glIsEnabled(GL_ALPHA_TEST);glDisable(GL_ALPHA_TEST);model_zero_draws++;return 1;
}
static void model_zero_end(const uint8_t*indices){if(indices){model_zero_use(0);if(model_zero_alpha_test)glEnable(GL_ALPHA_TEST);else glDisable(GL_ALPHA_TEST);}}

/* Wall classifications: 0 skip, 1 write output-index zero, 2 write nonzero.
   Encoded alpha belongs only to this private GPU texture, never scene RGBA. */
static GLuint wall_indexed_texture(unsigned width,unsigned height,const uint8_t*rgba,const uint8_t*states,const uint8_t*indices){
 if(!width||!height||width>1024||height>1024||!rgba||!states||!preview_zero_valid)return 0;
 size_t pixels=(size_t)width*height;for(size_t i=0;i<pixels;i++)if(states[i]>2)return 0;
 uint8_t*copy=malloc(pixels*4);if(!copy)return 0;memcpy(copy,rgba,pixels*4);
 for(size_t i=0;i<pixels;i++){copy[i*4+3]=states[i]==2?255:states[i]==1?128:0;if(indices&&preview_display_palette_valid){if((states[i]==2)!=(indices[i]!=0)){free(copy);return 0;}copy[i*4]=indices[i];copy[i*4+1]=copy[i*4+2]=0;}}
 GLuint result=preview_texture(width,height,copy);free(copy);return result;
}
static GLuint wall_zero_texture(unsigned width,unsigned height,const uint8_t*rgba,const uint8_t*states){return wall_indexed_texture(width,height,rgba,states,NULL);}
static int wall_zero_begin(GLuint skin,const uint8_t*states){
 if(!skin||!states||!model_zero_begin(skin,states))return 0;
 model_zero_uniform(model_zero_writer_location,1);model_zero_uniform(model_zero_indexed_location,0);model_zero_draws--;wall_zero_draws++;return 1;
}

/* Original mode4 framebuffer-zero background: owned scanline backdrop, no BG2. */
static int model_zero_background_draw(void){
 if(!preview_zero_background)return 1;
 if(!preview_zero_valid)return 0;
 glPushAttrib(GL_ENABLE_BIT|GL_TEXTURE_BIT|GL_CURRENT_BIT|GL_DEPTH_BUFFER_BIT|GL_COLOR_BUFFER_BIT);
 glDisable(GL_BLEND);glDisable(GL_DEPTH_TEST);glDepthMask(GL_FALSE);glEnable(GL_TEXTURE_2D);
 uint8_t zero[4]={0,0,0,0};GLuint skin=preview_texture(1,1,zero);
 if(!skin||!model_zero_begin(skin,zero)){glPopAttrib();return 0;}
 model_zero_draws--; /* Background is not a model draw. */
 glColor4f(1,1,1,1);glBegin(GL_QUADS);
 glTexCoord4d(.5,.5,0,1);glVertex2d(0,0);glVertex2d(240,0);glVertex2d(240,160);glVertex2d(0,160);glEnd();
 model_zero_end(zero);
 glPopAttrib();return 1;
}



