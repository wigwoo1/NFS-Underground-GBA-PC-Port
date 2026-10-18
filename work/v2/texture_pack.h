#ifndef NFSUG_TEXTURE_PACK_H
#define NFSUG_TEXTURE_PACK_H

#include <stdint.h>
#include <stddef.h>

/* External replacements live below <exe-dir>/textures/4k. The pack is active
   only when its ready marker is present and explicitly marks a full pack. */
uint64_t nf_texture_source_hash(const uint32_t *rgba, uint32_t width, uint32_t height);
int nf_texture_pack_ready(const char *exe_dir);
int nf_texture_pack_preference_load(const char *settings_path);
int nf_texture_pack_preference_save(const char *settings_path, int upscaled);
/* Build one immutable hash index for a ready pack. The runtime uses it to skip
   repeated filesystem probes for source textures that have no replacement. */
int nf_texture_pack_cache_prepare(const char *exe_dir);
/* Read valid replacement payloads into RAM before realtime drawing begins. */
int nf_texture_pack_cache_preload(const char *exe_dir);
/* Returns the number of indexed files; cache_preloaded_at succeeds only for
   validated payloads resident in RAM. Returned pixels remain owned by cache. */
size_t nf_texture_pack_cache_index_count(void);
int nf_texture_pack_cache_preloaded_at(size_t index, uint64_t *source_hash,
                                       uint32_t *width, uint32_t *height,
                                       const uint32_t **rgba);
void nf_texture_pack_cache_clear(void);
/* Overflow-safe RGBA8 byte-budget check used by CPU and GPU preload caps. */
int nf_texture_payload_fits_budget(uint32_t width, uint32_t height,
                                    uint64_t used_bytes, uint64_t max_bytes);
/* On missing/invalid replacement, rgba is NULL and dimensions are the source size. */
int nf_texture_pack_load(const char *exe_dir, uint64_t source_hash,
                         uint32_t source_width, uint32_t source_height,
                         uint32_t **rgba, uint32_t *width, uint32_t *height);
/* Same output contract, but requires cache_prepare and avoids per-texture pack.ready checks. */
int nf_texture_pack_load_cached(const char *exe_dir, uint64_t source_hash,
                                uint32_t source_width, uint32_t source_height,
                                uint32_t **rgba, uint32_t *width, uint32_t *height);

#endif
