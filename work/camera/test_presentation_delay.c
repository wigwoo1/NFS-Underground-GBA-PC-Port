#include "frame_clock.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
int main(void){NFFrameClock a,b;assert(nf_frame_clock_start(&a,0,100,5));assert(nf_frame_clock_start(&b,0,100,7));unsigned displays=0;for(uint64_t t=0;t<30000000000ull;t+=1000000){NFFramePlan x,y;assert(nf_frame_clock_poll(&a,t,&x)&&nf_frame_clock_poll(&b,t,&y));assert(x.simulation_steps==y.simulation_steps&&x.present==y.present&&x.skipped_displays==y.skipped_displays&&x.next_wake_ns==y.next_wake_ns);if(x.present){assert(x.display_index==y.display_index&&x.deadline_ns==y.deadline_ns&&fabs(x.source_target-y.source_target-2)<1e-9);displays++;}}assert(a.simulated==b.simulated);printf("PASS: delay changes target only; %u displays, %llu simulation refreshes\n",displays,(unsigned long long)a.simulated);return 0;}
