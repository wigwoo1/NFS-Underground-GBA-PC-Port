#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "texture_pack.h"

static void write_u32(FILE *f, uint32_t v) {
    unsigned char b[4]={(unsigned char)v,(unsigned char)(v>>8),(unsigned char)(v>>16),(unsigned char)(v>>24)};
    assert(fwrite(b,1,4,f)==4);
}
static void write_u64(FILE *f, uint64_t v) {
    write_u32(f,(uint32_t)v);write_u32(f,(uint32_t)(v>>32));
}
static void require(int ok,const char *label) {
    if(!ok){fprintf(stderr,"FAIL: %s (error %lu)\n",label,(unsigned long)GetLastError());ExitProcess(1);}
}
static void path_join(char *out,size_t cap,const char *base,const char *leaf) {
    size_t a=strlen(base),b=strlen(leaf);
    require(a+1+b<cap,"test path length");
    memcpy(out,base,a);out[a]='\\';memcpy(out+a+1,leaf,b+1);
}

int main(void) {
    const uint64_t one_gib = UINT64_C(1024) * 1024u * 1024u;
    const uint64_t four_k_square_bytes = UINT64_C(4096) * 4096u * sizeof(uint32_t);
    require(nf_texture_payload_fits_budget(4096,4096,0,one_gib),"4K RGBA payload fits empty 1-GiB budget");
    require(nf_texture_payload_fits_budget(1,1,one_gib-4,one_gib),"payload exactly fills remaining budget");
    require(!nf_texture_payload_fits_budget(1,1,one_gib-3,one_gib),"payload exceeding budget by one byte is rejected");
    require(!nf_texture_payload_fits_budget(0,1,0,one_gib),"zero width is rejected");
    require(!nf_texture_payload_fits_budget(1,0,0,one_gib),"zero height is rejected");
    require(!nf_texture_payload_fits_budget(1,1,one_gib+1,one_gib),"used bytes above cap is rejected");
    require(!nf_texture_payload_fits_budget(UINT32_MAX,UINT32_MAX,0,UINT64_MAX),"RGBA byte multiplication overflow is rejected");
    require(four_k_square_bytes == UINT64_C(67108864),"4K RGBA byte count is 64 MiB");
    char temp[MAX_PATH],root[MAX_PATH],textures[MAX_PATH],pack[MAX_PATH],marker[MAX_PATH],asset[MAX_PATH],settings[MAX_PATH];
    DWORD n=GetTempPathA(MAX_PATH,temp);require(n>0&&n<MAX_PATH,"temp path");
    require(GetTempFileNameA(temp,"nfp",0,root)!=0,"temp name");DeleteFileA(root);
    require(CreateDirectoryA(root,NULL),"temp root");
    path_join(settings,sizeof(settings),root,"settings.ini");
    require(nf_texture_pack_preference_load(settings)==0,"missing preference defaults to original");
    require(nf_texture_pack_preference_save(settings,1),"persist upscaled preference");
    require(nf_texture_pack_preference_load(settings)==1,"reload upscaled preference");
    require(nf_texture_pack_preference_save(settings,0),"persist original preference");
    require(nf_texture_pack_preference_load(settings)==0,"reload original preference");
    path_join(textures,sizeof(textures),root,"textures");
    path_join(pack,sizeof(pack),textures,"4k");
    require(CreateDirectoryA(textures,NULL),"textures directory");require(CreateDirectoryA(pack,NULL),"4k directory");
    require(!nf_texture_pack_ready(root),"incomplete pack must not be available");

    path_join(marker,sizeof(marker),pack,"pack.ready");
    FILE *f=fopen(marker,"wb");require(f!=NULL,"marker open");
    static const char ready[]="NFSUG-UPSCALED-TEXTURES 1\ncomplete=1\n";
    require(fwrite(ready,1,sizeof(ready)-1,f)==sizeof(ready)-1,"marker write");fclose(f);
    require(nf_texture_pack_ready(root),"complete marker recognized");

    const uint32_t source[4]={0xFF030201u,0xFF060504u,0xFF090807u,0xFF0C0B0Au};
    const uint32_t replacement[16]={0xFF010203u,0xFF040506u,0xFF070809u,0xFF0A0B0Cu,
        0xFF0D0E0Fu,0xFF101112u,0xFF131415u,0xFF161718u,
        0xFF191A1Bu,0xFF1C1D1Eu,0xFF1F2021u,0xFF222324u,
        0xFF252627u,0xFF28292Au,0xFF2B2C2Du,0xFF2E2F30u};
    uint64_t hash=nf_texture_source_hash(source,2,2);require(hash!=0,"stable source hash");
    uint32_t *loaded=NULL,width=0,height=0;
    require(!nf_texture_pack_load(root,hash,2,2,&loaded,&width,&height),"missing asset rejected");
    require(loaded==NULL&&width==2&&height==2,"missing asset preserves original fallback dimensions");
    char filename[32];snprintf(filename,sizeof(filename),"%016llx.rgba",(unsigned long long)hash);
    path_join(asset,sizeof(asset),pack,filename);
    f=fopen(asset,"wb");require(f!=NULL,"asset open");
    require(fwrite("NFGX",1,4,f)==4,"magic write");write_u32(f,1);write_u32(f,4);write_u32(f,4);write_u64(f,hash);
    require(fwrite(replacement,sizeof(uint32_t),16,f)==16,"pixel write");fclose(f);
    require(nf_texture_pack_cache_prepare(root),"ready pack index prepared from existing asset filenames");
    require(nf_texture_pack_cache_preload(root),"valid replacement payload preloaded before rendering");
    require(nf_texture_pack_load_cached(root,hash^1u,2,2,&loaded,&width,&height)==0,"indexed lookup skips missing source hash");
    require(loaded==NULL&&width==2&&height==2,"indexed miss preserves original fallback dimensions");
    require(DeleteFileA(asset),"remove pack file after successful preload");
    require(nf_texture_pack_load_cached(root,hash,2,2,&loaded,&width,&height),"indexed replacement loads");
    require(width==4&&height==4&&memcmp(loaded,replacement,sizeof(replacement))==0,"preloaded dimensions and RGBA bytes survive file removal");free(loaded);
    nf_texture_pack_cache_clear();
    f=fopen(asset,"wb");require(f!=NULL,"restore asset after preload-cache reset");
    require(fwrite("NFGX",1,4,f)==4,"restored magic write");write_u32(f,1);write_u32(f,4);write_u32(f,4);write_u64(f,hash);
    require(fwrite(replacement,sizeof(uint32_t),16,f)==16,"restored pixel write");fclose(f);
    require(nf_texture_pack_load_cached(root,hash,2,2,&loaded,&width,&height),"cache rebuilds after clear");
    require(width==4&&height==4&&memcmp(loaded,replacement,sizeof(replacement))==0,"rebuilt index preserves replacement payload");free(loaded);
    nf_texture_pack_cache_clear();
    require(nf_texture_pack_load(root,hash,2,2,&loaded,&width,&height),"valid replacement loads");
    require(width==4&&height==4&&memcmp(loaded,replacement,sizeof(replacement))==0,"dimensions and RGBA bytes preserved");free(loaded);
    require(!nf_texture_pack_load(root,hash,5,2,&loaded,&width,&height),"undersized replacement rejected");
    require(loaded==NULL&&width==5&&height==2,"undersized replacement preserves source fallback dimensions");
    require(!nf_texture_pack_load(root,hash^1u,2,2,&loaded,&width,&height),"wrong source identity rejected" );
    require(loaded==NULL&&width==2&&height==2,"wrong source identity preserves fallback dimensions");

    f=fopen(asset,"ab");require(f!=NULL,"append malformed byte");fputc(0,f);fclose(f);
    require(!nf_texture_pack_load(root,hash,2,2,&loaded,&width,&height),"trailing bytes rejected" );
    require(loaded==NULL&&width==2&&height==2,"invalid payload preserves fallback dimensions");
    DeleteFileA(asset);DeleteFileA(marker);DeleteFileA(settings);RemoveDirectoryA(pack);RemoveDirectoryA(textures);RemoveDirectoryA(root);
    puts("PASS: preference round trip, pack readiness, source identity, dimensions, exact payload, malformed and missing assets");
    return 0;
}
