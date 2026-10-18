#ifndef NF_RENDER_HANDOFF_H
#define NF_RENDER_HANDOFF_H
#include "render_submission.h"
typedef struct NFRenderHandoff NFRenderHandoff;
/* Bounded ownership transfer. Push succeeds by clearing caller's pointer;
   failure leaves it owned by caller. Pop transfers sole ownership to consumer.
   Epoch changes drain pending entries, never an already popped frame.
   Close rejects pushes and drains pending entries; join users before destroy. */
__declspec(dllexport) NFRenderHandoff*nf_render_handoff_create(uint64_t epoch);
__declspec(dllexport) int nf_render_handoff_push(NFRenderHandoff*,NFRenderSubmission**);
__declspec(dllexport) NFRenderSubmission*nf_render_handoff_pop(NFRenderHandoff*);
__declspec(dllexport) int nf_render_handoff_epoch(NFRenderHandoff*,uint64_t);
__declspec(dllexport) void nf_render_handoff_close(NFRenderHandoff*);
__declspec(dllexport) void nf_render_handoff_destroy(NFRenderHandoff*);
/* Serialized presentation boundary. Callback runs under epoch lock: 1 commit,
   0 stale/closed, -1 callback failure. Callback must not mutate this queue. */
__declspec(dllexport) int nf_render_handoff_commit(NFRenderHandoff*,uint64_t,int(*)(void*),void*);
/* pushed,popped,retired-pending,rejected; synchronized exact counters. */
__declspec(dllexport) int nf_render_handoff_stats(NFRenderHandoff*,uint64_t[4]);
__declspec(dllexport) uint64_t nf_render_handoff_current_epoch(NFRenderHandoff*);
/* Before changing producer source epoch: drain and block commits/pushes.
   Only publishing a strictly newer epoch resumes presentation. */
__declspec(dllexport) void nf_render_handoff_invalidate(NFRenderHandoff*);
/* Safe blank presentation while invalid, serialized against close/epoch. */
__declspec(dllexport) int nf_render_handoff_blank(NFRenderHandoff*,int(*)(void*),void*);
#endif
