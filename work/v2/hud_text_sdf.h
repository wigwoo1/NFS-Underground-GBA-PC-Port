#ifndef NF_HUD_TEXT_SDF_H
#define NF_HUD_TEXT_SDF_H
#include <stddef.h>
#include <stdint.h>

/* Encode signed Euclidean distance to a binary text mask as biased R8:
   128 is the edge, one byte represents 1/16 source pixel. */
int nf_hud_text_sdf_encode_scaled(const uint8_t *coverage, size_t width, size_t height,
                                  float screen_pixels_per_source_pixel,
                                  uint8_t *encoded, size_t capacity);
int nf_hud_text_sdf_encode(const uint8_t *coverage, size_t width, size_t height,
                           uint8_t *encoded, size_t capacity);
#endif
