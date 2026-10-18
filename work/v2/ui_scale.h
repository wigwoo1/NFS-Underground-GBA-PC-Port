#ifndef NF_UI_SCALE_H
#define NF_UI_SCALE_H
#include <stdint.h>

#define NF_UI_SOURCE_WIDTH 240u
#define NF_UI_SOURCE_HEIGHT 160u
#define NF_UI_SCALE 4u
#define NF_UI_4K_WIDTH 3240u
#define NF_UI_4K_HEIGHT 2160u
#define NF_UI_SCALED_WIDTH (NF_UI_SOURCE_WIDTH * NF_UI_SCALE)
#define NF_UI_SCALED_HEIGHT (NF_UI_SOURCE_HEIGHT * NF_UI_SCALE)

/* A regenerated menu frame or transparent HUD overlay is used only for an exact
   source hash and when it covers the active 3240x2160 game viewport at 4K. */
#define NF_UI_FRAME_CACHE_MAX_BYTES (UINT64_C(128) * 1024u * 1024u)
int nf_ui_frame_replacement_matches(uint64_t source_hash, uint64_t replacement_hash,
                                      unsigned replacement_width, unsigned replacement_height);

/* True when a transparent UI overlay contains at least one visible RGBA pixel. */
int nf_ui_overlay_has_content(const uint32_t *pixels, unsigned pixel_count);

/* Validate one lazily resident complete menu frame against a byte budget. */
int nf_ui_frame_payload_fits_budget(uint32_t width, uint32_t height,
                                    uint64_t used_bytes, uint64_t max_bytes);

/* One-entry exact-source UI cache. Load returns allocated RGBA pixels; upload
   returns a nonzero caller-owned handle. A failed candidate leaves the current
   entry available. All three callbacks execute synchronously on the caller. */
typedef struct {
    uint64_t source_hash;
    uint32_t handle, width, height;
} NFUiFrameCache;
typedef int (*NFUiFrameLoadFn)(void *context, uint64_t source_hash,
                               uint32_t **pixels, uint32_t *width, uint32_t *height);
typedef int (*NFUiFrameUploadFn)(void *context, const uint32_t *pixels,
                                 uint32_t width, uint32_t height, uint32_t *handle);
typedef void (*NFUiFrameDeleteFn)(void *context, uint32_t handle);
uint32_t nf_ui_frame_cache_get(NFUiFrameCache *cache, uint64_t source_hash,
                               uint64_t max_bytes, NFUiFrameLoadFn load,
                               NFUiFrameUploadFn upload, NFUiFrameDeleteFn destroy,
                               void *context);
void nf_ui_frame_cache_clear(NFUiFrameCache *cache, NFUiFrameDeleteFn destroy,
                             void *context);

/* Scale an RGBA source-resolution overlay by 4x using two Scale2x passes.
   scratch must hold 480x320 pixels; output must hold 960x640 pixels. */
void nf_ui_scale4x(const uint32_t *source, uint32_t *scratch, uint32_t *output);

#endif
