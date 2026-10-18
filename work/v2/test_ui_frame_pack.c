#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "texture_pack.h"
#include "ui_scale.h"

static void require(int ok,const char *label) {
    if(!ok){fprintf(stderr,"FAIL: %s (error %lu)\n",label,(unsigned long)GetLastError());ExitProcess(1);}
}
static void path_join(char *out,size_t cap,const char *base,const char *leaf) {
    size_t a=strlen(base),b=strlen(leaf);
    require(a+1+b<cap,"test path length");
    memcpy(out,base,a);out[a]='\\';memcpy(out+a+1,leaf,b+1);
}
static void write_u32(FILE *f,uint32_t v) {
    unsigned char b[4]={(unsigned char)v,(unsigned char)(v>>8),(unsigned char)(v>>16),(unsigned char)(v>>24)};
    require(fwrite(b,1,4,f)==4,"header uint32 write");
}
static void write_u64(FILE *f,uint64_t v) {
    write_u32(f,(uint32_t)v);write_u32(f,(uint32_t)(v>>32));
}
int main(void) {
    char temp[MAX_PATH],root[MAX_PATH],textures[MAX_PATH],pack[MAX_PATH],marker[MAX_PATH],asset[MAX_PATH];
    DWORD n=GetTempPathA(MAX_PATH,temp);require(n>0&&n<MAX_PATH,"temp path");
    require(GetTempFileNameA(temp,"nfu",0,root)!=0,"temp name");DeleteFileA(root);
    require(CreateDirectoryA(root,NULL),"temp root");
    path_join(textures,sizeof(textures),root,"textures");
    path_join(pack,sizeof(pack),textures,"4k");
    require(CreateDirectoryA(textures,NULL)&&CreateDirectoryA(pack,NULL),"texture pack directories");
    path_join(marker,sizeof(marker),pack,"pack.ready");
    FILE *f=fopen(marker,"wb");require(f!=NULL,"ready marker open");
    static const char ready[]="NFSUG-UPSCALED-TEXTURES 1\ncomplete=1\n";
    require(fwrite(ready,1,sizeof(ready)-1,f)==sizeof(ready)-1,"ready marker write");fclose(f);

    uint32_t *source=(uint32_t*)malloc((size_t)NF_UI_SOURCE_WIDTH*NF_UI_SOURCE_HEIGHT*sizeof(*source));
    require(source!=NULL,"source menu frame allocation");
    for(size_t i=0;i<(size_t)NF_UI_SOURCE_WIDTH*NF_UI_SOURCE_HEIGHT;i++)
        source[i]=0xFF000000u|(uint32_t)(i*2654435761u&0x00FFFFFFu);
    uint64_t hash=nf_texture_source_hash(source,NF_UI_SOURCE_WIDTH,NF_UI_SOURCE_HEIGHT);
    free(source);require(hash!=0,"source menu frame hash");

    uint32_t width=NF_UI_4K_WIDTH,height=NF_UI_4K_HEIGHT;
    uint64_t payload=(uint64_t)width*height*sizeof(uint32_t);
    char filename[32];snprintf(filename,sizeof(filename),"%016llx.rgba",(unsigned long long)hash);
    path_join(asset,sizeof(asset),pack,filename);
    f=fopen(asset,"wb");require(f!=NULL,"synthetic menu replacement open");
    require(fwrite("NFGX",1,4,f)==4,"replacement magic write");
    write_u32(f,1);write_u32(f,width);write_u32(f,height);write_u64(f,hash);
    uint32_t *row=(uint32_t*)malloc((size_t)width*sizeof(*row));
    require(row!=NULL,"replacement row allocation");
    for(uint32_t x=0;x<width;x++)row[x]=0xFF31A5C2u;
    for(uint32_t y=0;y<height;y++)require(fwrite(row,sizeof(*row),width,f)==width,"replacement row write");
    free(row);require(fclose(f)==0,"replacement close");

    require(nf_texture_pack_cache_prepare(root),"index source frame before lazy load");
    uint32_t *loaded=NULL,loaded_width=0,loaded_height=0;
    require(nf_texture_pack_load_cached(root,hash,NF_UI_SOURCE_WIDTH,NF_UI_SOURCE_HEIGHT,
                                        &loaded,&loaded_width,&loaded_height),
            "lazy loader resolves full-resolution menu frame without bulk preloading");
    require(nf_ui_frame_replacement_matches(hash,hash,loaded_width,loaded_height),
            "loaded frame passes exact identity and 3240x2160 coverage check");
    require(nf_ui_frame_payload_fits_budget(loaded_width,loaded_height,0,NF_UI_FRAME_CACHE_MAX_BYTES),
            "loaded frame fits bounded lazy GPU slot");
    require(loaded_width==width&&loaded_height==height&&loaded[0]==0xFF31A5C2u&&
            loaded[(size_t)width*height-1]==0xFF31A5C2u,
            "lazy file path returns exact dimensions and RGBA payload");
    free(loaded);loaded=NULL;
    require(DeleteFileA(asset),"remove lazy source asset");
    require(!nf_texture_pack_load_cached(root,hash,NF_UI_SOURCE_WIDTH,NF_UI_SOURCE_HEIGHT,
                                         &loaded,&loaded_width,&loaded_height),
            "missing lazy menu asset falls back safely");
    require(loaded==NULL&&loaded_width==NF_UI_SOURCE_WIDTH&&loaded_height==NF_UI_SOURCE_HEIGHT,
            "missing menu asset preserves source-frame fallback dimensions");
    nf_texture_pack_cache_clear();
    DeleteFileA(marker);RemoveDirectoryA(pack);RemoveDirectoryA(textures);RemoveDirectoryA(root);
    puts("PASS: exact-hash 3240x2160 menu asset loads lazily within budget and missing asset falls back");
    return 0;
}