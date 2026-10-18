#ifndef NF_VISIBILITY_CAPACITY_H
#define NF_VISIBILITY_CAPACITY_H
/* Build-specific research ABI. Default preserves existing diagnostic clients.
   Wide clients and DLL must use the same capacity; never write into game RAM. */
#ifndef NF_VISIBILITY_QUEUE_CAPACITY
#define NF_VISIBILITY_QUEUE_CAPACITY 20
#endif
#if NF_VISIBILITY_QUEUE_CAPACITY < 20 || NF_VISIBILITY_QUEUE_CAPACITY > 64
#error Unsupported visibility capacity
#endif
#define NF_VISIBILITY_QUEUE_BYTES (16 * NF_VISIBILITY_QUEUE_CAPACITY)
#endif
