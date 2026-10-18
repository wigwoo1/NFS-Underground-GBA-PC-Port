/* Real module compiled with an instrumented allocator to verify ownership and
 * failure behavior, including failures after the first insertion allocation. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "geometry_packet_cache.h"
typedef union { struct { size_t size; } value; max_align_t alignment; } Allocation;
static size_t live_bytes, max_live_bytes, live_allocations;
static long fail_after = -1;
static void *tracked_malloc(size_t size) {
    if (fail_after == 0) return NULL;
    if (fail_after > 0) fail_after--;
    Allocation *a = malloc(sizeof(*a) + size);
    assert(a); a->value.size = size;
    live_bytes += size; live_allocations++;
    if (live_bytes > max_live_bytes) max_live_bytes = live_bytes;
    return a + 1;
}
static void tracked_free(void *ptr) {
    if (!ptr) return;
    Allocation *a = (Allocation *)ptr - 1;
    assert(live_bytes >= a->value.size && live_allocations);
    live_bytes -= a->value.size; live_allocations--; free(a);
}
#define malloc tracked_malloc
#define free tracked_free
#include "geometry_packet_cache.c"
#undef malloc
#undef free

static NFGeometryCacheKey key(unsigned serial) {
    NFGeometryCacheKey k = {7, serial, 10, 12, 0}; return k;
}
static unsigned char guard[48], data[4096];
static void expect_hit(NFGeometryCache *c, NFGeometryCacheKey k) {
    void *out = NULL; size_t bytes = 0;
    assert(nf_geometry_cache_copy(c, &k, guard, sizeof(guard), &out, &bytes) == 1);
    assert(bytes == sizeof(data) && !memcmp(out, data, bytes)); tracked_free(out);
}
static void expect_miss(NFGeometryCache *c, NFGeometryCacheKey k) {
    void *out = (void *)(uintptr_t)1; size_t bytes = 999;
    assert(nf_geometry_cache_copy(c, &k, guard, sizeof(guard), &out, &bytes) == 0);
    assert(!out && !bytes);
}
int main(void) {
    NFGeometryCache c = {0}; NFGeometryCacheKey k = key(1);
    for (size_t i = 0; i < sizeof(data); i++) data[i] = (unsigned char)(i * 71);
    for (size_t i = 0; i < sizeof(guard); i++) guard[i] = (unsigned char)(i * 13);
    assert(!nf_geometry_cache_init(NULL, 100));
    assert(!nf_geometry_cache_init(&c, sizeof(c) - 1));
    assert(!nf_geometry_cache_init(&c, NF_GEOMETRY_CACHE_MAX_BYTES + 1));
    assert(nf_geometry_cache_init(&c, 1024 * 1024)); expect_miss(&c, k);
    assert(nf_geometry_cache_store(&c, &k, guard, sizeof(guard), data, sizeof(data)));
    void *a, *b; size_t ab, bb;
    assert(nf_geometry_cache_copy(&c, &k, guard, sizeof(guard), &a, &ab) == 1);
    assert(nf_geometry_cache_copy(&c, &k, guard, sizeof(guard), &b, &bb) == 1);
    assert(a != b && ab == bb); ((unsigned char *)a)[0] ^= 1;
    assert(!memcmp(b, data, bb)); expect_hit(&c, k);
    /* Changing the source buffers cannot mutate the stored copies. */
    unsigned char saved_guard = guard[0], saved_data = data[0];
    guard[0] ^= 1; expect_miss(&c, k); guard[0] = saved_guard;
    data[0] ^= 1; assert(((unsigned char *)b)[0] == saved_data); data[0] = saved_data;
    NFGeometryCacheKey changed = k; changed.epoch++; expect_miss(&c, changed);
    changed = k; changed.serial++; expect_miss(&c, changed);
    changed = k; changed.begin++; expect_miss(&c, changed);
    changed = k; changed.end++; expect_miss(&c, changed);
    changed = k; changed.page++; expect_miss(&c, changed);
    void *out = (void *)(uintptr_t)1; size_t bytes = 99;
    assert(nf_geometry_cache_copy(&c, &k, NULL, 1, &out, &bytes) == -1 && !out && !bytes);
    assert(nf_geometry_cache_copy(&c, &k, guard, sizeof(guard)-1, &out, &bytes) == 0);
    assert(!nf_geometry_cache_store(&c, &k, guard, SIZE_MAX, data, SIZE_MAX));
    assert(!nf_geometry_cache_store(&c, &k, guard, sizeof(guard), data, SIZE_MAX));
    /* Failure must not evict a useful older owner. */
    size_t before = c.used; uint64_t stores = c.stores;
    fail_after = 0;
    assert(nf_geometry_cache_copy(&c, &k, guard, sizeof(guard), &out, &bytes) == -1 && !out && !bytes);
    assert(!nf_geometry_cache_store(&c, &k, guard, sizeof(guard), data, sizeof(data)));
    fail_after = 1;
    assert(!nf_geometry_cache_store(&c, &k, guard, sizeof(guard), data, sizeof(data)));
    fail_after = -1; assert(c.used == before && c.stores == stores); expect_hit(&c, k);
    /* LRU hit changes the eviction victim; every field participates in key. */
    for (unsigned i = 2; i <= 4; i++) { changed = key(i); assert(nf_geometry_cache_store(&c, &changed, guard, sizeof(guard), data, sizeof(data))); }
    expect_hit(&c, k); changed = key(5);
    assert(nf_geometry_cache_store(&c, &changed, guard, sizeof(guard), data, sizeof(data)));
    expect_miss(&c, key(2)); expect_hit(&c, k); assert(c.evictions == 1);
    /* Replacement keeps a single entry and uses exact new guard/data. */
    guard[1] ^= 1;
    assert(nf_geometry_cache_store(&c, &k, guard, sizeof(guard), data, sizeof(data))); expect_hit(&c, k);
    guard[1] ^= 1; expect_miss(&c, k); guard[1] ^= 1;
    nf_geometry_cache_clear(&c); expect_miss(&c, k);
    /* Already returned frames survive cache clearing and destruction. */
    assert(!memcmp(b, data, bb)); tracked_free(a); tracked_free(b);
    assert(c.used == sizeof(c) && !live_allocations && !live_bytes);
    nf_geometry_cache_clear(&c);
    /* Exact resident budget and eviction under byte pressure. */
    assert(nf_geometry_cache_init(&c, sizeof(c) + sizeof(guard) + sizeof(data)));
    assert(nf_geometry_cache_store(&c, &k, guard, sizeof(guard), data, sizeof(data)));
    assert(c.used == c.budget); changed = key(6);
    assert(nf_geometry_cache_store(&c, &changed, guard, sizeof(guard), data, sizeof(data)));
    expect_miss(&c, k); expect_hit(&c, changed); assert(c.peak <= c.budget);
    nf_geometry_cache_clear(&c);
    assert(nf_geometry_cache_init(&c, sizeof(c) + sizeof(guard) + sizeof(data) - 1));
    assert(!nf_geometry_cache_store(&c, &k, guard, sizeof(guard), data, sizeof(data)));
    nf_geometry_cache_clear(&c);
    /* Hard cap includes staging. Reject oversized replacement before allocation. */
    assert(nf_geometry_cache_init(&c, NF_GEOMETRY_CACHE_MAX_BYTES));
    size_t large_bytes = NF_GEOMETRY_CACHE_MAX_BYTES - sizeof(c) - sizeof(guard);
    unsigned char *large = malloc(large_bytes); assert(large); memset(large, 0x97, large_bytes);
    assert(nf_geometry_cache_store(&c, &k, guard, sizeof(guard), large, large_bytes));
    assert(c.used == NF_GEOMETRY_CACHE_MAX_BYTES);
    size_t previous_allocations = live_allocations;
    assert(!nf_geometry_cache_store(&c, &changed, guard, sizeof(guard), data, sizeof(data)));
    assert(live_allocations == previous_allocations); nf_geometry_cache_clear(&c); free(large);
    assert(!live_allocations && !live_bytes);
    assert(max_live_bytes + sizeof(c) <= NF_GEOMETRY_CACHE_MAX_BYTES);
    puts("PASS_GEOMETRY_PACKET_CACHE_OWNERSHIP_BUDGET_FAILURE_LRU");
    return 0;
}
