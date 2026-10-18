/* Host compatibility adapters; all capture and endpoint behavior is shared. */
NF_TEXT_HOST_EXPORT int nf_owned_model_outcome_enable(int enabled){return nf_live_model_outcomes_enable(enabled);}
NF_TEXT_HOST_EXPORT int nf_owned_model_outcome_should_skip(uint64_t epoch,uint32_t serial,uint32_t begin,uint32_t end,const uint32_t identity[5]){return nf_live_completed_model_outcome_for(epoch,serial,begin,end,identity)==NF_MODEL_OUTCOME_NO_DRAW;}
NF_TEXT_HOST_EXPORT void nf_owned_model_outcome_stats(uint32_t serial,uint32_t out[4]){nf_live_model_outcome_stats(serial,out);}
