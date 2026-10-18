#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "texture_pack.h"
#include "ui_scale.h"
#include "ui_gl_texture.h"

typedef struct { const char *root; unsigned loads, uploads, deletes; int fail_upload; } TestContext;
static void check(int ok,const char *what){if(!ok){fprintf(stderr,"FAIL: %s (winerr=%lu glerr=0x%x)\n",what,(unsigned long)GetLastError(),(unsigned)glGetError());ExitProcess(2);}}
static LRESULT CALLBACK test_wndproc(HWND h,UINT m,WPARAM w,LPARAM l){return DefWindowProcA(h,m,w,l);}
static HWND create_gl_window(HDC *dc,HGLRC *rc){
 WNDCLASSA wc={0};wc.style=CS_OWNDC;wc.lpfnWndProc=test_wndproc;wc.hInstance=GetModuleHandleA(NULL);wc.lpszClassName="NfsUiGlCacheTest";
 check(RegisterClassA(&wc)!=0,"register hidden GL test class");
 HWND w=CreateWindowExA(0,wc.lpszClassName,"",WS_POPUP,0,0,32,32,NULL,NULL,wc.hInstance,NULL);check(w!=NULL,"create hidden GL window");
 *dc=GetDC(w);check(*dc!=NULL,"acquire GL DC");
 PIXELFORMATDESCRIPTOR pfd={sizeof(pfd),1,PFD_DRAW_TO_WINDOW|PFD_SUPPORT_OPENGL|PFD_DOUBLEBUFFER,PFD_TYPE_RGBA,32,0,0,0,0,0,0,0,0,0,0,0,0,0,24,8,0,PFD_MAIN_PLANE,0,0,0,0};
 int pf=ChoosePixelFormat(*dc,&pfd);check(pf!=0,"choose GL pixel format");check(SetPixelFormat(*dc,pf,&pfd),"set GL pixel format");
 *rc=wglCreateContext(*dc);check(*rc!=NULL,"create GL context");check(wglMakeCurrent(*dc,*rc),"activate GL context");return w;
}
static void path_join(char *out,size_t cap,const char *base,const char *leaf){size_t a=strlen(base),b=strlen(leaf);check(a+1+b<cap,"path fits MAX_PATH");memcpy(out,base,a);out[a]='\\';memcpy(out+a+1,leaf,b+1);}
static void write32(FILE *f,uint32_t v){uint8_t b[4]={(uint8_t)v,(uint8_t)(v>>8),(uint8_t)(v>>16),(uint8_t)(v>>24)};check(fwrite(b,1,4,f)==4,"write NFGX uint32");}
static void write64(FILE *f,uint64_t v){write32(f,(uint32_t)v);write32(f,(uint32_t)(v>>32));}
static uint64_t make_hash(unsigned salt){uint32_t *src=malloc((size_t)NF_UI_SOURCE_WIDTH*NF_UI_SOURCE_HEIGHT*4);check(src!=NULL,"allocate source frame");for(size_t i=0;i<(size_t)NF_UI_SOURCE_WIDTH*NF_UI_SOURCE_HEIGHT;i++)src[i]=0xff000000u|((uint32_t)(i*2654435761u+salt*2246822519u)&0xffffffu);uint64_t h=nf_texture_source_hash(src,NF_UI_SOURCE_WIDTH,NF_UI_SOURCE_HEIGHT);free(src);return h;}
static void write_entry(const char *pack,uint64_t hash,uint32_t rgba){char name[40],path[MAX_PATH];snprintf(name,sizeof(name),"%016llx.rgba",(unsigned long long)hash);path_join(path,sizeof(path),pack,name);FILE *f=fopen(path,"wb");check(f!=NULL,"create synthetic exact-hash asset");check(fwrite("NFGX",1,4,f)==4,"write NFGX magic");write32(f,1);write32(f,NF_UI_4K_WIDTH);write32(f,NF_UI_4K_HEIGHT);write64(f,hash);uint32_t *row=malloc((size_t)NF_UI_4K_WIDTH*4);check(row!=NULL,"allocate 4K fixture row");for(unsigned x=0;x<NF_UI_4K_WIDTH;x++)row[x]=rgba;for(unsigned y=0;y<NF_UI_4K_HEIGHT;y++)check(fwrite(row,4,NF_UI_4K_WIDTH,f)==NF_UI_4K_WIDTH,"write 4K RGBA row");free(row);check(fclose(f)==0,"close 4K fixture");}
static int load_frame(void *opaque,uint64_t hash,uint32_t **pixels,uint32_t *w,uint32_t *h){TestContext *c=opaque;c->loads++;return nf_texture_pack_load_cached(c->root,hash,NF_UI_SOURCE_WIDTH,NF_UI_SOURCE_HEIGHT,pixels,w,h);}
static int upload_gl(void *opaque,const uint32_t *pixels,uint32_t w,uint32_t h,uint32_t *handle){TestContext *c=opaque;c->uploads++;if(!nf_ui_gl_texture_upload_rgba(pixels,w,h,handle))return 0;if(c->fail_upload){c->fail_upload=0;return 0;}return 1;}
static void delete_gl(void *opaque,uint32_t h){TestContext *c=opaque;if(h){nf_ui_gl_texture_delete(h);c->deletes++;}}
static void verify_pixels(GLuint id,uint32_t expected){GLint w=0,h=0;glBindTexture(GL_TEXTURE_2D,id);glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_WIDTH,&w);glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_HEIGHT,&h);check(w==(GLint)NF_UI_4K_WIDTH&&h==(GLint)NF_UI_4K_HEIGHT,"uploaded texture is 3240x2160");size_t n=(size_t)w*h;uint32_t *out=malloc(n*4);check(out!=NULL,"allocate GL readback");glGetTexImage(GL_TEXTURE_2D,0,GL_RGBA,GL_UNSIGNED_BYTE,out);check(glGetError()==GL_NO_ERROR,"read back 4K GL texture");check(out[0]==expected&&out[n/2]==expected&&out[n-1]==expected,"readback pixels exactly match RGBA asset");free(out);}
int main(void){
 HDC dc=NULL;HGLRC rc=NULL;HWND win=create_gl_window(&dc,&rc);GLint max_texture=0;glGetIntegerv(GL_MAX_TEXTURE_SIZE,&max_texture);check(max_texture>=(GLint)NF_UI_4K_WIDTH,"driver supports 3240px texture width");
 char temp[MAX_PATH],root[MAX_PATH],textures[MAX_PATH],pack[MAX_PATH],marker[MAX_PATH];DWORD n=GetTempPathA(MAX_PATH,temp);check(n>0&&n<MAX_PATH,"get temp path");check(GetTempFileNameA(temp,"nug",0,root)!=0,"allocate temp folder name");DeleteFileA(root);check(CreateDirectoryA(root,NULL),"create test root");path_join(textures,sizeof(textures),root,"textures");path_join(pack,sizeof(pack),textures,"4k");check(CreateDirectoryA(textures,NULL)&&CreateDirectoryA(pack,NULL),"create pack folders");path_join(marker,sizeof(marker),pack,"pack.ready");FILE *f=fopen(marker,"wb");check(f!=NULL,"create pack.ready");static const char ready[]="NFSUG-UPSCALED-TEXTURES 1\ncomplete=1\n";check(fwrite(ready,1,sizeof(ready)-1,f)==sizeof(ready)-1,"write ready marker");check(fclose(f)==0,"close marker");
 uint64_t a=make_hash(1),b=make_hash(2);check(a&&b&&a!=b,"derive distinct source hashes");write_entry(pack,a,0xff31a5c2u);write_entry(pack,b,0xff43b6d7u);check(nf_texture_pack_cache_prepare(root),"index synthetic replacements");
 TestContext ctx={root,0,0,0,0};NFUiFrameCache cache={0};uint32_t ta=nf_ui_frame_cache_get(&cache,a,NF_UI_FRAME_CACHE_MAX_BYTES,load_frame,upload_gl,delete_gl,&ctx);check(ta!=0,"load and upload first 4K UI frame");verify_pixels(ta,0xff31a5c2u);check(ctx.loads==1&&ctx.uploads==1&&ctx.deletes==0,"first request loads/uploads once");
 check(nf_ui_frame_cache_get(&cache,a,NF_UI_FRAME_CACHE_MAX_BYTES,load_frame,upload_gl,delete_gl,&ctx)==ta,"same source returns resident texture");check(ctx.loads==1&&ctx.uploads==1&&ctx.deletes==0,"same source causes no read or upload");
 ctx.fail_upload=1;check(nf_ui_frame_cache_get(&cache,b,NF_UI_FRAME_CACHE_MAX_BYTES,load_frame,upload_gl,delete_gl,&ctx)==0,"failed candidate returns safe fallback signal");check(glIsTexture(ta)&&ctx.deletes==1,"failed new GL texture is deleted while old texture survives");verify_pixels(ta,0xff31a5c2u);
 uint32_t tb=nf_ui_frame_cache_get(&cache,b,NF_UI_FRAME_CACHE_MAX_BYTES,load_frame,upload_gl,delete_gl,&ctx);check(tb&&tb!=ta,"replacement hash commits a new GL texture");check(!glIsTexture(ta)&&ctx.loads==3&&ctx.uploads==3&&ctx.deletes==2,"replacement retires old texture only after upload succeeds");verify_pixels(tb,0xff43b6d7u);
 nf_ui_frame_cache_clear(&cache,delete_gl,&ctx);check(!glIsTexture(tb)&&ctx.deletes==3,"clear releases final resident texture");
 nf_texture_pack_cache_clear();DeleteFileA(marker);RemoveDirectoryA(pack);RemoveDirectoryA(textures);RemoveDirectoryA(root);wglMakeCurrent(NULL,NULL);wglDeleteContext(rc);ReleaseDC(win,dc);DestroyWindow(win);UnregisterClassA("NfsUiGlCacheTest",GetModuleHandleA(NULL));
 puts("PASS: hidden WGL 4K exact-hash upload/readback, reuse, replacement, failed-upload cleanup, and cache clear");return 0;
}
