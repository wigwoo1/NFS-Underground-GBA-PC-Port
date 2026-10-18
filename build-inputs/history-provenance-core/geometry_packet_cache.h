#ifndef NF_GEOMETRY_PACKET_CACHE_H
#define NF_GEOMETRY_PACKET_CACHE_H
#include <stddef.h>
#include <stdint.h>

/* Single producer-thread use only. Never publishes pointers into cache storage.
 * Callers must validate live owner availability before lookup, supply an exact
 * guard covering ALL mutable producer inputs, and clear on lifecycle changes.
 * This module cannot establish those producer-specific conditions itself. */
#define NF_GEOMETRY_CACHE_SLOTS 4
#define NF_GEOMETRY_CACHE_MAX_BYTES ((size_t)64 * 1024 * 1024)
#define NF_GEOMETRY_CACHE_MAX_GUARD ((size_t)32 * 1024)
typedef struct {
    uint64_t epoch;
    uint32_t serial, begin, end, page;
} NFGeometryCacheKey;
typedef struct {
    NFGeometryCacheKey key;
    unsigned char *guard, *packet;
    size_t guard_bytes, packet_bytes;
    unsigned valid;
} NFGeometryCacheEntry;
typedef struct {
    NFGeometryCacheEntry entries[NF_GEOMETRY_CACHE_SLOTS]; /* MRU first */
    size_t budget, used, peak;
    uint64_t hits, misses, stores, evictions, clears, allocation_failures;
} NFGeometryCache;

/* Budget includes resident struct, guards and packets, not caller-owned copies.
 * Insertion staging plus resident storage also never exceeds the hard 64 MiB
 * maximum: a store that cannot stage safely is rejected without changing entries.
 * init is for fresh storage only; clear releases entries and retains statistics. */
int nf_geometry_cache_init(NFGeometryCache *cache, size_t budget);
void nf_geometry_cache_clear(NFGeometryCache *cache);
/* Returns 1 hit (fresh malloc allocation), 0 miss, -1 invalid/allocation failure.
 * Outputs are reset even on failure. Caller frees successful output with free. */
int nf_geometry_cache_copy(NFGeometryCache *cache, const NFGeometryCacheKey *key,
                           const void *guard, size_t guard_bytes,
                           void **packet, size_t *packet_bytes);
/* Store makes private copies. A rejected/failed store never removes old entries.
 * Return 1 stored, 0 invalid/over-budget/allocation failure. */
int nf_geometry_cache_store(NFGeometryCache *cache, const NFGeometryCacheKey *key,
                            const void *guard, size_t guard_bytes,
                            const void *packet, size_t packet_bytes);
#endif
