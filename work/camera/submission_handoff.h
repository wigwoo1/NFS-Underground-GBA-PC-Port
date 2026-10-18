#ifndef NF_SUBMISSION_HANDOFF_H
#define NF_SUBMISSION_HANDOFF_H
#include "presentation_submission.h"
typedef struct NFSubmissionHandoff NFSubmissionHandoff;
/* Bounded ownership transfer. Push succeeds by clearing caller's pointer;
   failure leaves it owned by caller. Pop transfers sole ownership to consumer.
   Epoch changes drain pending entries, never an already popped frame.
   Close rejects pushes and drains pending entries; join users before destroy. */
__declspec(dllexport) NFSubmissionHandoff*nf_handoff_create(uint64_t epoch);
__declspec(dllexport) int nf_handoff_push(NFSubmissionHandoff*,NFPresentationSubmission**);
__declspec(dllexport) NFPresentationSubmission*nf_handoff_pop(NFSubmissionHandoff*);
__declspec(dllexport) int nf_handoff_epoch(NFSubmissionHandoff*,uint64_t);
__declspec(dllexport) void nf_handoff_close(NFSubmissionHandoff*);
__declspec(dllexport) void nf_handoff_destroy(NFSubmissionHandoff*);
/* Serialized presentation boundary. Callback runs under epoch lock: 1 commit,
   0 stale/closed, -1 callback failure. Callback must not mutate this queue. */
__declspec(dllexport) int nf_handoff_commit(NFSubmissionHandoff*,uint64_t,int(*)(void*),void*);
/* pushed,popped,retired-pending,rejected; synchronized exact counters. */
__declspec(dllexport) int nf_handoff_stats(NFSubmissionHandoff*,uint64_t[4]);
__declspec(dllexport) uint64_t nf_handoff_current_epoch(NFSubmissionHandoff*);
/* Before changing producer source epoch: drain and block commits/pushes.
   Only publishing a strictly newer epoch resumes presentation. */
__declspec(dllexport) void nf_handoff_invalidate(NFSubmissionHandoff*);
/* Safe blank presentation while invalid, serialized against close/epoch. */
__declspec(dllexport) int nf_handoff_blank(NFSubmissionHandoff*,int(*)(void*),void*);
#endif
