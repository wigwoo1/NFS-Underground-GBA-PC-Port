#include "presentation_timeline.h"
#include <math.h>
#include <string.h>
void nf_timeline_clear(NFTimeline*t){if(t)memset(t,0,sizeof(*t));}
int nf_timeline_push(NFTimeline*t,uint64_t epoch,uint64_t id,double time){
 if(!t||!isfinite(time)||t->count>NF_TIMELINE_CAPACITY)return 0;
 if(t->count){
  if(epoch<t->epoch)return 0;
  if(epoch==t->epoch&&time<=t->entries[t->count-1].time)return 0;
  if(epoch>t->epoch)t->count=0;
 }
 t->epoch=epoch;
 if(t->count==NF_TIMELINE_CAPACITY){memmove(t->entries,t->entries+1,(NF_TIMELINE_CAPACITY-1)*sizeof(*t->entries));t->count--;}
 t->entries[t->count++]=(NFTimelineEntry){time,id};return 1;
}
int nf_timeline_sample(const NFTimeline*t,double now,double delay,NFTimelineSample*out){
 if(!t||!out||!t->count||t->count>NF_TIMELINE_CAPACITY||!isfinite(now)||!isfinite(delay)||delay<0)return NF_TIME_EMPTY;
 double target=now-delay;if(!isfinite(target))return NF_TIME_EMPTY;
 NFTimelineSample result={t->epoch,t->entries[0].id,t->entries[0].id,0,target};int status=NF_TIME_READY;
 if(target<t->entries[0].time)status=NF_TIME_BEFORE;
 else{
  unsigned i=0;while(i+1<t->count&&t->entries[i+1].time<=target)i++;
  result.older=result.newer=t->entries[i].id;
  if(i+1<t->count){result.newer=t->entries[i+1].id;result.alpha=(target-t->entries[i].time)/(t->entries[i+1].time-t->entries[i].time);}
  else if(target>t->entries[i].time)status=NF_TIME_AFTER;
 }
 *out=result;return status;
}
