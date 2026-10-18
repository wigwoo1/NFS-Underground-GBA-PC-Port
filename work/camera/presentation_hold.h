#include <stdint.h>
#include <math.h>
#include "presentation_timeline.h"
typedef struct {uint64_t epoch;double target;int valid;} NFPresentationHold;
/* Returns 1 only for a repeated framebuffer, never a newly rendered pose.
   Hold for at most two original refreshes (~33 ms), without moving the clock.
   Any other unavailability, epoch change or reversed time invalidates history. */
static int nf_presentation_hold(NFPresentationHold*h,uint64_t epoch,double target,int rendered,int status){
 if(!isfinite(target)){h->valid=0;return 0;}
 if(rendered){*h=(NFPresentationHold){epoch,target,1};return 0;}
 if(h->valid&&h->epoch==epoch&&status==NF_TIME_AFTER&&target>=h->target&&target-h->target<=2)return 1;
 h->valid=0;return 0;
}
