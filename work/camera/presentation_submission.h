#ifndef NF_PRESENTATION_SUBMISSION_H
#define NF_PRESENTATION_SUBMISSION_H
#include "scene_packet.h"
#include "layer_snapshot.h"
#include "rigid_motion.h"
typedef struct NFPresentationSubmission NFPresentationSubmission;
typedef struct {uint64_t origin_ns,lag_ns;uint32_t source_base;double delay_refreshes;} NFSubmissionSchedule;
/* Sole producer only, once before publication. Published schedule is immutable. */
__declspec(dllexport) int nf_submission_schedule_set(NFPresentationSubmission*,const NFSubmissionSchedule*);
__declspec(dllexport) int nf_submission_schedule_get(const NFPresentationSubmission*,NFSubmissionSchedule*);
typedef int(*NFSubmissionRead)(void*,uint64_t,uint32_t,unsigned,NFHudLayerRow*);
/* Emulation-owner only construction. Copies all bytes before publication.
   On failure output is untouched. Published data is immutable; its sole owner
   must keep it alive until every render/read completes. No shared bridge views. */
__declspec(dllexport) int nf_submission_create(const void*,size_t,const NFTimelineSample*,uint32_t,uint32_t,const NFRigidPose*,const uint16_t[160],NFSubmissionRead,void*,NFPresentationSubmission**);
/* Takes exclusive packet ownership only after complete validation/HUD capture.
   Failure leaves packet and output untouched. Release executes at retirement;
   source allocator/module must remain alive until every submission is retired. */
__declspec(dllexport) int nf_submission_take(void**,size_t,const NFTimelineSample*,uint32_t,uint32_t,const NFRigidPose*,const uint16_t[160],NFSubmissionRead,void*,void(*)(void*),NFPresentationSubmission**);
__declspec(dllexport) void nf_submission_destroy(NFPresentationSubmission*);
__declspec(dllexport) unsigned nf_submission_last_error(void);
/* Sole producer, once before publication. Exact original command order;
   copies all camera poses and validates count against packet NFO1 commands. */
__declspec(dllexport) int nf_submission_command_cameras_set(NFPresentationSubmission*,const NFRigidPose*,unsigned);
/* Producer has matched endpoint commands by owned source identity/order.
   Samples both camera arrays at this submission alpha, validates all before publication. */
__declspec(dllexport) int nf_submission_command_camera_pair_set(NFPresentationSubmission*,const NFRigidPose*,const NFRigidPose*,unsigned);
/* Immutable borrowed metadata, atomic outputs on absence. */
__declspec(dllexport) int nf_submission_command_cameras(const NFPresentationSubmission*,const NFRigidPose**,unsigned*);
/* Diagnostic differences: packet1, HUD2, timeline4, cameras8, source16, zero32, schedule64, command cameras128, text256. */
__declspec(dllexport) unsigned nf_submission_difference(const NFPresentationSubmission*,const NFPresentationSubmission*);
/* Diagnostic independent clone and poison after the sole owner retires it. */
__declspec(dllexport) NFPresentationSubmission*nf_submission_clone(const NFPresentationSubmission*);
__declspec(dllexport) void nf_submission_poison_retired(NFPresentationSubmission*);
__declspec(dllexport) int nf_submission_packet(const NFPresentationSubmission*,const void**,size_t*);
__declspec(dllexport) int nf_submission_row(const NFPresentationSubmission*,uint64_t,uint32_t,unsigned,NFHudLayerRow*);
/* Complete owned BG palettes; no bridge calls. Atomic on identity mismatch. */
__declspec(dllexport) int nf_submission_bg_palettes(const NFPresentationSubmission*,uint64_t,uint32_t,uint16_t[160][256]);
__declspec(dllexport) const NFTimelineSample*nf_submission_time(const NFPresentationSubmission*);
__declspec(dllexport) const NFRigidPose*nf_submission_cameras(const NFPresentationSubmission*);
__declspec(dllexport) const uint16_t*nf_submission_zero_colors(const NFPresentationSubmission*);
__declspec(dllexport) int nf_submission_sources(const NFPresentationSubmission*,uint32_t out[2]);
typedef int(*NFSubmissionTextRead)(void*,uint64_t,uint32_t,unsigned,uint8_t[240],uint8_t[240]);
/* Sole producer once before publication; captures complete owned text rows atomically. */
__declspec(dllexport) int nf_submission_text_capture(NFPresentationSubmission*,NFSubmissionTextRead,void*);
__declspec(dllexport) int nf_submission_text_row(const NFPresentationSubmission*,uint64_t,uint32_t,unsigned,uint8_t[240],uint8_t[240]);
#endif
