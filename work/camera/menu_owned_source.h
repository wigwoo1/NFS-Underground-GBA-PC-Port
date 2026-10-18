/* Exact epoch/refresh adapter for compact immutable menu submissions. */
#include "hardware_submission.h"
typedef struct {const NFHardwareSubmission*submission;uint64_t epoch;uint32_t refresh;} NFMenuOwnedSource;
static int menu_owned_source(NFMenuOwnedSource*out,const NFHardwareSubmission*submission){
 NFTimelineSample time;NFSubmissionSchedule schedule;if(!out||!nf_hardware_submission_metadata(submission,&time,&schedule))return 0;
 out->submission=submission;out->epoch=time.epoch;out->refresh=(uint32_t)floor(time.target);return 1;
}
static int menu_owned_row(void*source,unsigned y,uint8_t out[100480]){
 NFMenuOwnedSource*s=source;NFHardwareLayerRow row;if(!out||!s||!nf_hardware_submission_row(s->submission,s->epoch,s->refresh,y,&row))return 0;memcpy(out,&row,sizeof(row));return 1;
}
