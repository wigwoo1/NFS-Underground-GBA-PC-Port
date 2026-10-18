#ifndef NF_RENDER_SUBMISSION_H
#define NF_RENDER_SUBMISSION_H
#include "hardware_submission.h"
#include "ordered_scene_submission.h"
#include "stable_scene_submission.h"
#include "prepared_motion_submission.h"
typedef struct NFRenderSubmission NFRenderSubmission;
enum {NF_RENDER_NATIVE=1,NF_RENDER_HARDWARE=2,NF_RENDER_SPLIT=3,NF_RENDER_ORDERED=4,NF_RENDER_STABLE=5,NF_RENDER_PREPARED_MOTION=6};
__declspec(dllexport) int nf_render_submission_native(NFPresentationSubmission**,NFRenderSubmission**);
/* Takes both exclusive owners atomically; caller must provide a verified split. */
__declspec(dllexport) int nf_render_submission_split(NFPresentationSubmission**,NFPresentationSubmission**,unsigned,NFRenderSubmission**);
__declspec(dllexport) int nf_render_submission_split_view(const NFRenderSubmission*,NFPresentationSubmission**,NFPresentationSubmission**,unsigned*);
__declspec(dllexport) int nf_render_submission_hardware(NFHardwareSubmission**,NFRenderSubmission**);
/* Transfers a complete owned split only with its actual endpoint timeline. */
__declspec(dllexport) int nf_render_submission_ordered(NFOrderedSceneSubmission**,const NFTimelineSample*,const NFSubmissionSchedule*,NFRenderSubmission**);
__declspec(dllexport) const NFOrderedSceneSubmission*nf_render_submission_ordered_view(const NFRenderSubmission*);
__declspec(dllexport) int nf_render_submission_ordered_schedule(const NFRenderSubmission*,NFSubmissionSchedule*);
__declspec(dllexport) int nf_render_submission_stable(NFStableSceneSubmission**,const NFTimelineSample*,const NFSubmissionSchedule*,NFRenderSubmission**);
__declspec(dllexport) const NFStableSceneSubmission*nf_render_submission_stable_view(const NFRenderSubmission*);
/* Diagnostic sampled scene transfer; does not establish live clock mapping. */
__declspec(dllexport) int nf_render_submission_prepared_motion(NFPreparedMotionSubmission**,const NFTimelineSample*,const NFSubmissionSchedule*,NFRenderSubmission**);
__declspec(dllexport) const NFPreparedMotionSubmission*nf_render_submission_prepared_motion_view(const NFRenderSubmission*);
__declspec(dllexport) unsigned nf_render_submission_kind(const NFRenderSubmission*);
__declspec(dllexport) const NFTimelineSample*nf_render_submission_time(const NFRenderSubmission*);
__declspec(dllexport) NFPresentationSubmission*nf_render_submission_native_view(const NFRenderSubmission*);
__declspec(dllexport) NFHardwareSubmission*nf_render_submission_hardware_view(const NFRenderSubmission*);
__declspec(dllexport) void nf_render_submission_destroy(NFRenderSubmission*);

/* Live publication requires source-derived motion timing, in addition to ownership validation. */
__declspec(dllexport) int nf_render_submission_prepared_motion_live(NFPreparedMotionSubmission**source,const NFTimelineSample*time,const NFSubmissionSchedule*schedule,NFRenderSubmission**out);
#endif
