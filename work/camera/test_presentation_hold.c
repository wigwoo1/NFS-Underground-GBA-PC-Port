#include <assert.h>
#include <stdio.h>
#include "presentation_hold.h"
int main(void){
 NFPresentationHold h={0};
 assert(!nf_presentation_hold(&h,1,10,0,NF_TIME_AFTER));
 assert(!nf_presentation_hold(&h,1,10,1,NF_TIME_READY));
 assert(nf_presentation_hold(&h,1,11,0,NF_TIME_AFTER));
 assert(nf_presentation_hold(&h,1,12,0,NF_TIME_AFTER));
 assert(!nf_presentation_hold(&h,1,12.01,0,NF_TIME_AFTER));
 assert(!nf_presentation_hold(&h,1,11,0,NF_TIME_AFTER));
 for(int status=0;status<=2;status++){
  nf_presentation_hold(&h,1,10,1,NF_TIME_READY);
  assert(!nf_presentation_hold(&h,1,11,0,status));
  assert(!nf_presentation_hold(&h,1,11,0,NF_TIME_AFTER));
 }
 nf_presentation_hold(&h,1,10,1,NF_TIME_READY);
 assert(!nf_presentation_hold(&h,2,11,0,NF_TIME_AFTER));
 nf_presentation_hold(&h,2,10,1,NF_TIME_READY);
 assert(!nf_presentation_hold(&h,2,9,0,NF_TIME_AFTER));
 nf_presentation_hold(&h,2,10,1,NF_TIME_READY);
 assert(!nf_presentation_hold(&h,2,NAN,0,NF_TIME_AFTER));
 nf_presentation_hold(&h,2,20,1,NF_TIME_READY);
 assert(nf_presentation_hold(&h,2,21,0,NF_TIME_AFTER));
 puts("PASS bounded hold, expiry, no timer extension, epoch/cut/invalid-time clearing, recovery");
 return 0;
}
