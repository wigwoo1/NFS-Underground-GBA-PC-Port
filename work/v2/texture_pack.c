#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "texture_pack.h"

#define NF_TEXTURE_PACK_MAX_DIM 4096u
#define NF_TEXTURE_PACK_MAX_PIXELS (4096u * 4096u)
#define NF_TEXTURE_PACK_HEADER_BYTES 24u
#define NF_TEXTURE_PACK_MAX_INDEX_ENTRIES 1048576u
#define NF_TEXTURE_PACK_MAX_PRELOAD_BYTES (UINT64_C(1024) * 1024u * 1024u)

static char indexed_root[MAX_PATH];
static uint64_t *indexed_hashes;
static uint32_t **indexed_pixels,*indexed_widths,*indexed_heights;
static size_t indexed_count,indexed_capacity;
static uint64_t indexed_payload_bytes;
static int indexed_ready,indexed_attempted,preload_attempted,preload_complete;

int nf_texture_payload_fits_budget(uint32_t width, uint32_t height,
                                    uint64_t used_bytes, uint64_t max_bytes) {
    if (!width || !height || used_bytes > max_bytes) return 0;
    uint64_t pixels = (uint64_t)width * height;
    if (pixels > UINT64_MAX / sizeof(uint32_t)) return 0;
    uint64_t bytes = pixels * sizeof(uint32_t);
    return bytes <= max_bytes - used_bytes;
}

static uint32_t read_u32le(const unsigned char *p) {
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static uint64_t read_u64le(const unsigned char *p) {
    return (uint64_t)read_u32le(p) | (uint64_t)read_u32le(p + 4) << 32;
}

static void hash_byte(uint64_t *hash, unsigned char value) {
    *hash ^= value;
    *hash *= UINT64_C(1099511628211);
}

uint64_t nf_texture_source_hash(const uint32_t *rgba, uint32_t width, uint32_t height) {
    if (!rgba || !width || !height || (uint64_t)width * height > NF_TEXTURE_PACK_MAX_PIXELS)
        return 0;
    uint64_t hash = UINT64_C(14695981039346656037);
    for (unsigned i = 0; i < 4; ++i) hash_byte(&hash, (unsigned char)(width >> (i * 8)));
    for (unsigned i = 0; i < 4; ++i) hash_byte(&hash, (unsigned char)(height >> (i * 8)));
    const unsigned char *bytes = (const unsigned char *)rgba;
    size_t count = (size_t)width * height * sizeof(*rgba);
    for (size_t i = 0; i < count; ++i) hash_byte(&hash, bytes[i]);
    return hash;
}

static int pack_path(char *out, size_t cap, const char *exe_dir, const char *tail) {
    if (!out || !cap || !exe_dir || !*exe_dir || !tail) return 0;
    int n = snprintf(out, cap, "%s\\textures\\4k\\%s", exe_dir, tail);
    return n > 0 && (size_t)n < cap;
}

int nf_texture_pack_ready(const char *exe_dir) {
    char path[MAX_PATH];
    if (!pack_path(path, sizeof(path), exe_dir, "pack.ready")) return 0;
    FILE *file = fopen(path, "rb");
    if (!file) return 0;
    static const char marker[] = "NFSUG-UPSCALED-TEXTURES 1\ncomplete=1\n";
    char contents[sizeof(marker)];
    size_t n = fread(contents, 1, sizeof(contents), file);
    int extra = fgetc(file);
    fclose(file);
    return n == sizeof(marker) - 1 && extra == EOF &&
           memcmp(contents, marker, sizeof(marker) - 1) == 0;
}

int nf_texture_pack_preference_load(const char *settings_path) {
    if (!settings_path || !*settings_path) return 0;
    char value[32];
    GetPrivateProfileStringA("Graphics", "TexturePack", "original",
                             value, sizeof(value), settings_path);
    return _stricmp(value, "upscaled") == 0;
}

int nf_texture_pack_preference_save(const char *settings_path, int upscaled) {
    if (!settings_path || !*settings_path) return 0;
    return WritePrivateProfileStringA("Graphics", "TexturePack",
                                      upscaled ? "upscaled" : "original",
                                      settings_path) != 0;
}

static int texture_pack_load_file(const char *exe_dir, uint64_t source_hash,
                                  uint32_t source_width, uint32_t source_height,
                                  uint64_t used_bytes, uint64_t max_bytes,
                                  uint32_t **rgba, uint32_t *width, uint32_t *height) {
    char filename[32], path[MAX_PATH];
    snprintf(filename, sizeof(filename), "%016llx.rgba", (unsigned long long)source_hash);
    if (!pack_path(path, sizeof(path), exe_dir, filename)) return 0;
    FILE *file = fopen(path, "rb");
    if (!file) return 0;

    unsigned char header[NF_TEXTURE_PACK_HEADER_BYTES];
    int ok = fread(header, 1, sizeof(header), file) == sizeof(header);
    uint32_t version = ok ? read_u32le(header + 4) : 0;
    uint32_t w = ok ? read_u32le(header + 8) : 0;
    uint32_t h = ok ? read_u32le(header + 12) : 0;
    uint64_t hash = ok ? read_u64le(header + 16) : 0;
    uint64_t pixels = (uint64_t)w * h;
    uint64_t payload = pixels * sizeof(uint32_t);
    if (!ok || memcmp(header, "NFGX", 4) || version != 1 || hash != source_hash ||
        w < source_width || h < source_height || w > NF_TEXTURE_PACK_MAX_DIM ||
        h > NF_TEXTURE_PACK_MAX_DIM || !pixels || pixels > NF_TEXTURE_PACK_MAX_PIXELS ||
        payload > SIZE_MAX || !nf_texture_payload_fits_budget(w,h,used_bytes,max_bytes)) {
        fclose(file);
        return 0;
    }

    long start = ftell(file);
    if (start < 0 || fseek(file, 0, SEEK_END) != 0) {
        fclose(file);
        return 0;
    }
    long end = ftell(file);
    if (end < start || (uint64_t)(end - start) != payload || fseek(file, start, SEEK_SET) != 0) {
        fclose(file);
        return 0;
    }

    uint32_t *image = (uint32_t *)malloc((size_t)payload);
    if (!image) {
        fclose(file);
        return 0;
    }
    if (fread(image, 1, (size_t)payload, file) != (size_t)payload || fgetc(file) != EOF) {
        free(image);
        fclose(file);
        return 0;
    }
    fclose(file);
    *rgba = image;
    *width = w;
    *height = h;
    return 1;
}

static int parse_hash_filename(const char *name,uint64_t *hash) {
    if(!name||strlen(name)!=21||memcmp(name+16,".rgba",5))return 0;
    uint64_t value=0;
    for(unsigned i=0;i<16;i++){
        unsigned char c=(unsigned char)name[i];unsigned digit;
        if(c>='0'&&c<='9')digit=(unsigned)(c-'0');
        else if(c>='a'&&c<='f')digit=(unsigned)(c-'a'+10);
        else if(c>='A'&&c<='F')digit=(unsigned)(c-'A'+10);
        else return 0;
        value=(value<<4)|digit;
    }
    *hash=value;return 1;
}

static int compare_hashes(const void *left,const void *right) {
    uint64_t a=*(const uint64_t*)left,b=*(const uint64_t*)right;
    return a<b?-1:a>b?1:0;
}

void nf_texture_pack_cache_clear(void) {
    if(indexed_pixels)for(size_t i=0;i<indexed_count;i++)free(indexed_pixels[i]);
    free(indexed_pixels);free(indexed_widths);free(indexed_heights);
    indexed_pixels=NULL;indexed_widths=indexed_heights=NULL;indexed_payload_bytes=0;
    free(indexed_hashes);indexed_hashes=NULL;indexed_count=indexed_capacity=0;
    indexed_root[0]=0;indexed_ready=indexed_attempted=preload_attempted=preload_complete=0;
}

static int append_index_hash(uint64_t hash) {
    if(indexed_count>=NF_TEXTURE_PACK_MAX_INDEX_ENTRIES)return 0;
    if(indexed_count==indexed_capacity){
        size_t next=indexed_capacity?indexed_capacity*2:64;
        if(next>NF_TEXTURE_PACK_MAX_INDEX_ENTRIES)next=NF_TEXTURE_PACK_MAX_INDEX_ENTRIES;
        uint64_t *grown=(uint64_t*)realloc(indexed_hashes,next*sizeof(*grown));
        if(!grown)return 0;
        indexed_hashes=grown;indexed_capacity=next;
    }
    indexed_hashes[indexed_count++]=hash;return 1;
}

int nf_texture_pack_cache_prepare(const char *exe_dir) {
    if(!exe_dir||!*exe_dir||strlen(exe_dir)>=sizeof(indexed_root))return 0;
    if(indexed_attempted&&!_stricmp(indexed_root,exe_dir))return indexed_ready;
    nf_texture_pack_cache_clear();
    if(!nf_texture_pack_ready(exe_dir))return 0;
    strcpy(indexed_root,exe_dir);indexed_attempted=1;
    char pattern[MAX_PATH];
    if(!pack_path(pattern,sizeof(pattern),exe_dir,"*.rgba"))return 0;
    WIN32_FIND_DATAA found;HANDLE search=FindFirstFileA(pattern,&found);
    if(search==INVALID_HANDLE_VALUE){indexed_ready=0;return 0;}
    int ok=1;
    do{
        uint64_t hash;
        if(!(found.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY)&&parse_hash_filename(found.cFileName,&hash)&&!append_index_hash(hash)){ok=0;break;}
    }while(FindNextFileA(search,&found));
    DWORD search_error=GetLastError();FindClose(search);
    if(search_error!=ERROR_NO_MORE_FILES)ok=0;
    if(!ok){nf_texture_pack_cache_clear();return 0;}
    qsort(indexed_hashes,indexed_count,sizeof(*indexed_hashes),compare_hashes);
    size_t unique=0;
    for(size_t i=0;i<indexed_count;i++)if(!unique||indexed_hashes[i]!=indexed_hashes[unique-1])indexed_hashes[unique++]=indexed_hashes[i];
    indexed_count=unique;indexed_ready=1;return 1;
}

int nf_texture_pack_cache_preload(const char *exe_dir) {
    if(!nf_texture_pack_cache_prepare(exe_dir))return 0;
    if(preload_attempted)return preload_complete;
    preload_attempted=1;
    if(!indexed_count)return 0;
    indexed_pixels=(uint32_t**)calloc(indexed_count,sizeof(*indexed_pixels));
    indexed_widths=(uint32_t*)calloc(indexed_count,sizeof(*indexed_widths));
    indexed_heights=(uint32_t*)calloc(indexed_count,sizeof(*indexed_heights));
    if(!indexed_pixels||!indexed_widths||!indexed_heights){
        free(indexed_pixels);free(indexed_widths);free(indexed_heights);
        indexed_pixels=NULL;indexed_widths=indexed_heights=NULL;return 0;
    }
    int complete=1;
    for(size_t i=0;i<indexed_count;i++){
        uint32_t *pixels=NULL,width=0,height=0;
        if(!texture_pack_load_file(exe_dir,indexed_hashes[i],1,1,indexed_payload_bytes,
                                   NF_TEXTURE_PACK_MAX_PRELOAD_BYTES,&pixels,&width,&height)){
            complete=0;continue;
        }
        uint64_t bytes=(uint64_t)width*height*sizeof(*pixels);
        indexed_pixels[i]=pixels;indexed_widths[i]=width;indexed_heights[i]=height;indexed_payload_bytes+=bytes;
    }
    preload_complete=complete;return preload_complete;
}

size_t nf_texture_pack_cache_index_count(void) {
    return indexed_ready?indexed_count:0;
}

int nf_texture_pack_cache_preloaded_at(size_t index,uint64_t *source_hash,
                                       uint32_t *width,uint32_t *height,
                                       const uint32_t **rgba) {
    if(source_hash)*source_hash=0;
    if(width)*width=0;
    if(height)*height=0;
    if(rgba)*rgba=NULL;
    if(!source_hash||!width||!height||!rgba||!indexed_ready||
       !indexed_pixels||index>=indexed_count||!indexed_pixels[index]||
       !indexed_widths[index]||!indexed_heights[index])return 0;
    *source_hash=indexed_hashes[index];
    *width=indexed_widths[index];
    *height=indexed_heights[index];
    *rgba=indexed_pixels[index];
    return 1;
}

static int indexed_contains(uint64_t hash) {
    return indexed_ready&&bsearch(&hash,indexed_hashes,indexed_count,sizeof(*indexed_hashes),compare_hashes)!=NULL;
}

static size_t indexed_position(uint64_t hash) {
    if(!indexed_ready)return SIZE_MAX;
    uint64_t *found=(uint64_t*)bsearch(&hash,indexed_hashes,indexed_count,sizeof(*indexed_hashes),compare_hashes);
    return found?(size_t)(found-indexed_hashes):SIZE_MAX;
}

int nf_texture_pack_load_cached(const char *exe_dir,uint64_t source_hash,
                                uint32_t source_width,uint32_t source_height,
                                uint32_t **rgba,uint32_t *width,uint32_t *height) {
    if(rgba)*rgba=NULL;
    if(width)*width=source_width;
    if(height)*height=source_height;
    if(!rgba||!width||!height||!source_hash||!source_width||!source_height)return 0;
    if(!nf_texture_pack_cache_prepare(exe_dir)||!indexed_contains(source_hash))return 0;
    size_t index=indexed_position(source_hash);
    if(index!=SIZE_MAX&&indexed_pixels&&indexed_pixels[index]&&
       indexed_widths[index]>=source_width&&indexed_heights[index]>=source_height){
        uint64_t bytes=(uint64_t)indexed_widths[index]*indexed_heights[index]*sizeof(uint32_t);
        if(bytes>SIZE_MAX)return 0;
        uint32_t *copy=(uint32_t*)malloc((size_t)bytes);if(!copy)return 0;
        memcpy(copy,indexed_pixels[index],(size_t)bytes);
        *rgba=copy;*width=indexed_widths[index];*height=indexed_heights[index];return 1;
    }
    return texture_pack_load_file(exe_dir,source_hash,source_width,source_height,0,UINT64_MAX,rgba,width,height);
}

int nf_texture_pack_load(const char *exe_dir, uint64_t source_hash,
                         uint32_t source_width, uint32_t source_height,
                         uint32_t **rgba, uint32_t *width, uint32_t *height) {
    if (rgba) *rgba = NULL;
    if (width) *width = source_width;
    if (height) *height = source_height;
    if (!rgba || !width || !height || !source_hash || !source_width || !source_height ||
        !nf_texture_pack_ready(exe_dir)) return 0;
    return texture_pack_load_file(exe_dir,source_hash,source_width,source_height,0,UINT64_MAX,rgba,width,height);
}
