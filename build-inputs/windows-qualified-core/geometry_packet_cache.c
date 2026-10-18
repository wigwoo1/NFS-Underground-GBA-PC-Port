#include "geometry_packet_cache.h"
#include <stdlib.h>
#include <string.h>

static int cache_ready(const NFGeometryCache *c) {
    return c && c->budget >= sizeof(*c) && c->budget <= NF_GEOMETRY_CACHE_MAX_BYTES;
}
static int key_valid(const NFGeometryCacheKey *k) {
    return k && k->epoch && k->begin <= k->end;
}
static int key_equal(const NFGeometryCacheKey *a, const NFGeometryCacheKey *b) {
    return a->epoch == b->epoch && a->serial == b->serial &&
        a->begin == b->begin && a->end == b->end && a->page == b->page;
}
static void remove_entry(NFGeometryCache *c, unsigned i) {
    NFGeometryCacheEntry *e = c->entries + i;
    if (!e->valid) return;
    c->used -= e->guard_bytes + e->packet_bytes;
    free(e->guard); free(e->packet);
    memmove(e, e + 1, (NF_GEOMETRY_CACHE_SLOTS - i - 1) * sizeof(*e));
    memset(c->entries + NF_GEOMETRY_CACHE_SLOTS - 1, 0, sizeof(*e));
}
int nf_geometry_cache_init(NFGeometryCache *c, size_t budget) {
    if (!c || budget < sizeof(*c) || budget > NF_GEOMETRY_CACHE_MAX_BYTES) return 0;
    memset(c, 0, sizeof(*c)); c->budget = budget; c->used = c->peak = sizeof(*c);
    return 1;
}
void nf_geometry_cache_clear(NFGeometryCache *c) {
    if (!cache_ready(c)) return;
    while (c->entries[0].valid) remove_entry(c, 0);
    c->clears++;
}
int nf_geometry_cache_copy(NFGeometryCache *c, const NFGeometryCacheKey *k,
                           const void *guard, size_t gb, void **packet, size_t *pb) {
    if (packet) *packet = NULL;
    if (pb) *pb = 0;
    if (!cache_ready(c) || !key_valid(k) || !guard || !gb ||
        gb > NF_GEOMETRY_CACHE_MAX_GUARD || !packet || !pb) return -1;
    for (unsigned i = 0; i < NF_GEOMETRY_CACHE_SLOTS; i++) {
        NFGeometryCacheEntry *e = c->entries + i;
        if (!e->valid || !key_equal(k, &e->key) || gb != e->guard_bytes ||
            memcmp(guard, e->guard, gb)) continue;
        void *copy = malloc(e->packet_bytes);
        if (!copy) { c->allocation_failures++; return -1; }
        memcpy(copy, e->packet, e->packet_bytes);
        *packet = copy; *pb = e->packet_bytes;
        NFGeometryCacheEntry hit = *e;
        memmove(c->entries + 1, c->entries, i * sizeof(*e));
        c->entries[0] = hit; c->hits++; return 1;
    }
    c->misses++; return 0;
}
int nf_geometry_cache_store(NFGeometryCache *c, const NFGeometryCacheKey *k,
                            const void *guard, size_t gb, const void *packet, size_t pb) {
    if (!cache_ready(c) || !key_valid(k) || !guard || !gb ||
        gb > NF_GEOMETRY_CACHE_MAX_GUARD || !packet || !pb ||
        gb > c->budget - sizeof(*c) || pb > c->budget - sizeof(*c) - gb ||
        gb > NF_GEOMETRY_CACHE_MAX_BYTES - c->used ||
        pb > NF_GEOMETRY_CACHE_MAX_BYTES - c->used - gb) return 0;
    /* Allocate before eviction: memory failure must preserve old cached data.
     * The hard cap check also accounts for this temporary insertion storage. */
    unsigned char *g = malloc(gb);
    if (!g) { c->allocation_failures++; return 0; }
    unsigned char *p = malloc(pb);
    if (!p) { free(g); c->allocation_failures++; return 0; }
    memcpy(g, guard, gb); memcpy(p, packet, pb);
    for (unsigned i = 0; i < NF_GEOMETRY_CACHE_SLOTS; i++)
        if (c->entries[i].valid && key_equal(k, &c->entries[i].key)) {
            remove_entry(c, i); break;
        }
    while (c->used > c->budget - gb - pb || c->entries[NF_GEOMETRY_CACHE_SLOTS - 1].valid) {
        unsigned last = 0;
        while (last + 1 < NF_GEOMETRY_CACHE_SLOTS && c->entries[last + 1].valid) last++;
        remove_entry(c, last); c->evictions++;
    }
    memmove(c->entries + 1, c->entries, (NF_GEOMETRY_CACHE_SLOTS - 1) * sizeof(c->entries[0]));
    NFGeometryCacheEntry fresh = {0}; fresh.key = *k;
    fresh.guard = g; fresh.packet = p; fresh.guard_bytes = gb; fresh.packet_bytes = pb; fresh.valid = 1;
    c->entries[0] = fresh; c->used += gb + pb;
    if (c->used > c->peak) c->peak = c->used;
    c->stores++; return 1;
}
