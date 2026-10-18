#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "scene.h"
#include "gpu.h"
#include "texture_pack.h"
#include "ui_scale.h"
#include "ui_gl_texture.h"
#include "hash_region.h"
#define FB 0x8D40
#define ATTACHMENT 0x8CE0
#define COMPLETE 0x8CD5
static void(APIENTRY* GenFramebuffers)(GLsizei,GLuint*);
static void(APIENTRY* BindFramebuffer)(GLenum,GLuint);
static void(APIENTRY* FramebufferTexture2D)(GLenum,GLenum,GLenum,GLuint,GLint);
static GLenum(APIENTRY* CheckFramebufferStatus)(GLenum);
static void(APIENTRY* DeleteFramebuffers)(GLsizei,const GLuint*);
static GLuint fbo,target,reference,overlay;
static uint32_t texture_pixels[1024*1024],overlay_pixels[240*160];
static uint32_t ui_scale_scratch[NF_UI_SOURCE_WIDTH*2*NF_UI_SOURCE_HEIGHT*2];
static uint32_t ui_scale_output[NF_UI_SCALED_WIDTH*NF_UI_SCALED_HEIGHT];
static int poly_count;
static uint32_t palette_hash;
static uint32_t layer_overlay_hash,layer_background_hash,layer_overlay_pixel_count;
static int layer_overlay_active,layer_audit_enabled;
static uint32_t hash_pixels(const uint32_t* pixels,size_t count){uint32_t hash=2166136261u;for(size_t i=0;i<count;i++)hash=(hash^pixels[i])*16777619u;return hash;}
typedef struct {NFPoly spec;GLuint gl;unsigned refreshed;uint64_t source_hash;int replacement;int tex_width,tex_height;int borrowed;} CachedTexture;
typedef struct {uint64_t source_hash;GLuint gl;uint32_t width,height;} PrewarmedTexture;
static CachedTexture cache[256];static unsigned cache_count;
static PrewarmedTexture* prewarmed_textures;static size_t prewarmed_count;static uint64_t prewarmed_bytes;
static NFUiFrameCache ui_frame_replacement_cache;
#define NF_GPU_TEXTURE_PREWARM_MAX_BYTES (UINT64_C(1024)*1024u*1024u)
static unsigned draw_serial;
static char texture_pack_root[MAX_PATH],texture_inventory_root[MAX_PATH];
static int texture_pack_enabled,texture_export_enabled,ui_overlay_export_enabled;
static uint64_t ui_overlay_capture_hashes[512],ui_frame_capture_hashes[512];
static unsigned ui_overlay_capture_count,ui_frame_capture_count;
static int motion_profile_enabled;
static int motion_verify_enabled;
static int motion_legacy_forced;
static uint64_t motion_profile_calls,motion_profile_total_ns,motion_profile_max_ns,motion_profile_candidates,motion_profile_legacy_cost_calls;
static uint64_t motion_verify_scene_pairs,motion_verify_mismatches;
static FILE* texture_pack_trace;static uint64_t texture_pack_trace_hash;
static int texture_pack_trace_all;static int texture_pack_filter_nearest;static unsigned texture_pack_trace_rows;
static FILE* texture_upload_trace;static LARGE_INTEGER texture_upload_frequency;
static FILE* ui_gl_trace;
static void trace_ui_gl_errors(const char* stage){
 if(!ui_gl_trace)return;
 GLenum error;while((error=glGetError())!=GL_NO_ERROR)fprintf(ui_gl_trace,"gl-error\t%u\t%s\t0x%04x\n",draw_serial,stage,(unsigned)error);
 fflush(ui_gl_trace);
}
static void trace_texture(const char* event,const NFPoly* p,const CachedTexture* entry){
 if(!texture_pack_trace||!p||!entry||(!texture_pack_trace_all&&entry->source_hash!=texture_pack_trace_hash)||texture_pack_trace_rows>=100000)return;
 float s0=INFINITY,s1=-INFINITY,t0=INFINITY,t1=-INFINITY,x0=INFINITY,x1=-INFINITY,y0=INFINITY,y1=-INFINITY,q0=INFINITY,q1=-INFINITY;
 for(unsigned i=0;i<p->count;i++){const NFVertex*v=&p->v[i];if(v->s<s0)s0=v->s;if(v->s>s1)s1=v->s;if(v->t<t0)t0=v->t;if(v->t>t1)t1=v->t;if(v->x<x0)x0=v->x;if(v->x>x1)x1=v->x;if(v->y<y0)y0=v->y;if(v->y>y1)y1=v->y;if(v->q<q0)q0=v->q;if(v->q>q1)q1=v->q;}
 fprintf(texture_pack_trace,"%s\t%u\t%016llx\t%08x\t%u\t%u\t%u\t%u\t%d\t%u\t%u\t%u\t%.7g\t%.7g\t%.7g\t%.7g\t%.7g\t%.7g\t%.7g\t%.7g\t%.7g\t%.7g\n",event,draw_serial,(unsigned long long)entry->source_hash,p->address,p->width,p->height,p->stride,p->kind,p->shade,(unsigned)entry->replacement,(unsigned)entry->tex_width,(unsigned)entry->tex_height,s0,s1,t0,t1,x0,x1,y0,y1,q0,q1);
 texture_pack_trace_rows++;
}
void* nf_pixels(void);unsigned nf_read(unsigned,int);
void nf_gpu_audit_layers(int enabled){layer_audit_enabled=!!enabled;layer_overlay_hash=layer_background_hash=layer_overlay_pixel_count=0;layer_overlay_active=0;}
void nf_gpu_audit_frame_begin(void){if(layer_audit_enabled){layer_overlay_hash=layer_background_hash=layer_overlay_pixel_count=0;layer_overlay_active=0;}}
uint32_t nf_gpu_reference_hash(void){return hash_pixels((const uint32_t*)nf_pixels(),240u*160u);}
uint32_t nf_gpu_source_region_hash(unsigned x,unsigned y,unsigned width,unsigned height){
 return nf_hash_u32_region((const uint32_t*)nf_pixels(),240u,160u,x,y,width,height);
}
uint32_t nf_gpu_overlay_hash(void){return layer_overlay_hash;}
uint32_t nf_gpu_background_hash(void){return layer_background_hash;}
uint32_t nf_gpu_overlay_pixel_count(void){return layer_overlay_pixel_count;}
int nf_gpu_overlay_active(void){return layer_overlay_active;}
static void setup_texture(GLuint id,int w,int h,const void* bytes,int filter){
 glBindTexture(GL_TEXTURE_2D,id);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,filter);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,filter);
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);
 glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,w,h,0,GL_RGBA,GL_UNSIGNED_BYTE,bytes);
}
static void polygon_cache_clear(void){for(unsigned i=0;i<cache_count;i++)if(!cache[i].borrowed)glDeleteTextures(1,&cache[i].gl);cache_count=0;}
static void prewarmed_textures_clear(void){if(prewarmed_textures){for(size_t i=0;i<prewarmed_count;i++)if(prewarmed_textures[i].gl)glDeleteTextures(1,&prewarmed_textures[i].gl);free(prewarmed_textures);}prewarmed_textures=NULL;prewarmed_count=0;prewarmed_bytes=0;}
static PrewarmedTexture* prewarmed_texture_find(uint64_t source_hash){size_t lo=0,hi=prewarmed_count;while(lo<hi){size_t mid=lo+(hi-lo)/2;uint64_t hash=prewarmed_textures[mid].source_hash;if(hash<source_hash)lo=mid+1;else hi=mid;}return lo<prewarmed_count&&prewarmed_textures[lo].source_hash==source_hash?&prewarmed_textures[lo]:NULL;}
static void prewarm_pack_textures(void){
 GLint max_dimension=0;glGetIntegerv(GL_MAX_TEXTURE_SIZE,&max_dimension);if(max_dimension<=0)return;
 size_t entries=nf_texture_pack_cache_index_count();if(!entries)return;
 PrewarmedTexture* warmed=(PrewarmedTexture*)calloc(entries,sizeof(*warmed));if(!warmed)return;
 for(size_t i=0;i<entries;i++){
  uint64_t hash=0;uint32_t width=0,height=0;const uint32_t* pixels=NULL;
  if(!nf_texture_pack_cache_preloaded_at(i,&hash,&width,&height,&pixels)||
     !hash||!pixels||width>(uint32_t)max_dimension||height>(uint32_t)max_dimension)continue;
  if(!nf_texture_payload_fits_budget(width,height,prewarmed_bytes,
                                      NF_GPU_TEXTURE_PREWARM_MAX_BYTES))continue;
  uint64_t bytes=(uint64_t)width*height*sizeof(*pixels);
  GLuint id=0;glGenTextures(1,&id);if(!id)continue;
  while(glGetError()!=GL_NO_ERROR){}
  GLint filter=texture_pack_filter_nearest?GL_NEAREST:GL_LINEAR;
  setup_texture(id,(int)width,(int)height,pixels,filter);
  if(glGetError()!=GL_NO_ERROR){glDeleteTextures(1,&id);continue;}
  warmed[prewarmed_count].source_hash=hash;warmed[prewarmed_count].gl=id;
  warmed[prewarmed_count].width=width;warmed[prewarmed_count].height=height;
  prewarmed_count++;prewarmed_bytes+=bytes;
 }
 if(!prewarmed_count){free(warmed);return;}
 prewarmed_textures=warmed;
}
static int ui_frame_replacement_load(void* context,uint64_t source_hash,uint32_t** pixels,uint32_t* width,uint32_t* height){
 (void)context;return nf_texture_pack_load_cached(texture_pack_root,source_hash,NF_UI_SOURCE_WIDTH,NF_UI_SOURCE_HEIGHT,pixels,width,height);
}
static int ui_frame_replacement_upload(void* context,const uint32_t* pixels,uint32_t width,uint32_t height,uint32_t* handle){
 (void)context;return nf_ui_gl_texture_upload_rgba(pixels,width,height,handle);
}
static void ui_frame_replacement_delete(void* context,uint32_t handle){
 (void)context;nf_ui_gl_texture_delete(handle);
}
static void ui_frame_replacement_clear(void){
 nf_ui_frame_cache_clear(&ui_frame_replacement_cache,ui_frame_replacement_delete,NULL);
}
static GLuint ui_frame_replacement_get(uint64_t source_hash){
 GLuint handle=(GLuint)nf_ui_frame_cache_get(&ui_frame_replacement_cache,source_hash,
        NF_UI_FRAME_CACHE_MAX_BYTES,ui_frame_replacement_load,
        ui_frame_replacement_upload,ui_frame_replacement_delete,NULL);
 if(ui_gl_trace){fprintf(ui_gl_trace,"ui-cache\t%u\t%016llx\t%u\n",draw_serial,(unsigned long long)source_hash,(unsigned)handle);fflush(ui_gl_trace);}
 return handle;
}
int nf_gpu_init(void){
 char motion_switch[8]={0};motion_profile_enabled=GetEnvironmentVariableA("NFSUG_PROFILE_MOTION_MATCH",motion_switch,sizeof(motion_switch))>0&&motion_switch[0]!='0';
 char verify_switch[8]={0};motion_verify_enabled=GetEnvironmentVariableA("NFSUG_VERIFY_MOTION_MATCH",verify_switch,sizeof(verify_switch))>0&&verify_switch[0]!='0';
 char legacy_switch[8]={0};motion_legacy_forced=GetEnvironmentVariableA("NFSUG_FORCE_LEGACY_MOTION_MATCH",legacy_switch,sizeof(legacy_switch))>0&&legacy_switch[0]!='0';
 motion_profile_calls=motion_profile_total_ns=motion_profile_max_ns=motion_profile_candidates=motion_profile_legacy_cost_calls=0;
 motion_verify_scene_pairs=motion_verify_mismatches=0;
 GenFramebuffers=(void*)wglGetProcAddress("glGenFramebuffers");BindFramebuffer=(void*)wglGetProcAddress("glBindFramebuffer");FramebufferTexture2D=(void*)wglGetProcAddress("glFramebufferTexture2D");CheckFramebufferStatus=(void*)wglGetProcAddress("glCheckFramebufferStatus");DeleteFramebuffers=(void*)wglGetProcAddress("glDeleteFramebuffers");
 if(!GenFramebuffers||!BindFramebuffer||!FramebufferTexture2D||!CheckFramebufferStatus||!DeleteFramebuffers)return 0;
 glGenTextures(1,&target);setup_texture(target,3840,2160,NULL,GL_LINEAR);GenFramebuffers(1,&fbo);BindFramebuffer(FB,fbo);FramebufferTexture2D(FB,ATTACHMENT,GL_TEXTURE_2D,target,0);
 int ok=CheckFramebufferStatus(FB)==COMPLETE;BindFramebuffer(FB,0);
 GetModuleFileNameA(NULL,texture_pack_root,sizeof(texture_pack_root));char* slash=strrchr(texture_pack_root,'\\');if(slash)*slash=0;else texture_pack_root[0]=0;
 char ui_trace_switch[8]={0};if(GetEnvironmentVariableA("NFSUG_UI_GL_TRACE",ui_trace_switch,sizeof(ui_trace_switch))>0&&ui_trace_switch[0]!='0'){char trace_path[MAX_PATH];int trace_n=snprintf(trace_path,sizeof(trace_path),"%s\\ui-gl-trace.tsv",texture_pack_root);if(trace_n>0&&(size_t)trace_n<sizeof(trace_path)){ui_gl_trace=fopen(trace_path,"w");if(ui_gl_trace)fprintf(ui_gl_trace,"event\tdraw_serial\tstage_or_source_hash\tvalue\n");}}
 char filter_switch[16]={0};DWORD filter_length=GetEnvironmentVariableA("NFSUG_TEXTURE_PACK_FILTER",filter_switch,sizeof(filter_switch));texture_pack_filter_nearest=filter_length>0&&filter_length<sizeof(filter_switch)&&!_stricmp(filter_switch,"nearest");
 char trace_switch[32]={0};DWORD trace_length=GetEnvironmentVariableA("NFSUG_TEXTURE_PACK_TRACE_HASH",trace_switch,sizeof(trace_switch));if(trace_length>0&&trace_length<sizeof(trace_switch)){texture_pack_trace_all=!_stricmp(trace_switch,"all")||!strcmp(trace_switch,"*");texture_pack_trace_hash=texture_pack_trace_all?0:(uint64_t)strtoull(trace_switch,NULL,16);if(texture_pack_trace_all||texture_pack_trace_hash){char trace_path[MAX_PATH];int trace_n=snprintf(trace_path,sizeof(trace_path),"%s\\texture-pack-trace.tsv",texture_pack_root);if(trace_n>0&&(size_t)trace_n<sizeof(trace_path)){texture_pack_trace=fopen(trace_path,"w");if(texture_pack_trace){fprintf(texture_pack_trace,"event\tdraw_serial\tsource_hash\taddress_hex\tsource_width\tsource_height\tstride\tkind\tshade\treplacement\tbound_width\tbound_height\ts_min\ts_max\tt_min\tt_max\tx_min\tx_max\ty_min\ty_max\tq_min\tq_max\n");setvbuf(texture_pack_trace,NULL,_IONBF,0);}}}}
 char upload_trace_switch[8]={0};if(GetEnvironmentVariableA("NFSUG_TEXTURE_UPLOAD_TRACE",upload_trace_switch,sizeof(upload_trace_switch))>0&&upload_trace_switch[0]!='0'){
  char trace_path[MAX_PATH];int trace_n=snprintf(trace_path,sizeof(trace_path),"%s\\texture-upload-timing.tsv",texture_pack_root);
 if(trace_n>0&&(size_t)trace_n<sizeof(trace_path)){texture_upload_trace=fopen(trace_path,"w");if(texture_upload_trace){if(!QueryPerformanceFrequency(&texture_upload_frequency)||texture_upload_frequency.QuadPart<=0){fclose(texture_upload_trace);texture_upload_trace=NULL;}else fprintf(texture_upload_trace,"event\tdraw_serial\tsource_hash\taddress_hex\tsource_width\tsource_height\tbound_width\tbound_height\treplacement\tpack_load_ms\tteximage_ms\tgl_error_ms\n");}}
 }
 char export_switch[8]={0};texture_export_enabled=GetEnvironmentVariableA("NFSUG_DUMP_TEXTURES",export_switch,sizeof(export_switch))>0&&export_switch[0]!='0';
 char ui_export_switch[8]={0};ui_overlay_export_enabled=GetEnvironmentVariableA("NFSUG_DUMP_UI_FRAMES",ui_export_switch,sizeof(ui_export_switch))>0&&ui_export_switch[0]!='0';
 if(texture_export_enabled||ui_overlay_export_enabled){snprintf(texture_inventory_root,sizeof(texture_inventory_root),"%s\\texture-source-inventory",texture_pack_root);if(!CreateDirectoryA(texture_inventory_root,NULL)&&GetLastError()!=ERROR_ALREADY_EXISTS){texture_export_enabled=0;ui_overlay_export_enabled=0;}}
 glGenTextures(1,&reference);setup_texture(reference,240,160,NULL,GL_NEAREST);glGenTextures(1,&overlay);setup_texture(overlay,240,160,NULL,GL_NEAREST);
 return ok;
}
int nf_gpu_texture_pack_available(void){return nf_texture_pack_ready(texture_pack_root);}
void nf_gpu_texture_pack(int enabled){
 trace_ui_gl_errors("pack-before-enable");
 enabled=enabled&&nf_gpu_texture_pack_available();
 if(enabled){if(!nf_texture_pack_cache_prepare(texture_pack_root))enabled=0;else (void)nf_texture_pack_cache_preload(texture_pack_root);}
 trace_ui_gl_errors("pack-after-cpu-load");
 if(enabled==texture_pack_enabled)return;
 polygon_cache_clear();prewarmed_textures_clear();ui_frame_replacement_clear();texture_pack_enabled=enabled;
 if(enabled)prewarm_pack_textures();
 trace_ui_gl_errors("pack-after-gl-prewarm");
 unsigned width=enabled?NF_UI_SCALED_WIDTH:NF_UI_SOURCE_WIDTH;
 unsigned height=enabled?NF_UI_SCALED_HEIGHT:NF_UI_SOURCE_HEIGHT;
 setup_texture(reference,(int)width,(int)height,NULL,enabled?GL_LINEAR:GL_NEAREST);
 setup_texture(overlay,(int)width,(int)height,NULL,GL_NEAREST);
 trace_ui_gl_errors("pack-after-ui-targets");
}
static void projection(float w,float h){glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(0,w,h,0,-1,1);glMatrixMode(GL_MODELVIEW);glLoadIdentity();}
static void quad(GLuint id,int invert){
 glBindTexture(GL_TEXTURE_2D,id);glColor4f(1,1,1,1);glBegin(GL_QUADS);glTexCoord2f(0,invert?1:0);glVertex2f(0,0);glTexCoord2f(1,invert?1:0);glVertex2f(240,0);glTexCoord2f(1,invert?0:1);glVertex2f(240,160);glTexCoord2f(0,invert?0:1);glVertex2f(0,160);glEnd();
}
static int upload_texture(CachedTexture* entry,const NFPoly* p,const uint32_t* original,uint64_t source_hash){
 uint32_t* replacement=NULL;uint32_t width=p->width,height=p->height;const uint32_t* pixels=original;int has_replacement=0;
 LARGE_INTEGER load_begin={0},load_end={0},upload_end={0},error_end={0};if(texture_upload_trace)QueryPerformanceCounter(&load_begin);
 PrewarmedTexture* warm=texture_pack_enabled&&source_hash?prewarmed_texture_find(source_hash):NULL;
 if(warm&&warm->width>=p->width&&warm->height>=p->height){
  if(!entry->borrowed)glDeleteTextures(1,&entry->gl);
  entry->gl=warm->gl;entry->borrowed=1;has_replacement=1;width=warm->width;height=warm->height;
  if(texture_upload_trace){QueryPerformanceCounter(&load_end);QueryPerformanceCounter(&upload_end);QueryPerformanceCounter(&error_end);double scale=1000.0/(double)texture_upload_frequency.QuadPart;fprintf(texture_upload_trace,"replacement-prewarmed\t%u\t%016llx\t%08x\t%u\t%u\t%u\t%u\t1\t%.3f\t0\t0\n",draw_serial,(unsigned long long)source_hash,p->address,p->width,p->height,width,height,(load_end.QuadPart-load_begin.QuadPart)*scale);}
  entry->source_hash=source_hash;entry->replacement=1;entry->tex_width=(int)width;entry->tex_height=(int)height;trace_texture("prewarmed-bind",p,entry);return 1;
 }
 if(entry->borrowed){entry->gl=0;glGenTextures(1,&entry->gl);entry->borrowed=0;if(!entry->gl)return 0;}
 if(texture_pack_enabled&&source_hash&&nf_texture_pack_load_cached(texture_pack_root,source_hash,p->width,p->height,&replacement,&width,&height)){
  pixels=replacement;has_replacement=1;
 }else{width=p->width;height=p->height;}
 if(texture_upload_trace)QueryPerformanceCounter(&load_end);
 GLint filter=has_replacement&&!texture_pack_filter_nearest?GL_LINEAR:GL_NEAREST;
 glBindTexture(GL_TEXTURE_2D,entry->gl);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,filter);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,filter);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);
 glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,(GLsizei)width,(GLsizei)height,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
 if(texture_upload_trace)QueryPerformanceCounter(&upload_end);
 free(replacement);int gl_error=glGetError();
 if(texture_upload_trace){QueryPerformanceCounter(&error_end);double scale=1000.0/(double)texture_upload_frequency.QuadPart;fprintf(texture_upload_trace,"%s\t%u\t%016llx\t%08x\t%u\t%u\t%u\t%u\t%d\t%.3f\t%.3f\t%.3f\n",has_replacement?"replacement":"original",draw_serial,(unsigned long long)source_hash,p->address,p->width,p->height,width,height,has_replacement,(load_end.QuadPart-load_begin.QuadPart)*scale,(upload_end.QuadPart-load_end.QuadPart)*scale,(error_end.QuadPart-upload_end.QuadPart)*scale);}
 if(gl_error!=GL_NO_ERROR)return 0;
 entry->source_hash=source_hash;entry->replacement=has_replacement;entry->tex_width=(int)width;entry->tex_height=(int)height;trace_texture(has_replacement?"upload-replaced":"upload-original",p,entry);return 1;
}
/* Opt-in source export for building an audited replacement pack. Polygon
   and UI captures are disabled by default; UI capture is hash-deduplicated
   and bounded separately for full frames and transparent overlays. */
static void dump_texture_source(const NFPoly* p,const uint32_t* rgba,uint64_t hash){
 if(!p||!rgba||!hash||!p->width||!p->height)return;
 int ui_capture=p->kind==4||p->kind==5;
 if((ui_capture&&!ui_overlay_export_enabled)||(!ui_capture&&!texture_export_enabled))return;
 uint64_t bytes=(uint64_t)p->width*p->height*sizeof(*rgba);if(bytes>sizeof(texture_pixels))return;
 char filename[40],path[MAX_PATH],manifest[MAX_PATH];snprintf(filename,sizeof(filename),"%016llx.rgba",(unsigned long long)hash);
 int n=snprintf(path,sizeof(path),"%s\\%s",texture_inventory_root,filename);if(n<=0||(size_t)n>=sizeof(path))return;
 DWORD attributes=GetFileAttributesA(path);
 if(attributes==INVALID_FILE_ATTRIBUTES){FILE* f=fopen(path,"wb");if(!f)return;int ok=fwrite(rgba,1,(size_t)bytes,f)==(size_t)bytes;if(fclose(f)!=0)ok=0;if(!ok){DeleteFileA(path);return;}}
 else if(!ui_capture)return;
 n=snprintf(manifest,sizeof(manifest),"%s\\source-inventory.tsv",texture_inventory_root);if(n<=0||(size_t)n>=sizeof(manifest)){if(attributes==INVALID_FILE_ATTRIBUTES)DeleteFileA(path);return;}
 FILE* f=fopen(manifest,"ab");if(!f){if(attributes==INVALID_FILE_ATTRIBUTES)DeleteFileA(path);return;}fprintf(f,"%016llx\t%u\t%u\t%08x\t%u\t%u\t%u\t%lu\t%u\n",(unsigned long long)hash,p->width,p->height,p->address,p->kind,(unsigned)p->stride,(unsigned)p->shade,(unsigned long)GetCurrentProcessId(),draw_serial);if(fclose(f)!=0&&attributes==INVALID_FILE_ATTRIBUTES)DeleteFileA(path);
}
static void dump_ui_source(const uint32_t* rgba,uint64_t hash,unsigned kind){
 if(!ui_overlay_export_enabled||!rgba||!hash||(kind!=4&&kind!=5))return;
 if(kind==4&&!nf_ui_overlay_has_content(rgba,NF_UI_SOURCE_WIDTH*NF_UI_SOURCE_HEIGHT))return;
 uint64_t* hashes=kind==4?ui_overlay_capture_hashes:ui_frame_capture_hashes;unsigned* count=kind==4?&ui_overlay_capture_count:&ui_frame_capture_count;
 for(unsigned i=0;i<*count;i++)if(hashes[i]==hash)return;
 if(*count>=512)return;
 NFPoly source={0};source.width=240;source.height=160;source.stride=240;source.address=0xffffffffu;source.kind=(uint8_t)kind;
 dump_texture_source(&source,rgba,hash);hashes[(*count)++]=hash;
}
static CachedTexture* texture_for(const NFPoly* p){
 unsigned i;for(i=0;i<cache_count;i++){NFPoly* s=&cache[i].spec;if(s->address==p->address&&s->width==p->width&&s->height==p->height&&s->stride==p->stride&&s->shade==p->shade&&s->kind==p->kind)break;}
 if(i==cache_count){if(cache_count==256||!nf_texture(p,texture_pixels))return NULL;memset(&cache[i],0,sizeof(cache[i]));cache[i].spec=*p;glGenTextures(1,&cache[i].gl);uint64_t hash=nf_texture_source_hash(texture_pixels,p->width,p->height);dump_texture_source(p,texture_pixels,hash);if(!upload_texture(&cache[i],p,texture_pixels,hash)){glDeleteTextures(1,&cache[i].gl);return NULL;}cache_count++;}
 /* RAM-backed car skins may change in place. Their source hash selects an
    exact replacement; otherwise update from the current original pixels. */
 else if(p->address<0x08000000&&cache[i].refreshed!=draw_serial){if(!nf_texture(p,texture_pixels))return NULL;uint64_t hash=nf_texture_source_hash(texture_pixels,p->width,p->height);if(hash!=cache[i].source_hash)dump_texture_source(p,texture_pixels,hash);if(hash!=cache[i].source_hash&&!upload_texture(&cache[i],p,texture_pixels,hash))return NULL;}
 cache[i].refreshed=draw_serial;
 return &cache[i];
}
static float cross(const NFVertex* a,const NFVertex* b,const NFVertex* c){return (b->x-a->x)*(c->y-a->y)-(b->y-a->y)*(c->x-a->x);}
static void vertex(const NFVertex* v){glTexCoord4f(v->s,v->t,0,v->q);glVertex2f(v->x,v->y);}
static void polygon(const NFPoly* p){
 int ids[32],n=0;float area=0;
 for(unsigned i=0;i<p->count;i++){
  const NFVertex* v=&p->v[i];if(!isfinite(v->x)||!isfinite(v->y)||!isfinite(v->s)||!isfinite(v->t)||!isfinite(v->q)||v->q<=0)return;
  if(n&&fabsf(v->x-p->v[ids[n-1]].x)<0.001f&&fabsf(v->y-p->v[ids[n-1]].y)<0.001f)continue;ids[n++]=i;
 }
 if(n>2&&p->v[ids[0]].x==p->v[ids[n-1]].x&&p->v[ids[0]].y==p->v[ids[n-1]].y)n--;
 for(int i=0;i<n;i++){const NFVertex*a=&p->v[ids[i]],*b=&p->v[ids[(i+1)%n]];area+=a->x*b->y-b->x*a->y;}
 if(fabsf(area)<.01f)return;float sign=area>0?1:-1;
 CachedTexture* entry=texture_for(p);if(!entry)return;trace_texture("polygon",p,entry);glBindTexture(GL_TEXTURE_2D,entry->gl);glBegin(GL_TRIANGLES);unsigned triangles=0;
 while(n>=3){int found=0;
  for(int i=0;i<n;i++){
   int prev=(i+n-1)%n,next=(i+1)%n;const NFVertex *a=&p->v[ids[prev]],*b=&p->v[ids[i]],*c=&p->v[ids[next]];
   float cr=cross(a,b,c)*sign;if(cr<.001f)continue;int inside=0;
   for(int j=0;j<n;j++){if(j==prev||j==i||j==next)continue;const NFVertex*v=&p->v[ids[j]];if(cross(a,b,v)*sign>0.001f&&cross(b,c,v)*sign>0.001f&&cross(c,a,v)*sign>0.001f){inside=1;break;}}
   if(inside)continue;vertex(a);vertex(b);vertex(c);triangles++;memmove(ids+i,ids+i+1,(n-i-1)*sizeof(int));n--;found=1;break;
  }
  if(!found)break;
 }
 glEnd();char event[32];snprintf(event,sizeof(event),"triangles=%u",triangles);trace_texture(event,p,entry);
}

/* Presentation interpolation only: it never changes emulated memory or clocks. */
static NFPoly motion_previous[NF_MAX_POLYS],motion_current[NF_MAX_POLYS];
static int motion_matches[NF_MAX_POLYS],motion_count,motion_enabled=1;
static unsigned motion_version;
static double motion_start,motion_interval=1.0/15.0;
/* Index previous polygons by immutable texture/topology identity so motion
   matching does not compare every polygon against every other polygon. */
#define NF_MOTION_BUCKET_COUNT 8192u
#define NF_MOTION_BUCKET_MASK (NF_MOTION_BUCKET_COUNT-1u)
typedef struct {uint64_t key;unsigned epoch;int head,tail;} MotionBucket;
static MotionBucket motion_buckets[NF_MOTION_BUCKET_COUNT];
static int motion_next[NF_MAX_POLYS];
static unsigned motion_bucket_epoch;
unsigned nf_scene_version(void);
static double motion_now(void){LARGE_INTEGER q,f;QueryPerformanceCounter(&q);QueryPerformanceFrequency(&f);return (double)q.QuadPart/f.QuadPart;}
void nf_gpu_motion(int enabled){motion_enabled=enabled;motion_count=0;motion_start=0;}
void nf_gpu_motion_profile(uint64_t* calls,uint64_t* total_ns,uint64_t* max_ns,uint64_t* candidates,uint64_t* legacy_cost_calls){
 if(calls)*calls=motion_profile_calls;if(total_ns)*total_ns=motion_profile_total_ns;
 if(max_ns)*max_ns=motion_profile_max_ns;if(candidates)*candidates=motion_profile_candidates;
 if(legacy_cost_calls)*legacy_cost_calls=motion_profile_legacy_cost_calls;
}
void nf_gpu_motion_verification(uint64_t* scene_pairs,uint64_t* mismatches){
 if(scene_pairs)*scene_pairs=motion_verify_scene_pairs;if(mismatches)*mismatches=motion_verify_mismatches;
}
int nf_gpu_motion_legacy_forced(void){return motion_legacy_forced;}
static uint64_t motion_key(const NFPoly* p){
 const uint32_t fields[]={p->kind,p->address,p->shade,p->count,p->width,p->height,p->stride};
 uint64_t h=UINT64_C(14695981039346656037);
 for(unsigned i=0;i<sizeof(fields)/sizeof(fields[0]);i++)for(unsigned b=0;b<4;b++){h^=(unsigned char)(fields[i]>>(b*8));h*=UINT64_C(1099511628211);}
 return h?h:1;
}
static int motion_bucket(uint64_t key,unsigned epoch,int create){
 unsigned slot=(unsigned)(key^(key>>32))&NF_MOTION_BUCKET_MASK;
 for(unsigned probes=0;probes<NF_MOTION_BUCKET_COUNT;probes++,slot=(slot+1)&NF_MOTION_BUCKET_MASK){
  MotionBucket* b=&motion_buckets[slot];
  if(b->epoch!=epoch){if(!create)return -1;b->epoch=epoch;b->key=key;b->head=b->tail=-1;return (int)slot;}
  if(b->key==key)return (int)slot;
 }
 return -1;
}
static void motion_profile_finish(LARGE_INTEGER begin){
 if(!motion_profile_enabled)return;LARGE_INTEGER end,f;QueryPerformanceCounter(&end);QueryPerformanceFrequency(&f);
 uint64_t ns=f.QuadPart>0?(uint64_t)((end.QuadPart-begin.QuadPart)*UINT64_C(1000000000)/(uint64_t)f.QuadPart):0;
 motion_profile_calls++;motion_profile_total_ns+=ns;if(ns>motion_profile_max_ns)motion_profile_max_ns=ns;
}
/* Only stable UV topology is safe to interpolate. Screen-column wall strips
   do not identify the same world surface across frames. */
static float match_cost(const NFPoly*a,const NFPoly*b){
 if(a->kind==3||b->kind==3)return 1e20f;
 if(a->kind!=b->kind||a->address!=b->address||a->shade!=b->shade||a->count!=b->count||a->width!=b->width||a->height!=b->height||a->stride!=b->stride)return 1e20f;
 float cost=0;
 for(unsigned j=0;j<a->count;j++){
  const NFVertex*x=&a->v[j],*y=&b->v[j];
  if(!isfinite(x->q)||!isfinite(y->q)||x->q<=0||y->q<=0)return 1e20f;
  float dx=x->x-y->x,dy=x->y-y->y,du=x->s/x->q-y->s/y->q,dv=x->t/x->q-y->t/y->q;
  if(!isfinite(du)||!isfinite(dv)||fabsf(du)>0.00002f||fabsf(dv)>0.00002f)return 1e20f;
  if(fabsf(dx)>45||fabsf(dy)>45||x->q/y->q<.5f||x->q/y->q>2)return 1e20f;
  cost+=dx*dx+dy*dy;
 }
 return cost/a->count;
}
static NFVertex motion_vertex(NFVertex a,NFVertex b,float alpha){
 /* Interpolate reconstructed camera-space coordinates, then project again.
    Linear screen XY plus independent reciprocal depth bends texture mapping. */
 float za=1/a.q,zb=1/b.q,z=za+(zb-za)*alpha;
 NFVertex v;v.q=1/z;
 v.x=(a.x*za+(b.x*zb-a.x*za)*alpha)*v.q;
 v.y=(a.y*za+(b.y*zb-a.y*za)*alpha)*v.q;
 v.s=(a.s*za+(b.s*zb-a.s*za)*alpha)*v.q;
 v.t=(a.t*za+(b.t*zb-a.t*za)*alpha)*v.q;
 return v;
}
static void motion_prepare(const NFPoly* polys,int n,double now){
 LARGE_INTEGER profile_begin={0};if(motion_profile_enabled)QueryPerformanceCounter(&profile_begin);
 unsigned version=nf_scene_version();if(version==motion_version&&motion_count){motion_profile_finish(profile_begin);return;}
 int previous_count=motion_count;memcpy(motion_previous,motion_current,previous_count*sizeof(NFPoly));
 memcpy(motion_current,polys,n*sizeof(NFPoly));motion_count=n;
 unsigned char used[NF_MAX_POLYS]={0};
 unsigned matched_previous_count=0;
 if(motion_legacy_forced){
  for(int i=0;i<n;i++){
   int best=-1,candidates=0;float cost=1600;
   if(motion_profile_enabled)motion_profile_legacy_cost_calls+=(uint64_t)(previous_count-(int)matched_previous_count);
   for(int j=0;j<previous_count;j++)if(!used[j]){if(motion_profile_enabled)motion_profile_candidates++;float candidate=match_cost(&polys[i],&motion_previous[j]);if(candidate<1600)candidates++;if(candidate<cost){best=j;cost=candidate;}}
   if(candidates!=1)best=-1;motion_matches[i]=best;if(best>=0){used[best]=1;matched_previous_count++;}
  }
 }else{
  if(++motion_bucket_epoch==0){memset(motion_buckets,0,sizeof(motion_buckets));motion_bucket_epoch=1;}
  for(int j=0;j<previous_count;j++){
   int slot=motion_bucket(motion_key(&motion_previous[j]),motion_bucket_epoch,1);if(slot<0)continue;
   MotionBucket* b=&motion_buckets[slot];motion_next[j]=-1;
   if(b->tail>=0)motion_next[b->tail]=j;else b->head=j;b->tail=j;
  }
  for(int i=0;i<n;i++){
   int best=-1,candidates=0;float cost=1600;
   if(motion_profile_enabled)motion_profile_legacy_cost_calls+=(uint64_t)(previous_count-(int)matched_previous_count);
   int slot=motion_bucket(motion_key(&polys[i]),motion_bucket_epoch,0);
   for(int j=slot>=0?motion_buckets[slot].head:-1;j>=0;j=motion_next[j])if(!used[j]){if(motion_profile_enabled)motion_profile_candidates++;float candidate=match_cost(&polys[i],&motion_previous[j]);if(candidate<1600)candidates++;if(candidate<cost){best=j;cost=candidate;}}
   if(candidates!=1)best=-1;motion_matches[i]=best;if(best>=0){used[best]=1;matched_previous_count++;}
  }
 }
 /* Optional reference execution checks the indexed lookup against the exact
    pre-optimization scan on the same real scene pair. */
 if(motion_verify_enabled){
  unsigned char legacy_used[NF_MAX_POLYS]={0};
  for(int i=0;i<n;i++){
   int best=-1,candidates=0;float cost=1600;
   for(int j=0;j<previous_count;j++)if(!legacy_used[j]){float candidate=match_cost(&polys[i],&motion_previous[j]);if(candidate<1600)candidates++;if(candidate<cost){best=j;cost=candidate;}}
   if(candidates!=1)best=-1;if(best>=0)legacy_used[best]=1;
   if(best!=motion_matches[i])motion_verify_mismatches++;
  }
  motion_verify_scene_pairs++;
 }
 if(motion_start){double interval=now-motion_start;if(interval>=.025&&interval<=.2)motion_interval=interval;}
 motion_start=now;motion_version=version;motion_profile_finish(profile_begin);
}
void nf_gpu_draw(int w,int h,int native_view){
 draw_serial++;
 unsigned hash=2166136261u;for(int i=0;i<256;i++)hash=(hash^nf_read(0x05000000+i*2,2))*16777619u;
 if(hash!=palette_hash){polygon_cache_clear();palette_hash=hash;}
 glEnable(GL_TEXTURE_2D);glDisable(GL_DEPTH_TEST);glDisable(GL_BLEND);glColor4f(1,1,1,1);
 const uint32_t* frame_pixels=(const uint32_t*)nf_pixels();uint64_t frame_source_hash=(!native_view&&(texture_pack_enabled||ui_overlay_export_enabled))?nf_texture_source_hash(frame_pixels,240,160):0;if(ui_overlay_export_enabled&&!native_view)dump_ui_source(frame_pixels,frame_source_hash,5);glBindTexture(GL_TEXTURE_2D,reference);if(texture_pack_enabled){nf_ui_scale4x(frame_pixels,ui_scale_scratch,ui_scale_output);glTexSubImage2D(GL_TEXTURE_2D,0,0,0,NF_UI_SCALED_WIDTH,NF_UI_SCALED_HEIGHT,GL_RGBA,GL_UNSIGNED_BYTE,ui_scale_output);}else glTexSubImage2D(GL_TEXTURE_2D,0,0,0,240,160,GL_RGBA,GL_UNSIGNED_BYTE,frame_pixels);
 trace_ui_gl_errors("draw-after-reference-upload");
 BindFramebuffer(FB,fbo);glViewport(0,0,3840,2160);glClearColor(0,0,0,1);glClear(GL_COLOR_BUFFER_BIT);glViewport(300,0,3240,2160);projection(240,160);PrewarmedTexture* full_frame=texture_pack_enabled&&!native_view&&frame_source_hash?prewarmed_texture_find(frame_source_hash):NULL;GLuint full_frame_gl=0;if(full_frame&&nf_ui_frame_replacement_matches(frame_source_hash,full_frame->source_hash,full_frame->width,full_frame->height))full_frame_gl=full_frame->gl;else if(texture_pack_enabled&&!native_view&&frame_source_hash)full_frame_gl=ui_frame_replacement_get(frame_source_hash);if(ui_gl_trace&&!native_view)fprintf(ui_gl_trace,"ui-frame\t%u\t%016llx\t%u\n",draw_serial,(unsigned long long)frame_source_hash,(unsigned)full_frame_gl);if(full_frame_gl)quad(full_frame_gl,0);else quad(reference,0);trace_ui_gl_errors("draw-after-menu-quad");
 const NFPoly* polys=nf_scene(&poly_count);
 if(!poly_count)motion_count=0;
 if(native_view && (nf_read(0x04000000,2)&7)==4 && poly_count>0){
  glEnable(GL_ALPHA_TEST);glAlphaFunc(GL_GREATER,0.5f);
  int interpolate=motion_enabled&&nf_read(0x03005f14,4)==5;
  double clock=motion_now();if(interpolate)motion_prepare(polys,poly_count,clock);else motion_count=0;
  float alpha=motion_interval>0?(float)((clock-motion_start)/motion_interval):1;if(alpha<0)alpha=0;if(alpha>1)alpha=1;
  for(int i=0;i<poly_count;i++){
   if(interpolate&&motion_matches[i]>=0){
    NFPoly blended=motion_current[i];const NFPoly* old=&motion_previous[motion_matches[i]];
    for(unsigned j=0;j<blended.count;j++){
     NFVertex* v=&blended.v[j];const NFVertex* a=&old->v[j];
     *v=motion_vertex(*a,*v,alpha);
    }
    polygon(&blended);
   }else polygon(&polys[i]);
  }
  glDisable(GL_ALPHA_TEST);
  nf_overlay(overlay_pixels);uint64_t overlay_source_hash=(texture_pack_enabled||ui_overlay_export_enabled)?nf_texture_source_hash(overlay_pixels,240,160):0;if(ui_overlay_export_enabled)dump_ui_source(overlay_pixels,overlay_source_hash,4);if(layer_audit_enabled){const uint32_t*source=(const uint32_t*)nf_pixels();uint32_t bh=2166136261u;unsigned opaque=0;for(unsigned i=0;i<240u*160u;i++){int foreground=(overlay_pixels[i]>>24)!=0;uint32_t pixel=foreground?0:source[i];if(foreground)opaque++;bh=(bh^pixel)*16777619u;}layer_overlay_hash=hash_pixels(overlay_pixels,240u*160u);layer_background_hash=bh;layer_overlay_pixel_count=opaque;layer_overlay_active=1;}PrewarmedTexture* high_overlay=texture_pack_enabled&&overlay_source_hash?prewarmed_texture_find(overlay_source_hash):NULL;if(high_overlay&&nf_ui_frame_replacement_matches(overlay_source_hash,high_overlay->source_hash,high_overlay->width,high_overlay->height))glBindTexture(GL_TEXTURE_2D,high_overlay->gl);else{glBindTexture(GL_TEXTURE_2D,overlay);if(texture_pack_enabled){nf_ui_scale4x(overlay_pixels,ui_scale_scratch,ui_scale_output);glTexSubImage2D(GL_TEXTURE_2D,0,0,0,NF_UI_SCALED_WIDTH,NF_UI_SCALED_HEIGHT,GL_RGBA,GL_UNSIGNED_BYTE,ui_scale_output);}else glTexSubImage2D(GL_TEXTURE_2D,0,0,0,240,160,GL_RGBA,GL_UNSIGNED_BYTE,overlay_pixels);}
  glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);quad(high_overlay&&nf_ui_frame_replacement_matches(overlay_source_hash,high_overlay->source_hash,high_overlay->width,high_overlay->height)?high_overlay->gl:overlay,0);glDisable(GL_BLEND);
 }
 trace_ui_gl_errors("draw-after-scene");BindFramebuffer(FB,0);glViewport(0,0,w,h);glClear(GL_COLOR_BUFFER_BIT);
 int vw=w,vh=w*2160/3840;if(vh>h){vh=h;vw=h*3840/2160;}glViewport((w-vw)/2,(h-vh)/2,vw,vh);projection(240,160);quad(target,1);trace_ui_gl_errors("draw-after-output-quad");
}
int nf_gpu_capture(const char* path){
 uint8_t* rgb=malloc(3840*2160*3);if(!rgb)return 0;
 BindFramebuffer(FB,fbo);glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(0,0,3840,2160,GL_RGB,GL_UNSIGNED_BYTE,rgb);BindFramebuffer(FB,0);
 FILE*f=fopen(path,"wb");if(!f){free(rgb);return 0;}fprintf(f,"P6\n3840 2160\n255\n");for(int y=2159;y>=0;y--)fwrite(rgb+y*3840*3,3,3840,f);fclose(f);free(rgb);return 1;
}
int nf_gpu_polygon_count(void){return poly_count;}
void nf_gpu_close(void){polygon_cache_clear();prewarmed_textures_clear();ui_frame_replacement_clear();nf_texture_pack_cache_clear();if(texture_pack_trace){fclose(texture_pack_trace);texture_pack_trace=NULL;}if(texture_upload_trace){fclose(texture_upload_trace);texture_upload_trace=NULL;}if(ui_gl_trace){fclose(ui_gl_trace);ui_gl_trace=NULL;}if(fbo)DeleteFramebuffers(1,&fbo);glDeleteTextures(1,&target);glDeleteTextures(1,&reference);glDeleteTextures(1,&overlay);}

unsigned nf_gpu_frame_hash(void){
 static unsigned pixels[1000*600];unsigned hash=2166136261u;
 BindFramebuffer(FB,fbo);glReadPixels(1200,600,1000,600,GL_RGBA,GL_UNSIGNED_BYTE,pixels);BindFramebuffer(FB,0);
 for(unsigned i=0;i<1000*600;i++)hash=(hash^pixels[i])*16777619u;
 return hash;
}
