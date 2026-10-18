/* Split scratch storage belongs exclusively to the current renderer context. */
static GLuint preview_split_scratch;
/* Renderer-owned resources survive snapshot replacement within one context. */
#ifndef NF_PREVIEW_TEXTURE_BUDGET
#define NF_PREVIEW_TEXTURE_BUDGET (128u*1024u*1024u)
#endif
#ifndef NF_PREVIEW_TEXTURE_SLOTS
#define NF_PREVIEW_TEXTURE_SLOTS 1024u
#endif
typedef struct {GLuint texture;unsigned width,height;uint64_t hash,generation;size_t bytes;uint8_t*pixels;} PreviewTexture;
static PreviewTexture preview_textures[NF_PREVIEW_TEXTURE_SLOTS];
static size_t preview_texture_bytes;
static uint64_t preview_generation;
static unsigned preview_uploads,preview_hits,preview_contexts;
static unsigned preview_evictions;
static double preview_finish_wall_ms;static unsigned preview_finish_calls;
static uint64_t preview_uploaded_bytes;
/* Frame-local call order is a candidate hint only. Cached owned bytes must
   still match exactly; reordered/replaced scenes safely fall back to hashing. */
static unsigned preview_texture_hints[NF_PREVIEW_TEXTURE_SLOTS];
static unsigned preview_texture_hint_cursor,preview_texture_hint_hits;
static uint64_t preview_texture_hint_generation,preview_texture_hash_bytes_saved;
static int preview_force_context_rebind;
static int preview_keep_context;
static int preview_window_output;
static HWND preview_window;static HDC preview_dc;static HGLRC preview_context;
static GLuint preview_target,preview_fbo;
#ifdef NF_DIAGNOSTIC_DEPTH
static GLuint preview_depth;
#endif
static int preview_evict(void){
 unsigned oldest=NF_PREVIEW_TEXTURE_SLOTS;
 for(unsigned i=0;i<NF_PREVIEW_TEXTURE_SLOTS;i++)if(preview_textures[i].pixels&&preview_textures[i].generation!=preview_generation){
  if(oldest==NF_PREVIEW_TEXTURE_SLOTS||preview_textures[i].generation<preview_textures[oldest].generation)oldest=i;
 }
 if(oldest==NF_PREVIEW_TEXTURE_SLOTS)return 0;
 PreviewTexture*t=preview_textures+oldest;glDeleteTextures(1,&t->texture);free(t->pixels);preview_texture_bytes-=t->bytes;memset(t,0,sizeof(*t));preview_evictions++;return 1;
}
static GLuint preview_texture(unsigned width,unsigned height,const uint8_t*pixels){
 size_t bytes=(size_t)width*height*4;if(bytes>NF_PREVIEW_TEXTURE_BUDGET)return 0;
 if(preview_texture_hint_generation!=preview_generation){preview_texture_hint_generation=preview_generation;preview_texture_hint_cursor=0;}
 unsigned ordinal=preview_texture_hint_cursor++;
 if(ordinal<NF_PREVIEW_TEXTURE_SLOTS&&preview_texture_hints[ordinal]){
  unsigned candidate=preview_texture_hints[ordinal]-1;PreviewTexture*t=preview_textures+candidate;
  if(t->pixels&&t->width==width&&t->height==height&&!memcmp(t->pixels,pixels,bytes)){
   t->generation=preview_generation;preview_hits++;preview_texture_hint_hits++;preview_texture_hash_bytes_saved+=bytes;return t->texture;
  }
 }
 /* Hash full content eight bytes at a time; memcpy permits unaligned callers.
    Hashes only filter candidates: exact byte comparison still decides reuse. */
 uint64_t hash=14695981039346656037ull;size_t at=0;
 for(;bytes-at>=8;at+=8){uint64_t word;memcpy(&word,pixels+at,8);hash^=word;hash*=1099511628211ull;}
 for(;at<bytes;at++){hash^=pixels[at];hash*=1099511628211ull;}
 for(unsigned i=0;i<NF_PREVIEW_TEXTURE_SLOTS;i++){
  PreviewTexture*t=preview_textures+i;
  if(t->pixels&&t->width==width&&t->height==height&&t->hash==hash&&!memcmp(t->pixels,pixels,bytes)){t->generation=preview_generation;preview_hits++;if(ordinal<NF_PREVIEW_TEXTURE_SLOTS)preview_texture_hints[ordinal]=i+1;return t->texture;}
 }
 while(preview_texture_bytes+bytes>NF_PREVIEW_TEXTURE_BUDGET)if(!preview_evict())return 0;
 unsigned slot=0;while(slot<NF_PREVIEW_TEXTURE_SLOTS&&preview_textures[slot].pixels)slot++;
 if(slot==NF_PREVIEW_TEXTURE_SLOTS){if(!preview_evict())return 0;for(slot=0;preview_textures[slot].pixels;slot++);}
 uint8_t*copy=malloc(bytes);if(!copy)return 0;memcpy(copy,pixels,bytes);
 GLuint texture;glGenTextures(1,&texture);glBindTexture(GL_TEXTURE_2D,texture);
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
 glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,width,height,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
 preview_textures[slot]=(PreviewTexture){texture,width,height,hash,preview_generation,bytes,copy};preview_texture_bytes+=bytes;preview_uploads++;preview_uploaded_bytes+=bytes;if(ordinal<NF_PREVIEW_TEXTURE_SLOTS)preview_texture_hints[ordinal]=slot+1;return texture;
}
static int preview_context_open(void){
 if(preview_context){
  /* The persistent worker already owns this exact binding. Migrated or
     detached contexts still take the normal make-current path. */
  if(!preview_force_context_rebind&&!getenv("NF_PREVIEW_REBIND_ALWAYS")&&wglGetCurrentContext()==preview_context&&wglGetCurrentDC()==preview_dc)return 0;
  return wglMakeCurrent(preview_dc,preview_context)?0:9;
 }
 HINSTANCE instance=GetModuleHandle(NULL);WNDCLASSA wc={0};wc.lpfnWndProc=DefWindowProcA;wc.hInstance=instance;wc.lpszClassName="NFSModelPreview";wc.style=CS_OWNDC;RegisterClassA(&wc);
 DWORD style=preview_window_output?WS_OVERLAPPEDWINDOW:WS_OVERLAPPED;RECT bounds={0,0,preview_window_output?1280:16,preview_window_output?720:16};AdjustWindowRect(&bounds,style,FALSE);
 preview_window=CreateWindowA(wc.lpszClassName,"NFSUG native renderer diagnostic",style,0,0,bounds.right-bounds.left,bounds.bottom-bounds.top,NULL,NULL,instance,NULL);preview_dc=GetDC(preview_window);
 PIXELFORMATDESCRIPTOR pfd={0};pfd.nSize=sizeof(pfd);pfd.nVersion=1;pfd.dwFlags=PFD_DRAW_TO_WINDOW|PFD_SUPPORT_OPENGL;pfd.iPixelType=PFD_TYPE_RGBA;pfd.cColorBits=32;
 if(preview_window_output)pfd.dwFlags|=PFD_DOUBLEBUFFER;
 int format=ChoosePixelFormat(preview_dc,&pfd);if(!format||!SetPixelFormat(preview_dc,format,&pfd))return 8;
 preview_context=wglCreateContext(preview_dc);if(!preview_context||!wglMakeCurrent(preview_dc,preview_context))return 9;preview_contexts++;
  fprintf(stderr,"native_gl vendor=%s renderer=%s version=%s\n",glGetString(GL_VENDOR),glGetString(GL_RENDERER),glGetString(GL_VERSION));
 fprintf(stderr,"native_gl timer_query=%u timestamp_query=%u sync_fence=%u\n",wglGetProcAddress("glGetQueryObjectui64v")!=NULL&&wglGetProcAddress("glBeginQuery")!=NULL,wglGetProcAddress("glQueryCounter")!=NULL,wglGetProcAddress("glFenceSync")!=NULL);
 void(APIENTRY*gen)(GLsizei,GLuint*)=(void*)wglGetProcAddress("glGenFramebuffers");
 void(APIENTRY*bind)(GLenum,GLuint)=(void*)wglGetProcAddress("glBindFramebuffer");
 void(APIENTRY*attach)(GLenum,GLenum,GLenum,GLuint,GLint)=(void*)wglGetProcAddress("glFramebufferTexture2D");
 GLenum(APIENTRY*check)(GLenum)=(void*)wglGetProcAddress("glCheckFramebufferStatus");if(!gen||!bind||!attach||!check)return 10;
 glGenTextures(1,&preview_target);glBindTexture(GL_TEXTURE_2D,preview_target);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,3840,2160,0,GL_RGBA,GL_UNSIGNED_BYTE,NULL);
 gen(1,&preview_fbo);bind(0x8d40,preview_fbo);attach(0x8d40,0x8ce0,GL_TEXTURE_2D,preview_target,0);
#ifdef NF_DIAGNOSTIC_DEPTH
 glGenTextures(1,&preview_depth);glBindTexture(GL_TEXTURE_2D,preview_depth);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
 /* Zero-to-one clipping avoids cancellation of small reciprocal depths. */
 void(APIENTRY*clip_control)(GLenum,GLenum)=(void*)wglGetProcAddress("glClipControl");if(!clip_control)return 29;
 clip_control(0x8ca1,0x935f);
 glTexImage2D(GL_TEXTURE_2D,0,0x8cac,3840,2160,0,GL_DEPTH_COMPONENT,GL_FLOAT,NULL);attach(0x8d40,0x8d00,GL_TEXTURE_2D,preview_depth,0);
#endif
 return check(0x8d40)==0x8cd5?0:11;
}
static void preview_shutdown(void){
 if(preview_context){
  for(unsigned i=0;i<NF_PREVIEW_TEXTURE_SLOTS;i++){PreviewTexture*t=preview_textures+i;if(t->pixels){glDeleteTextures(1,&t->texture);free(t->pixels);}}
  memset(preview_textures,0,sizeof(preview_textures));preview_texture_bytes=0;
  memset(preview_texture_hints,0,sizeof(preview_texture_hints));preview_texture_hint_cursor=0;preview_texture_hint_generation=0;
  void(APIENTRY*remove_fbo)(GLsizei,const GLuint*)=(void*)wglGetProcAddress("glDeleteFramebuffers");if(remove_fbo&&preview_fbo)remove_fbo(1,&preview_fbo);
  #ifdef NF_DIAGNOSTIC_DEPTH
  glDeleteTextures(1,&preview_depth);preview_depth=0;
#endif
  if(preview_split_scratch){glDeleteTextures(1,&preview_split_scratch);preview_split_scratch=0;}
  glDeleteTextures(1,&preview_target);wglMakeCurrent(NULL,NULL);wglDeleteContext(preview_context);
 }
 if(preview_dc)ReleaseDC(preview_window,preview_dc);
 if(preview_window)DestroyWindow(preview_window);
 preview_context=NULL;preview_dc=NULL;preview_window=NULL;preview_target=preview_fbo=0;
}
