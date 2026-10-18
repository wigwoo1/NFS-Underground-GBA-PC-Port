#include "ui_scale.h"
#include <stdlib.h>

static void scale2x_rgba(const uint32_t *source, unsigned width, unsigned height,
                         uint32_t *output) {
    for (unsigned y = 0; y < height; ++y) {
        unsigned up = y ? y - 1 : y;
        unsigned down = y + 1 < height ? y + 1 : y;
        for (unsigned x = 0; x < width; ++x) {
            unsigned left = x ? x - 1 : x;
            unsigned right = x + 1 < width ? x + 1 : x;
            uint32_t e = source[y * width + x];
            uint32_t b = source[up * width + x];
            uint32_t d = source[y * width + left];
            uint32_t f = source[y * width + right];
            uint32_t h = source[down * width + x];
            uint32_t p00 = e, p10 = e, p01 = e, p11 = e;
            if (b != h && d != f) {
                if (d == b) p00 = d;
                if (b == f) p10 = f;
                if (d == h) p01 = d;
                if (h == f) p11 = h;
            }
            unsigned oy = y * 2, ox = x * 2;
            output[oy * width * 2 + ox] = p00;
            output[oy * width * 2 + ox + 1] = p10;
            output[(oy + 1) * width * 2 + ox] = p01;
            output[(oy + 1) * width * 2 + ox + 1] = p11;
        }
    }
}

int nf_ui_frame_replacement_matches(uint64_t source_hash, uint64_t replacement_hash,
                                      unsigned replacement_width, unsigned replacement_height) {
    return source_hash != 0 && source_hash == replacement_hash &&
           replacement_width >= NF_UI_4K_WIDTH &&
           replacement_height >= NF_UI_4K_HEIGHT;
}

int nf_ui_frame_payload_fits_budget(uint32_t width, uint32_t height,
                                    uint64_t used_bytes, uint64_t max_bytes) {
    if (width < NF_UI_4K_WIDTH || height < NF_UI_4K_HEIGHT || used_bytes > max_bytes) return 0;
    uint64_t pixels = (uint64_t)width * height;
    if (pixels > UINT64_MAX / sizeof(uint32_t)) return 0;
    uint64_t bytes = pixels * sizeof(uint32_t);
    return bytes <= max_bytes - used_bytes;
}

uint32_t nf_ui_frame_cache_get(NFUiFrameCache *cache, uint64_t source_hash,
                               uint64_t max_bytes, NFUiFrameLoadFn load,
                               NFUiFrameUploadFn upload, NFUiFrameDeleteFn destroy,
                               void *context) {
    if (!cache || !source_hash || !load || !upload || !destroy) return 0;
    if (cache->handle && cache->source_hash == source_hash) return cache->handle;

    uint32_t *pixels = NULL, width = 0, height = 0;
    if (!load(context, source_hash, &pixels, &width, &height) || !pixels) {
        free(pixels);
        return 0;
    }
    if (!nf_ui_frame_replacement_matches(source_hash, source_hash, width, height) ||
        !nf_ui_frame_payload_fits_budget(width, height, 0, max_bytes)) {
        free(pixels);
        return 0;
    }

    uint32_t candidate = 0;
    int uploaded = upload(context, pixels, width, height, &candidate);
    free(pixels);
    if (!uploaded || !candidate) {
        if (candidate) destroy(context, candidate);
        return 0;
    }

    if (cache->handle) destroy(context, cache->handle);
    cache->source_hash = source_hash;
    cache->handle = candidate;
    cache->width = width;
    cache->height = height;
    return candidate;
}

void nf_ui_frame_cache_clear(NFUiFrameCache *cache, NFUiFrameDeleteFn destroy,
                             void *context) {
    if (!cache) return;
    if (cache->handle && destroy) destroy(context, cache->handle);
    cache->source_hash = 0;
    cache->handle = 0;
    cache->width = 0;
    cache->height = 0;
}

int nf_ui_overlay_has_content(const uint32_t *pixels, unsigned pixel_count) {
    if (!pixels) return 0;
    for (unsigned i = 0; i < pixel_count; ++i)
        if (pixels[i] >> 24) return 1;
    return 0;
}

void nf_ui_scale4x(const uint32_t *source, uint32_t *scratch, uint32_t *output) {
    if (!source || !scratch || !output) return;
    scale2x_rgba(source, NF_UI_SOURCE_WIDTH, NF_UI_SOURCE_HEIGHT, scratch);
    scale2x_rgba(scratch, NF_UI_SOURCE_WIDTH * 2, NF_UI_SOURCE_HEIGHT * 2, output);
}
