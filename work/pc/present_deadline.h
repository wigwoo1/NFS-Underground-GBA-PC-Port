#ifndef NF_PC_PRESENT_DEADLINE_H
#define NF_PC_PRESENT_DEADLINE_H
#include <stdint.h>
/* Render-only phase clock. Scene wakeups do not move its deadline. Missed
   slots are skipped rather than replayed; no game logic uses this clock. */
typedef struct { double next; } NFPresentDeadline;
static inline int nf_present_due(const NFPresentDeadline*c,double t){return t>=c->next;}
static inline void nf_present_completed(NFPresentDeadline*c,double t){
 const double period=1.0/60.0;c->next+=period;
 if(c->next<=t){uint64_t skipped=(uint64_t)((t-c->next)/period)+1;c->next+=skipped*period;}
}
static inline unsigned nf_present_wait(const NFPresentDeadline*c,double t){
 double ms=(c->next-t)*1000.0;if(ms<=0)return 0;
 if(ms>=17.0)return 17;
 unsigned n=(unsigned)ms;return n+(ms>n);
}
#endif
