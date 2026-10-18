#include "hud_text_sdf.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

#define NF_SDF_INF 1.0e20f
#define NF_SDF_LIMIT 7.9375f

static int edt_line(const float *f, size_t n, float *d, size_t *v, double *z) {
    size_t first = n;
    for (size_t i = 0; i < n; ++i) {
        if (f[i] < NF_SDF_INF * 0.5f) { first = i; break; }
    }
    if (first == n) {
        for (size_t i = 0; i < n; ++i) d[i] = NF_SDF_INF;
        return 1;
    }

    size_t k = 0;
    v[0] = first;
    z[0] = -HUGE_VAL;
    z[1] = HUGE_VAL;
    for (size_t q = first + 1; q < n; ++q) {
        if (f[q] >= NF_SDF_INF * 0.5f) continue;
        double s;
        for (;;) {
            size_t vk = v[k];
            s = ((double)f[q] + (double)q*q -
                 (double)f[vk] - (double)vk*vk) /
                (2.0 * ((double)q - (double)vk));
            if (s > z[k] || k == 0) break;
            --k;
        }
        if (s <= z[k] && k == 0) {
            v[0] = q;
            z[0] = -HUGE_VAL;
            z[1] = HUGE_VAL;
        } else {
            ++k;
            v[k] = q;
            z[k] = s;
            z[k+1] = HUGE_VAL;
        }
    }
    k = 0;
    for (size_t q = 0; q < n; ++q) {
        while (z[k+1] < (double)q) ++k;
        double delta = (double)q - (double)v[k];
        d[q] = (float)(delta*delta + f[v[k]]);
    }
    return 1;
}

static int edt_2d(const uint8_t *features, size_t width, size_t height,
                  float *out) {
    size_t count = width * height;
    size_t longest = width > height ? width : height;
    float *tmp = (float*)malloc(count * sizeof(*tmp));
    float *f = (float*)malloc(longest * sizeof(*f));
    float *d = (float*)malloc(longest * sizeof(*d));
    size_t *v = (size_t*)malloc(longest * sizeof(*v));
    double *z = (double*)malloc((longest + 1) * sizeof(*z));
    if (!tmp || !f || !d || !v || !z) {
        free(tmp); free(f); free(d); free(v); free(z);
        return 0;
    }

    for (size_t y = 0; y < height; ++y) {
        for (size_t x = 0; x < width; ++x)
            f[x] = features[y*width+x] ? 0.0f : NF_SDF_INF;
        edt_line(f, width, d, v, z);
        memcpy(tmp + y*width, d, width * sizeof(*d));
    }
    for (size_t x = 0; x < width; ++x) {
        for (size_t y = 0; y < height; ++y) f[y] = tmp[y*width+x];
        edt_line(f, height, d, v, z);
        for (size_t y = 0; y < height; ++y) out[y*width+x] = d[y];
    }

    free(tmp); free(f); free(d); free(v); free(z);
    return 1;
}

int nf_hud_text_sdf_encode_scaled(const uint8_t *coverage, size_t width, size_t height,
                                  float screen_pixels_per_source_pixel,
                                  uint8_t *encoded, size_t capacity) {
    if (!(screen_pixels_per_source_pixel > 0.0f) ||
        !(screen_pixels_per_source_pixel <= 64.0f)) return 0;
    if (!coverage || !encoded || !width || !height ||
        width > 240 || height > 160 || width > SIZE_MAX / height ||
        width*height > capacity || width*height > 38400) return 0;

    size_t padded_width = width + 2, padded_height = height + 2;
    if (padded_width > SIZE_MAX / padded_height) return 0;
    size_t padded_count = padded_width * padded_height;
    uint8_t *mask = (uint8_t*)calloc(padded_count, 1);
    uint8_t *features = (uint8_t*)malloc(padded_count);
    float *distance_bg = (float*)malloc(padded_count * sizeof(*distance_bg));
    float *distance_fg = (float*)malloc(padded_count * sizeof(*distance_fg));
    uint8_t *result = (uint8_t*)malloc(width * height);
    if (!mask || !features || !distance_bg || !distance_fg || !result) {
        free(mask); free(features); free(distance_bg); free(distance_fg); free(result);
        return 0;
    }
    int any = 0;
    for (size_t y = 0; y < height; ++y) {
        for (size_t x = 0; x < width; ++x) {
            uint8_t on = coverage[y*width+x] != 0;
            mask[(y+1)*padded_width+x+1] = on;
            any |= on;
        }
    }
    for (size_t i = 0; i < padded_count; ++i) features[i] = !mask[i];
    if (!edt_2d(features,padded_width,padded_height,distance_bg)) goto fail;
    if (any) {
        for (size_t i = 0; i < padded_count; ++i) features[i] = !!mask[i];
        if (!edt_2d(features,padded_width,padded_height,distance_fg)) goto fail;
    }
    for (size_t y = 0; y < height; ++y) {
        for (size_t x = 0; x < width; ++x) {
            size_t p = (y+1)*padded_width+x+1;
            float distance;
            if (mask[p]) distance = sqrtf(distance_bg[p]) - 0.5f;
            else if (any) distance = -(sqrtf(distance_fg[p]) - 0.5f);
            else distance = -NF_SDF_LIMIT;
            /* Encode in output-pixel units so one R8 step stays subpixel after
               the HUD plane is enlarged by screen_pixels_per_source_pixel. */
            distance *= screen_pixels_per_source_pixel;
            if (distance > NF_SDF_LIMIT) distance = NF_SDF_LIMIT;
            if (distance < -8.0f) distance = -8.0f;
            int code = (int)lrintf(128.0f + distance*16.0f);
            if (code < 0) code = 0;
            if (code > 255) code = 255;
            result[y*width+x] = (uint8_t)code;
        }
    }
    memcpy(encoded,result,width*height);
    free(mask); free(features); free(distance_bg); free(distance_fg); free(result);
    return 1;
fail:
    free(mask); free(features); free(distance_bg); free(distance_fg); free(result);
    return 0;
}

int nf_hud_text_sdf_encode(const uint8_t *coverage, size_t width, size_t height,
                           uint8_t *encoded, size_t capacity) {
    return nf_hud_text_sdf_encode_scaled(coverage, width, height, 1.0f,
                                         encoded, capacity);
}
