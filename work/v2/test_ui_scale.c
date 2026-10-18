#include "ui_scale.h"
#include <stdio.h>
#include <stdlib.h>

static uint32_t source[NF_UI_SOURCE_WIDTH * NF_UI_SOURCE_HEIGHT];
static uint32_t scratch[NF_UI_SOURCE_WIDTH * 2 * NF_UI_SOURCE_HEIGHT * 2];
static uint32_t output[NF_UI_SCALED_WIDTH * NF_UI_SCALED_HEIGHT];

static void require(int condition, const char *message) {
    if (!condition) {
        fprintf(stderr, "FAIL: %s\n", message);
        exit(1);
    }
}

static uint32_t pixel(unsigned x, unsigned y) {
    return output[y * NF_UI_SCALED_WIDTH + x];
}

typedef struct {
    unsigned loads, uploads, deletes;
    uint64_t failed_load_hash, failed_upload_hash, undersized_hash, loaded_hash;
    uint32_t next_handle, deleted[8];
} MockUiCache;

static int mock_ui_load(void *context,uint64_t hash,uint32_t **pixels,uint32_t *width,uint32_t *height) {
    MockUiCache *mock=(MockUiCache*)context;
    mock->loads++;mock->loaded_hash=hash;*pixels=(uint32_t*)malloc(sizeof(uint32_t));
    if(!*pixels)return 0;
    **pixels=0xFF123456u;*width=NF_UI_4K_WIDTH;*height=NF_UI_4K_HEIGHT;
    if(hash==mock->undersized_hash)*width=NF_UI_4K_WIDTH-1;
    return hash!=mock->failed_load_hash;
}
static int mock_ui_upload(void *context,const uint32_t *pixels,uint32_t width,uint32_t height,uint32_t *handle) {
    MockUiCache *mock=(MockUiCache*)context;
    mock->uploads++;*handle=++mock->next_handle;
    return pixels&&width>=NF_UI_4K_WIDTH&&height>=NF_UI_4K_HEIGHT&&
           mock->loaded_hash!=mock->failed_upload_hash;
}
static void mock_ui_delete(void *context,uint32_t handle) {
    MockUiCache *mock=(MockUiCache*)context;
    if(mock->deletes<8)mock->deleted[mock->deletes]=handle;
    mock->deletes++;
}

int main(void) {
    require(nf_ui_frame_replacement_matches(0x1234u, 0x1234u, NF_UI_4K_WIDTH, NF_UI_4K_HEIGHT),
            "exact source UI frame selects a full 4K viewport replacement");
    require(!nf_ui_frame_replacement_matches(0x1234u, 0x1235u, NF_UI_4K_WIDTH, NF_UI_4K_HEIGHT),
            "UI replacement requires the exact source frame hash");
    require(!nf_ui_frame_replacement_matches(0x1234u, 0x1234u, NF_UI_4K_WIDTH - 1, NF_UI_4K_HEIGHT),
            "undersized UI replacement falls back to the source scaler");
    require(!nf_ui_frame_replacement_matches(0x1234u, 0x1234u, NF_UI_SCALED_WIDTH, NF_UI_SCALED_HEIGHT),
            "4x UI scaling alone is not accepted as a 4K replacement");
    require(!nf_ui_frame_replacement_matches(0, 0, NF_UI_4K_WIDTH, NF_UI_4K_HEIGHT),
            "empty source identity never selects a UI replacement");
    const uint64_t ui_cache_limit = NF_UI_FRAME_CACHE_MAX_BYTES;
    require(nf_ui_frame_payload_fits_budget(NF_UI_4K_WIDTH, NF_UI_4K_HEIGHT, 0, ui_cache_limit),
            "complete 3240x2160 menu replacement fits the lazy one-frame cache");
    require(nf_ui_frame_payload_fits_budget(4096, 4096, 0, ui_cache_limit),
            "maximum supported texture dimensions fit the bounded UI cache");
    require(!nf_ui_frame_payload_fits_budget(4096, 4096, ui_cache_limit - 1, ui_cache_limit),
            "one-frame cache rejects a payload that exceeds its remaining byte budget");
    require(!nf_ui_frame_payload_fits_budget(NF_UI_4K_WIDTH - 1, NF_UI_4K_HEIGHT, 0, ui_cache_limit),
            "undersized menu asset cannot consume the replacement slot");
    require(!nf_ui_frame_payload_fits_budget(UINT32_MAX, UINT32_MAX, 0, ui_cache_limit),
            "oversized dimensions fail safely without arithmetic wrap");
    NFUiFrameCache frame_cache={0};
    MockUiCache mock={0};mock.next_handle=100;
    uint32_t frame=nf_ui_frame_cache_get(&frame_cache,0x1001u,ui_cache_limit,
                                         mock_ui_load,mock_ui_upload,mock_ui_delete,&mock);
    require(frame==101&&mock.loads==1&&mock.uploads==1&&mock.deletes==0,
            "first exact menu hash loads and uploads one cache entry");
    require(nf_ui_frame_cache_get(&frame_cache,0x1001u,ui_cache_limit,
                                  mock_ui_load,mock_ui_upload,mock_ui_delete,&mock)==frame&&
            mock.loads==1&&mock.uploads==1,
            "repeated identical menu hash reuses its GPU handle without reloading");
    mock.failed_load_hash=0x1002u;
    require(nf_ui_frame_cache_get(&frame_cache,0x1002u,ui_cache_limit,
                                  mock_ui_load,mock_ui_upload,mock_ui_delete,&mock)==0&&
            frame_cache.handle==frame&&mock.uploads==1,
            "missing replacement leaves current cache intact and selects fallback");
    mock.failed_load_hash=0;mock.failed_upload_hash=0x1003u;
    require(nf_ui_frame_cache_get(&frame_cache,0x1003u,ui_cache_limit,
                                  mock_ui_load,mock_ui_upload,mock_ui_delete,&mock)==0&&
            frame_cache.handle==frame&&mock.deletes==1&&mock.deleted[0]==102,
            "failed upload discards its candidate but preserves the previous entry");
    mock.failed_upload_hash=0;mock.undersized_hash=0x1004u;
    require(nf_ui_frame_cache_get(&frame_cache,0x1004u,ui_cache_limit,
                                  mock_ui_load,mock_ui_upload,mock_ui_delete,&mock)==0&&
            mock.uploads==2&&frame_cache.handle==frame,
            "undersized replacement is rejected before GPU upload");
    mock.undersized_hash=0;
    uint32_t next_frame=nf_ui_frame_cache_get(&frame_cache,0x1005u,ui_cache_limit,
                                              mock_ui_load,mock_ui_upload,mock_ui_delete,&mock);
    require(next_frame==103&&frame_cache.handle==next_frame&&mock.deletes==2&&
            mock.deleted[1]==frame,
            "successful hash change replaces and releases the old GPU handle");
    nf_ui_frame_cache_clear(&frame_cache,mock_ui_delete,&mock);
    require(frame_cache.handle==0&&frame_cache.source_hash==0&&mock.deletes==3&&
            mock.deleted[2]==next_frame,
            "cache clear releases its active handle exactly once");
    require(!nf_ui_overlay_has_content(NULL, NF_UI_SOURCE_WIDTH * NF_UI_SOURCE_HEIGHT),
            "missing overlay source is not captured as a HUD asset");
    for (unsigned i = 0; i < NF_UI_SOURCE_WIDTH * NF_UI_SOURCE_HEIGHT; ++i)
        source[i] = 0x00FFFFFFu;
    require(!nf_ui_overlay_has_content(source, NF_UI_SOURCE_WIDTH * NF_UI_SOURCE_HEIGHT),
            "fully transparent overlay is not captured as a HUD asset");
    source[1234] = 0x01000000u;
    require(nf_ui_overlay_has_content(source, NF_UI_SOURCE_WIDTH * NF_UI_SOURCE_HEIGHT),
            "overlay with visible alpha is retained");
    const uint32_t transparent = 0x00000000u;
    const uint32_t black = 0xFF000000u;
    const uint32_t white = 0xFFFFFFFFu;

    for (unsigned i = 0; i < NF_UI_SOURCE_WIDTH * NF_UI_SOURCE_HEIGHT; ++i)
        source[i] = 0x7F31A5C2u;
    nf_ui_scale4x(source, scratch, output);
    for (unsigned i = 0; i < NF_UI_SCALED_WIDTH * NF_UI_SCALED_HEIGHT; ++i)
        require(output[i] == 0x7F31A5C2u, "solid RGBA planes remain exact");

    for (unsigned i = 0; i < NF_UI_SOURCE_WIDTH * NF_UI_SOURCE_HEIGHT; ++i)
        source[i] = transparent;
    source[40 * NF_UI_SOURCE_WIDTH + 50] = white;
    nf_ui_scale4x(source, scratch, output);
    static const char *const dot_shape[] = {".##.", "####", "####", ".##."};
    for (unsigned y = 0; y < 4; ++y)
        for (unsigned x = 0; x < 4; ++x)
            require(pixel(50 * 4 + x, 40 * 4 + y) ==
                    (dot_shape[y][x] == '#' ? white : transparent),
                    "isolated glyph dot keeps deterministic edge-aware shape");
    require(pixel(50 * 4 - 1, 40 * 4) == transparent &&
            pixel(51 * 4, 40 * 4) == transparent,
            "transparent overlay outside glyph remains transparent");

    for (unsigned i = 0; i < NF_UI_SOURCE_WIDTH * NF_UI_SOURCE_HEIGHT; ++i)
        source[i] = black;
    for (unsigned y = 0; y < NF_UI_SOURCE_HEIGHT; ++y)
        source[y * NF_UI_SOURCE_WIDTH + 120] = white;
    nf_ui_scale4x(source, scratch, output);
    for (unsigned y = 0; y < NF_UI_SCALED_HEIGHT; ++y) {
        require(pixel(120 * 4, y) == white && pixel(120 * 4 + 3, y) == white,
                "one-pixel bitmap stroke scales to four output pixels");
        require(pixel(120 * 4 - 1, y) == black && pixel(120 * 4 + 4, y) == black,
                "edge-aware scaling does not widen a straight stroke");
    }

    puts("UI scaling, exact replacement, bounded cache reuse/replacement/failure/cleanup, and overlay tests passed.");
    return 0;
}
