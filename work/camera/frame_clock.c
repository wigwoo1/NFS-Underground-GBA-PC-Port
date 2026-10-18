#include "frame_clock.h"
#include <math.h>
#include <string.h>
#define NS 1000000000ull
#define LIMIT (7ull*24*60*60*NS)
static uint64_t ceil_ratio(uint64_t value,uint64_t denominator){return value/denominator+(value%denominator!=0);}
static uint64_t simulation_deadline(uint64_t frame){
 uint64_t cycles=frame*280896;return cycles/16777216*NS+ceil_ratio(cycles%16777216*NS,16777216);
}
static uint64_t display_deadline(uint64_t index){return index/60*NS+ceil_ratio(index%60*NS,60);}
int nf_frame_clock_prepare(const NFFrameClock*c,uint64_t now,uint64_t lead,NFPreparationPlan*out){
 if(!c||!out||!c->active||now<c->last||now-c->origin>LIMIT||lead>15000000ull||c->next_display>7ull*24*60*60*60)return 0;
 uint64_t deadline=c->origin+display_deadline(c->next_display);
 uint64_t wake=deadline>=lead?deadline-lead:0;
 NFPreparationPlan plan={0};plan.display_index=c->next_display;plan.deadline_ns=deadline;
 plan.eligible=now<deadline&&deadline-now<=lead;
 plan.next_wake_ns=wake>now?wake:now;
 plan.source_target=c->base+c->next_display*(16777216.0/(280896.0*60.0))-c->delay;
 *out=plan;return 1;
}
int nf_frame_clock_start(NFFrameClock*c,uint64_t now,uint32_t base,double delay){
 if(!c||now>UINT64_MAX-LIMIT-NS||!isfinite(delay)||delay<0)return 0;
 NFFrameClock fresh={now,now,0,0,base,1,delay};*c=fresh;return 1;
}
int nf_frame_clock_poll(NFFrameClock*c,uint64_t now,NFFramePlan*out){
 if(!c||!out||!c->active||now<c->last||now-c->origin>LIMIT)return 0;
 uint64_t elapsed=now-c->origin,seconds=elapsed/NS,remainder=elapsed%NS;
 uint64_t due=(seconds*16777216+remainder*16777216/NS)/280896;
 if(due<c->simulated)return 0;
 NFFramePlan p={0};uint64_t backlog=due-c->simulated;p.simulation_steps=backlog>4?4:(uint32_t)backlog;
 NFFrameClock next=*c;next.last=now;next.simulated+=p.simulation_steps;
 uint64_t latest=seconds*60+remainder*60/NS;
 if(next.simulated==due&&latest>=next.next_display){
  p.present=1;p.display_index=latest;p.skipped_displays=latest-next.next_display;
  p.deadline_ns=next.origin+display_deadline(latest);
  p.source_target=next.base+latest*(16777216.0/(280896.0*60.0))-next.delay;
  next.next_display=latest+1;
 }
 uint64_t sim=next.origin+simulation_deadline(next.simulated+1),display=next.origin+display_deadline(next.next_display);
 p.next_wake_ns=sim<display?sim:display;if(p.next_wake_ns<now)p.next_wake_ns=now;
 *c=next;*out=p;return 1;
}
