#include "hardware_submission.h"
#include <stdlib.h>
#include <math.h>
struct NFHardwareSubmission {NFTimelineSample time;NFSubmissionSchedule schedule;NFLayerSnapshot*layers;uint32_t refresh;};
int nf_hardware_submission_create(const NFLayerSnapshot*source,const NFTimelineSample*time,const NFSubmissionSchedule*schedule,NFHardwareSubmission**out){
 uint32_t refresh;
 if(!source||!time||!schedule||!out||!time->epoch||!isfinite(time->target)||time->target<0||time->target>UINT32_MAX||!isfinite(time->alpha)||time->alpha<0||time->alpha>1||!isfinite(schedule->delay_refreshes)||schedule->delay_refreshes<0||schedule->lag_ns>1000000000ull||schedule->origin_ns>UINT64_MAX-schedule->lag_ns||!nf_layer_snapshot_refresh(source,&refresh)||refresh!=(uint32_t)floor(time->target))return 0;
 NFHardwareSubmission*s=malloc(sizeof(*s));if(!s)return 0;s->layers=nf_layer_snapshot_clone(source);if(!s->layers){free(s);return 0;}s->time=*time;s->schedule=*schedule;s->refresh=refresh;*out=s;return 1;
}
void nf_hardware_submission_destroy(NFHardwareSubmission*s){if(s){nf_layer_snapshot_destroy(s->layers);free(s);}}
int nf_hardware_submission_row(const NFHardwareSubmission*s,uint64_t epoch,uint32_t refresh,unsigned y,NFHardwareLayerRow*out){return s&&epoch==s->time.epoch&&refresh==s->refresh&&nf_layer_snapshot_read(s->layers,y,out);}
int nf_hardware_submission_metadata(const NFHardwareSubmission*s,NFTimelineSample*time,NFSubmissionSchedule*schedule){if(!s||!time||!schedule)return 0;*time=s->time;*schedule=s->schedule;return 1;}
size_t nf_hardware_submission_bytes(const NFHardwareSubmission*s){return s?sizeof(*s)+nf_layer_snapshot_bytes(s->layers):0;}
