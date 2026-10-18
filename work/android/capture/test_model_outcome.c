#include <assert.h>
#include <stdio.h>
#include "model_outcome.h"
int main(void){
 static NFModelOutcomeHistory h;uint32_t a[5]={3,0x030000c0,0x02004458,0x08331914,0},b[5];
 assert(nf_model_outcome_query(&h,2,7,100,104,a)==NF_MODEL_OUTCOME_UNKNOWN);
 nf_model_outcome_record(&h,2,7,100,102,a,0);
 assert(nf_model_outcome_query(&h,2,7,100,104,a)==NF_MODEL_OUTCOME_NO_DRAW);
 assert(nf_model_outcome_query(&h,3,7,100,104,a)==NF_MODEL_OUTCOME_UNKNOWN);
 assert(nf_model_outcome_query(&h,2,8,100,104,a)==NF_MODEL_OUTCOME_UNKNOWN);
 assert(nf_model_outcome_query(&h,2,7,101,104,a)==NF_MODEL_OUTCOME_UNKNOWN);
 assert(nf_model_outcome_query(&h,2,7,100,101,a)==NF_MODEL_OUTCOME_UNKNOWN);
 assert(nf_model_outcome_query(&h,2,7,104,100,a)==NF_MODEL_OUTCOME_UNKNOWN);
 for(unsigned i=0;i<5;i++){memcpy(b,a,20);b[i]^=1;assert(nf_model_outcome_query(&h,2,7,100,104,b)==NF_MODEL_OUTCOME_UNKNOWN);}
 nf_model_outcome_record(&h,2,7,100,103,a,1);
 assert(nf_model_outcome_query(&h,2,7,100,104,a)==NF_MODEL_OUTCOME_CONFLICT);
 nf_model_outcome_record(&h,2,23,200,201,a,1);
 assert(nf_model_outcome_query(&h,2,7,100,104,a)==NF_MODEL_OUTCOME_UNKNOWN);
 assert(nf_model_outcome_query(&h,2,23,200,204,a)==NF_MODEL_OUTCOME_DRAW);
 nf_model_outcome_record(&h,3,23,200,201,a,0);
 assert(nf_model_outcome_query(&h,2,23,200,204,a)==NF_MODEL_OUTCOME_UNKNOWN);
 assert(nf_model_outcome_query(&h,3,23,200,204,a)==NF_MODEL_OUTCOME_NO_DRAW);
 nf_model_outcome_record(&h,3,23,200,202,a,2);
 assert(nf_model_outcome_query(&h,3,23,200,204,a)==NF_MODEL_OUTCOME_CONFLICT);
 nf_model_outcome_reset(&h);
 for(unsigned i=0;i<64;i++)nf_model_outcome_record(&h,4,9,300,301,a,0);
 assert(nf_model_outcome_query(&h,4,9,300,304,a)==NF_MODEL_OUTCOME_NO_DRAW);
 nf_model_outcome_record(&h,4,9,300,301,a,0);
 assert(nf_model_outcome_query(&h,4,9,300,304,a)==NF_MODEL_OUTCOME_CONFLICT);
 nf_model_outcome_reset(&h);nf_model_outcome_record(&h,5,2,50,49,a,0);
 assert(nf_model_outcome_query(&h,5,2,50,54,a)==NF_MODEL_OUTCOME_CONFLICT);
 nf_model_outcome_reset(&h);assert(nf_model_outcome_query(&h,5,2,50,54,a)==NF_MODEL_OUTCOME_UNKNOWN);
 puts("PASS_MODEL_OUTCOME_OWNERSHIP_CONFLICT_EVICTION_OVERFLOW_RESET");return 0;
}
