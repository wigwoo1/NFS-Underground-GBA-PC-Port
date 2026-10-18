#ifndef NF_HARDWARE_SUBMISSION_H
#define NF_HARDWARE_SUBMISSION_H
#include "presentation_submission.h"
typedef struct NFHardwareSubmission NFHardwareSubmission;
/* Producer clones complete source pages; discrete hardware refresh=floor(target).
   Creation/rejected reads leave caller output unchanged. Epoch is supplied by
   the producer's exact queue selection, not inferred from snapshot contents. */
__declspec(dllexport) int nf_hardware_submission_create(const NFLayerSnapshot*,const NFTimelineSample*,const NFSubmissionSchedule*,NFHardwareSubmission**);
__declspec(dllexport) void nf_hardware_submission_destroy(NFHardwareSubmission*);
__declspec(dllexport) int nf_hardware_submission_row(const NFHardwareSubmission*,uint64_t,uint32_t,unsigned,NFHardwareLayerRow*);
__declspec(dllexport) int nf_hardware_submission_metadata(const NFHardwareSubmission*,NFTimelineSample*,NFSubmissionSchedule*);
__declspec(dllexport) size_t nf_hardware_submission_bytes(const NFHardwareSubmission*);
#endif
